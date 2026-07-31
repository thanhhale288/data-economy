"""Task #62 — Forecast narrative cites only forecast + metrics + importance numbers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.services.forecast_narrative import (
    extract_number_tokens,
    generate_forecast_narrative,
    narrative_numbers_are_honest,
)


@pytest.fixture()
def api_db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'forecast_narrative_api_test.db'}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def client(api_db):
    def override_get_db():
        try:
            yield api_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _forecast_payload(**overrides):
    base = {
        "model": "xgboost",
        "horizon": 6,
        "forecasts": [
            {"period": "2025-01-01", "predicted_value": 98.12},
            {"period": "2025-02-01", "predicted_value": 99.05},
            {"period": "2025-03-01", "predicted_value": 100.4},
        ],
    }
    base.update(overrides)
    return base


def _importance_available(*, gain: dict | None = None) -> dict:
    gain = gain or {"iip_roll3m": 12.5, "iip_lag1": 8.0, "indigo": 3.25}
    return {
        "available": True,
        "features": [
            {"feature": k, "gain": v}
            for k, v in sorted(gain.items(), key=lambda kv: kv[1], reverse=True)
        ],
        "gain": gain,
        "message": None,
    }


def test_narrative_only_contains_input_numbers(tmp_path: Path):
    forecast = _forecast_payload()
    metrics = {"mae": 1.25, "rmse": 2.5, "mape": 3.75}
    importance = _importance_available()

    out = generate_forecast_narrative(
        forecast,
        metrics=metrics,
        importance=importance,
        load_importance=False,
        artifact_dir=tmp_path,
    )
    assert out["method"] == "rules"
    assert out["narrative"]
    assert out["importance_available"] is True
    data = {**forecast, "metrics": metrics}
    assert narrative_numbers_are_honest(out["narrative"], data, importance)
    assert "6" in out["narrative"]
    assert "98.12" in out["narrative"]
    assert "1.25" in out["narrative"]
    assert "iip_roll3m" in out["narrative"]
    assert "12.5" in out["narrative"] or "12.50" in out["narrative"]
    tokens = extract_number_tokens(out["narrative"])
    assert "99.99" not in tokens
    assert "50" not in tokens  # no invented median / fake driver share


def test_narrative_missing_importance_does_not_invent_drivers(tmp_path: Path):
    forecast = _forecast_payload(model="xgboost")
    out = generate_forecast_narrative(
        forecast,
        metrics={"mae": 1.0},
        importance=None,
        load_importance=True,
        artifact_dir=tmp_path,
    )
    assert "importance" in out["omitted"]
    assert out["importance_available"] is False
    assert "Thiếu" in out["narrative"] or "không bịa" in out["narrative"].lower()
    assert "iip_roll3m" not in out["narrative"]
    assert "nguyên nhân" in out["narrative"].lower() or "không bịa" in out["narrative"].lower()
    data = {**forecast, "metrics": {"mae": 1.0}}
    assert narrative_numbers_are_honest(out["narrative"], data, {"available": False})


def test_narrative_arima_skips_importance_without_inventing():
    forecast = _forecast_payload(model="arima", horizon=3)
    out = generate_forecast_narrative(
        forecast,
        metrics=None,
        importance=None,
        load_importance=True,
    )
    assert "importance" in out["omitted"]
    assert "arima" in out["narrative"].lower()
    assert "mae" in out["omitted"] or "Thiếu sai số" in out["narrative"]
    assert narrative_numbers_are_honest(
        out["narrative"],
        {**forecast, "metrics": {}},
        {"available": False},
    )
    # Must not invent a fake MAPE like 4.2 when metrics missing.
    assert "4.2" not in out["narrative"]


def test_narrative_lightgbm_uses_importance_when_present(tmp_path: Path):
    gain = {"iip_lag1": 9.5, "mei_ip": 4.0}
    (tmp_path / "lightgbm_importance.json").write_text(
        json.dumps({"gain": gain, "weight": {}, "feature_cols": list(gain.keys())}),
        encoding="utf-8",
    )
    forecast = _forecast_payload(model="lightgbm", horizon=3)
    out = generate_forecast_narrative(
        forecast,
        metrics={"rmse": 2.0},
        load_importance=True,
        artifact_dir=tmp_path,
    )
    assert out["importance_available"] is True
    assert "iip_lag1" in out["narrative"]
    assert "9.5" in out["narrative"]
    assert narrative_numbers_are_honest(
        out["narrative"],
        {**forecast, "metrics": {"rmse": 2.0}},
        {
            "available": True,
            "gain": gain,
            "features": [
                {"feature": "iip_lag1", "gain": 9.5},
                {"feature": "mei_ip", "gain": 4.0},
            ],
        },
    )


def test_narrative_endpoint_openapi_and_honesty(client):
    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    assert "/api/ml/narrative" in openapi.json()["paths"]

    importance = _importance_available()
    payload = {
        **_forecast_payload(),
        "metrics": {"mae": 1.25, "rmse": 2.5, "mape": 3.75},
        "importance": importance,
        "load_importance": False,
    }
    res = client.post("/api/ml/narrative", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["narrative"]
    assert body["method"] == "rules"
    assert body["importance_available"] is True
    data = {
        "model": payload["model"],
        "horizon": payload["horizon"],
        "forecasts": payload["forecasts"],
        "metrics": payload["metrics"],
    }
    assert narrative_numbers_are_honest(body["narrative"], data, importance)
    assert any(c["field"] == "horizon" for c in body["citations"])


def test_llm_missing_key_uses_rules(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("FORECAST_NARRATIVE_LLM_KEY", raising=False)
    out = generate_forecast_narrative(
        _forecast_payload(),
        metrics={"mae": 1.0},
        importance={"available": False, "message": "Thiếu importance"},
        load_importance=False,
    )
    assert out["method"] == "rules"
