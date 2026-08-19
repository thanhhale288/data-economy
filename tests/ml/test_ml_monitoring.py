"""Task #63 — ML monitoring contract (present vs missing metrics / drift)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.models import ModelPrediction, ModelRegistry
from backend.app.services import ml_monitoring as svc


@pytest.fixture()
def db_session(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from backend.app.database import Base

    engine = create_engine(f"sqlite:///{tmp_path / 'ml_monitoring_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_missing_registry_metrics_are_null_with_warning(db_session, tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    baseline = tmp_path / "no_baseline.json"

    status = svc.get_monitoring_status(
        db_session,
        baseline_path=baseline,
        models_dir=models_dir,
    )

    assert status.counters.models_tracked == 4
    assert status.counters.models_with_metrics == 0
    assert status.counters.models_missing_metrics == 4
    assert status.counters.baseline_available is False
    assert status.counters.models_with_drift == 0
    assert any("drift_unavailable" in w for w in status.warnings)

    names = {snap.model_name for snap in status.models}
    assert names == set(svc.CANONICAL_MODELS)
    assert "lightgbm" in names

    for snap in status.models:
        assert snap.model_name in ("arima", "xgboost", "lightgbm", "lstm")
        assert snap.metrics.get("mae") is None
        assert snap.metrics.get("rmse") is None
        assert snap.metrics.get("mape") is None
        assert snap.drift_flag is None
        assert snap.drift_score is None
        assert snap.warning is not None
        assert "registry_missing" in snap.warning
        assert "no_baseline_artifact" in snap.warning
        assert snap.artifact_present is False


def test_present_metrics_and_baseline_compute_drift(db_session, tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "arima_model.joblib").write_bytes(b"fake")
    (models_dir / "xgboost_model.joblib").write_bytes(b"fake")

    db_session.add_all(
        [
            ModelRegistry(
                model_name="arima",
                model_type="arima",
                version="1",
                metrics={"mae": 1.2, "rmse": 2.0, "mape": 12.0},
                artifact_path=str(models_dir / "arima_model.joblib"),
                is_active=True,
                trained_at=datetime(2024, 6, 1, 12, 0, 0),
            ),
            ModelRegistry(
                model_name="xgboost",
                model_type="xgboost",
                version="1",
                metrics={"mae": 0.8, "rmse": 1.1, "mape": 8.0},
                artifact_path=str(models_dir / "xgboost_model.joblib"),
                is_active=True,
                trained_at=datetime(2024, 6, 2, 12, 0, 0),
            ),
            ModelPrediction(
                model_name="arima",
                target_indicator="IIP_C",
                period=datetime(2024, 1, 1).date(),
                predicted_value=100.0,
                actual_value=101.0,
            ),
            ModelPrediction(
                model_name="arima",
                target_indicator="IIP_C",
                period=datetime(2024, 2, 1).date(),
                predicted_value=102.0,
                actual_value=103.0,
            ),
        ]
    )
    db_session.commit()

    baseline_path = tmp_path / "ml_monitoring_baseline.json"
    baseline_path.write_text(
        json.dumps(
            {
                "mape_drift_threshold": 5.0,
                "models": {
                    "arima": {"mape": 5.0},
                    "xgboost": {"mape": 8.0},
                },
            }
        ),
        encoding="utf-8",
    )

    status = svc.get_monitoring_status(
        db_session,
        baseline_path=baseline_path,
        models_dir=models_dir,
    )

    assert status.counters.baseline_available is True
    assert status.counters.models_with_metrics == 2
    assert status.counters.models_missing_metrics == 2  # lstm + lightgbm still missing
    assert status.counters.artifacts_on_disk >= 2

    by_name = {s.model_name: s for s in status.models}
    arima = by_name["arima"]
    assert arima.metrics["mape"] == 12.0
    assert arima.sample_count == 2
    assert arima.artifact_present is True
    assert arima.drift_score == pytest.approx(7.0)
    assert arima.drift_flag is True
    assert arima.warning is None or "no_baseline" not in (arima.warning or "")

    xgb = by_name["xgboost"]
    assert xgb.drift_score == pytest.approx(0.0)
    assert xgb.drift_flag is False

    lstm = by_name["lstm"]
    assert lstm.metrics["mape"] is None
    assert lstm.drift_flag is None
    assert "metrics_missing" in (lstm.warning or "") or "registry_missing" in (
        lstm.warning or ""
    )

    lgbm = by_name["lightgbm"]
    assert lgbm.metrics.get("mae") is None
    assert lgbm.metrics.get("rmse") is None
    assert lgbm.metrics.get("mape") is None
    assert lgbm.drift_flag is None
    assert lgbm.drift_score is None
    assert "registry_missing" in (lgbm.warning or "")
    assert lgbm.artifact_present is False


def test_no_fake_drift_without_baseline_even_with_metrics(db_session, tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    db_session.add(
        ModelRegistry(
            model_name="arima",
            model_type="arima",
            version="1",
            metrics={"mae": 1.0, "rmse": 1.5, "mape": 9.0},
            is_active=True,
            trained_at=datetime(2024, 6, 1),
        )
    )
    db_session.commit()

    status = svc.get_monitoring_status(
        db_session,
        baseline_path=tmp_path / "missing_baseline.json",
        models_dir=models_dir,
    )
    arima = next(s for s in status.models if s.model_name == "arima")
    assert arima.metrics["mape"] == 9.0
    assert arima.drift_flag is None
    assert arima.drift_score is None
    assert "no_baseline_artifact" in (arima.warning or "")


def test_api_ml_monitoring_endpoint(db_session, monkeypatch):
    from backend.app.database import get_db
    from backend.app.main import app

    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    client = TestClient(app)
    try:
        res = client.get("/api/ml/monitoring")
        assert res.status_code == 200
        body = res.json()
        assert "counters" in body
        assert "models" in body
        assert body["backend"] == "sqlalchemy_registry"
        assert body["great_expectations"] is False
        assert body["counters"]["models_tracked"] >= 4
        # Empty DB → honesty warnings, no invented drift
        assert any(m["drift_flag"] is None for m in body["models"])
    finally:
        app.dependency_overrides.clear()

def test_lightgbm_artifact_candidates_honesty(db_session, tmp_path):
    """Untrained LightGBM stays in the monitor with null metrics; disk files flip artifact_present."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    status = svc.get_monitoring_status(
        db_session,
        baseline_path=tmp_path / "no_baseline.json",
        models_dir=models_dir,
    )
    by_name = {s.model_name: s for s in status.models}
    snap = by_name["lightgbm"]
    assert snap.metrics["mape"] is None
    assert snap.warning is not None
    assert "registry_missing" in snap.warning
    assert snap.artifact_present is False

    (models_dir / "lightgbm_model.joblib").write_bytes(b"fake")
    (models_dir / "lightgbm_importance.json").write_text("{}", encoding="utf-8")
    assert svc.artifact_present("lightgbm", models_dir=models_dir) is True

