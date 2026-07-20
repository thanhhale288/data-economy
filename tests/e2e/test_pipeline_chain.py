"""Task #17 — offline E2E: crawl → clean → features → ML → API (honest skips)."""

from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import pytest

from backend.app.models import GsoMacro, PipelineJob
from tests.e2e.conftest import inject_offline_crawl


@pytest.fixture()
def chained_db(e2e_db, artifact_dirs):
    """Run the offline pipeline chain once; yield db + artifact paths."""
    pytest.importorskip("statsmodels")

    counts = inject_offline_crawl(e2e_db)
    iip_n = (
        e2e_db.query(GsoMacro)
        .filter(GsoMacro.indicator_code == "IIP_C", GsoMacro.vsic_code == "C")
        .count()
    )
    if iip_n < 25:
        pytest.skip(f"need >=25 IIP_C months for ARIMA, got {iip_n}")

    from ml.models.trainer import train_arima
    from pipeline.cleaning.digital_metrics import compute_all_digital_metrics
    from pipeline.cleaning.run_cleaning import (
        CLEANED_MACRO_NAME,
        CLEANING_REPORT_NAME,
        run_data_cleaning,
    )
    from pipeline.features.engineering import run_feature_engineering

    n_metrics = compute_all_digital_metrics(e2e_db)
    n_clean, clean_detail = run_data_cleaning(e2e_db)
    assert n_clean >= 1, clean_detail

    processed = artifact_dirs["processed"]
    report_path = processed / CLEANING_REPORT_NAME
    assert report_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert "artifacts" in report
    assert "series_missing" in report
    # Peer MEI_IP@EA20 not injected offline — must be listed missing (no invent).
    assert "mei_ip" in report["series_missing"]
    assert (processed / CLEANED_MACRO_NAME).is_file()

    n_feat = run_feature_engineering(e2e_db)
    assert n_feat > 0
    features_path = processed / "features.parquet"
    assert features_path.is_file()
    feats = pd.read_parquet(features_path)
    assert "iip" in feats.columns
    assert "mei_bci" not in feats.columns

    # ARIMA only in E2E: proves ML stage without XGBoost OpenMP segfault risk on macOS.
    arima_metrics = train_arima(e2e_db)
    assert arima_metrics.get("mae") is not None or arima_metrics.get("status") == "ok"
    assert (artifact_dirs["models"] / "arima_model.joblib").is_file()

    e2e_db.add(
        PipelineJob(
            job_name="data_cleaning",
            status="success",
            records_processed=n_clean,
            error_message=clean_detail[:500],
            started_at=datetime(2024, 6, 1, 2, 0, 0),
            finished_at=datetime(2024, 6, 1, 2, 5, 0),
            created_at=datetime(2024, 6, 1, 2, 0, 0),
        )
    )
    e2e_db.commit()

    return {
        "db": e2e_db,
        "dirs": artifact_dirs,
        "crawl_counts": counts,
        "n_metrics": n_metrics,
        "n_clean": n_clean,
        "n_feat": n_feat,
        "arima_metrics": arima_metrics,
        "report": report,
    }


def test_e2e_chain_artifacts_and_no_invented_mei_bci(chained_db):
    """Prove clean → features artifacts exist and forbidden MEI_BCI stays absent."""
    dirs = chained_db["dirs"]
    assert (dirs["processed"] / "cleaning_report.json").is_file()
    assert (dirs["processed"] / "features.parquet").is_file()
    assert (dirs["models"] / "arima_model.joblib").is_file()
    assert "mei_bci" not in chained_db["report"].get("macro", {})
    assert chained_db["n_feat"] > 0
    assert chained_db["n_metrics"] >= 1


def test_e2e_api_dashboard_company_pipeline_ml(chained_db, api_client):
    """Happy-path HTTP smoke after chain: Dashboard / Company / Pipeline / ML."""
    # Pipeline monitor
    q = api_client.get("/api/pipeline/quality")
    assert q.status_code == 200
    qbody = q.json()
    assert qbody["available"] is True
    assert qbody["summary"] is not None

    status = api_client.get("/api/pipeline/status")
    assert status.status_code == 200
    assert status.json()["staging_postgres"] is False

    jobs = api_client.get("/api/pipeline/jobs")
    assert jobs.status_code == 200
    assert any(j["job_name"] == "data_cleaning" for j in jobs.json())

    # Dashboard
    summary = api_client.get("/api/dashboard/summary")
    assert summary.status_code == 200
    sbody = summary.json()
    assert sbody["total_companies"] == 10
    assert sbody["iip_latest"] is not None

    iip = api_client.get("/api/dashboard/iip")
    assert iip.status_code == 200
    assert len(iip.json()) >= 25

    oecd = api_client.get("/api/dashboard/oecd-vs-gso")
    assert oecd.status_code == 200
    obody = oecd.json()
    # Offline inject has no MEI_IP@EA20 peer — must be explicit missing, not invented.
    assert obody["oecd_status"] == "missing"
    assert obody["oecd"] == []

    # Company (BMP ticker lock)
    companies = api_client.get("/api/companies/")
    assert companies.status_code == 200
    codes = {c["stock_code"] for c in companies.json()}
    assert "BMP" in codes
    assert "BWE" not in codes

    bmp = api_client.get("/api/companies/BMP")
    assert bmp.status_code == 200
    assert bmp.json()["stock_code"] == "BMP"

    ral = api_client.get("/api/companies/RAL")
    assert ral.status_code == 200
    assert "Rạng Đông" in ral.json()["name"] or ral.json().get("case_study") is not None

    # ML registry + forecast from real artifact
    models = api_client.get("/api/ml/models")
    assert models.status_code == 200
    names = {m["model_name"] for m in models.json()}
    assert "arima" in names

    forecast = api_client.post(
        "/api/ml/forecast",
        json={"model_name": "arima", "horizon_months": 6},
    )
    assert forecast.status_code == 200, forecast.text
    fbody = forecast.json()
    assert fbody["model"] == "arima"
    assert fbody["horizon"] == 6
    assert len(fbody["forecasts"]) == 6
    assert all("predicted_value" in row for row in fbody["forecasts"])

    # No XGB train in this smoke → importance must stay unavailable (không bịa).
    imp = api_client.get("/api/ml/feature-importance?model_name=xgboost")
    assert imp.status_code == 200
    ibody = imp.json()
    assert ibody["available"] is False
    assert ibody["features"] == []
    assert "không bịa" in (ibody.get("message") or "").lower()


def test_e2e_forecast_missing_artifact_is_404(e2e_db, artifact_dirs, api_client):
    """Missing model file → 404, not a invented growth series."""
    # Seed minimal IIP so the handler reaches the artifact check.
    from datetime import date

    e2e_db.add(
        GsoMacro(
            vsic_code="C",
            indicator_code="IIP_C",
            indicator_name="IIP Section C",
            period=date(2024, 1, 1),
            value=100.0,
            unit="index",
            source="test",
        )
    )
    e2e_db.commit()

    res = api_client.post(
        "/api/ml/forecast",
        json={"model_name": "arima", "horizon_months": 3},
    )
    assert res.status_code == 404
    assert "artifact" in res.json()["detail"].lower() or "arima" in res.json()["detail"].lower()


def test_e2e_pipeline_quality_missing_is_honest(api_client, artifact_dirs):
    """No cleaning_report → available=false (không bịa quality)."""
    res = api_client.get("/api/pipeline/quality")
    assert res.status_code == 200
    body = res.json()
    assert body["available"] is False
    assert body["summary"] is None
    assert "không bịa" in (body.get("message") or "").lower()
