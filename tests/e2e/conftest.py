"""Shared fixtures for Task #17 E2E chain (SQLite + tmp artifact dirs, no network)."""

from __future__ import annotations

import json
import os
from pathlib import Path

# Mitigate OpenMP segfaults with XGBoost on some macOS / CI runners (see tests/ml/conftest).
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.models import Company
from backend.app.seed import load_companies, load_vsic_mappings

REPO_ROOT = Path(__file__).resolve().parents[2]
GSO_FIXTURE_XML = REPO_ROOT / "tests" / "gso" / "fixtures" / "iip_sample.xml"
OECD_INDIGO_FIXTURE = REPO_ROOT / "tests" / "oecd" / "fixtures" / "sdmx_indigo_vnm.json"
SEED_TICKERS = frozenset(
    {"RAL", "HPG", "VNM", "FPT", "GVR", "DGC", "MSN", "PNJ", "REE", "BMP"}
)


@pytest.fixture()
def e2e_db(tmp_path):
    """Isolated SQLite with schema; VSIC + 10 seed companies (incl. BMP, not BWE)."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'e2e.db'}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    load_vsic_mappings(session)
    load_companies(session)
    codes = {c.stock_code for c in session.query(Company).all()}
    assert "BMP" in codes
    assert "BWE" not in codes
    assert SEED_TICKERS.issubset(codes)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def artifact_dirs(tmp_path, monkeypatch):
    """Redirect processed + models dirs away from shared data/."""
    processed = tmp_path / "processed"
    models = tmp_path / "models"
    processed.mkdir()
    models.mkdir()

    import pipeline.cleaning.run_cleaning as run_cleaning_mod
    import pipeline.features.engineering as eng
    from backend.app.services import ml_lab_service, pipeline_service
    from ml.models import arima_model, lstm_model, trainer, xgboost_model

    monkeypatch.setattr(run_cleaning_mod, "PROCESSED_DIR", processed)
    monkeypatch.setattr(pipeline_service, "PROCESSED_DIR", processed)

    monkeypatch.setattr(eng, "_PROCESSED_DIR", processed)
    monkeypatch.setattr(eng, "_CLEANED_MACRO_PATH", processed / "cleaned_macro.parquet")
    monkeypatch.setattr(eng, "_FEATURES_PATH", processed / "features.parquet")
    monkeypatch.setattr(eng, "_MANIFEST_PATH", processed / "features_manifest.json")

    monkeypatch.setattr(trainer, "MODELS_DIR", models)
    monkeypatch.setattr(trainer, "ARIMA_ARTIFACT", models / "arima_model.joblib")
    monkeypatch.setattr(trainer, "XGB_ARTIFACT", models / "xgboost_model.joblib")
    monkeypatch.setattr(trainer, "LSTM_ARTIFACT", models / "lstm_model.pt")

    monkeypatch.setattr(arima_model, "MODELS_DIR", models)
    monkeypatch.setattr(arima_model, "DEFAULT_ARTIFACT_PATH", models / "arima_model.joblib")
    monkeypatch.setattr(xgboost_model, "MODELS_DIR", models)
    monkeypatch.setattr(lstm_model, "MODELS_DIR", models)
    monkeypatch.setattr(ml_lab_service, "MODELS_DIR", models)

    return {"processed": processed, "models": models}


@pytest.fixture()
def api_client(e2e_db):
    """FastAPI TestClient bound to the E2E SQLite session."""
    from fastapi.testclient import TestClient

    from backend.app.database import get_db
    from backend.app.main import app

    def override_get_db():
        try:
            yield e2e_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def inject_offline_crawl(db) -> dict[str, int]:
    """Crawl stage without live network: GSO fixture + fallback CSV + OECD INDIGO fixture.

    Values come only from committed fixtures / sourced fallback — never invented.
    """
    from crawlers.gso.iip_crawler import (
        load_fallback_records,
        parse_sdmx_series,
        save_gso_records,
    )
    from crawlers.oecd.sdmx_client import (
        expand_annual_to_monthly_step,
        parse_sdmx_json,
        save_oecd_records,
    )

    if not GSO_FIXTURE_XML.is_file():
        pytest.skip(f"GSO fixture missing: {GSO_FIXTURE_XML}")
    if not OECD_INDIGO_FIXTURE.is_file():
        pytest.skip(f"OECD fixture missing: {OECD_INDIGO_FIXTURE}")

    parsed = parse_sdmx_series(GSO_FIXTURE_XML.read_text(encoding="utf-8"))
    n_fixture = save_gso_records(db, parsed.records)

    try:
        fallback = load_fallback_records()
    except FileNotFoundError as exc:
        pytest.skip(f"GSO fallback CSV missing (needed for ML length): {exc}")
    n_fallback = save_gso_records(db, fallback)

    indigo_payload = json.loads(OECD_INDIGO_FIXTURE.read_text(encoding="utf-8"))
    indigo_annual = parse_sdmx_json(
        indigo_payload,
        indicator_code="INDIGO",
        indicator_name="Digital Trade Openness Index",
        country_filter="VNM",
    )
    indigo_monthly = expand_annual_to_monthly_step(indigo_annual)
    n_oecd = save_oecd_records(db, indigo_monthly)

    return {
        "gso_fixture_rows": n_fixture,
        "gso_fallback_upserts": n_fallback,
        "oecd_indigo_rows": n_oecd,
        "iip_total": n_fixture + n_fallback,  # approximate; upserts may update
    }
