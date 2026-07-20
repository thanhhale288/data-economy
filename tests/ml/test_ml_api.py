"""Task #16 — HTTP API tests for ML Lab feature-importance endpoint."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.services import ml_lab_service as svc


@pytest.fixture()
def api_db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'ml_lab_api_test.db'}",
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


def test_feature_importance_endpoint_missing(client, tmp_path, monkeypatch):
    monkeypatch.setattr(svc, "MODELS_DIR", tmp_path)
    res = client.get("/api/ml/feature-importance?model_name=xgboost")
    assert res.status_code == 200
    body = res.json()
    assert body["available"] is False
    assert body["features"] == []
    assert "không bịa" in body["message"].lower()


def test_feature_importance_endpoint_reads_json(client, tmp_path, monkeypatch):
    monkeypatch.setattr(svc, "MODELS_DIR", tmp_path)
    (tmp_path / "xgboost_importance.json").write_text(
        json.dumps(
            {
                "gain": {"iip_lag1": 9.0, "indigo": 1.5},
                "weight": {"iip_lag1": 3, "indigo": 1},
                "feature_cols": ["iip_lag1", "indigo"],
            }
        ),
        encoding="utf-8",
    )
    res = client.get("/api/ml/feature-importance")
    assert res.status_code == 200
    body = res.json()
    assert body["available"] is True
    assert body["features"][0]["feature"] == "iip_lag1"
    assert body["gain"]["iip_lag1"] == 9.0


def test_feature_importance_endpoint_arima_banner(client, tmp_path, monkeypatch):
    monkeypatch.setattr(svc, "MODELS_DIR", tmp_path)
    res = client.get("/api/ml/feature-importance?model_name=arima")
    assert res.status_code == 200
    body = res.json()
    assert body["available"] is False
    assert "arima" in body["message"].lower()
