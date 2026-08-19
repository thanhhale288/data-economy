"""Task #74 — HTTP API tests for POST /api/ml/categorize."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.services import product_categorizer_service as svc
from ml.product_categorizer import ProductCategorizer

REPO_ROOT = Path(__file__).resolve().parents[2]
LABELS_PATH = REPO_ROOT / "data" / "seeds" / "product_categorizer_labels.json"


@pytest.fixture(scope="module")
def trained_cat(tmp_path_factory) -> ProductCategorizer:
    cat = ProductCategorizer(
        model_path=tmp_path_factory.mktemp("pc") / "product_categorizer.joblib"
    )
    cat.train(labels_path=LABELS_PATH, persist=True)
    return cat


@pytest.fixture()
def api_db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'categorize_api_test.db'}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def client(api_db, trained_cat, monkeypatch):
    monkeypatch.setattr(svc, "get_categorizer", lambda: trained_cat)

    def override_get_db():
        try:
            yield api_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_categorize_happy_path_labeled_product(client):
    res = client.post(
        "/api/ml/categorize",
        json={"product_name": "Bóng LED Rạng Đông 9W"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["product_name"] == "Bóng LED Rạng Đông 9W"
    assert body["vsic_code"] == "2740"
    assert body["reason"] is None
    assert body["confidence"] >= 0.22


def test_categorize_oov_unknown_abstains(client):
    res = client.post(
        "/api/ml/categorize",
        json={"product_name": "Vé máy bay nội địa"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["vsic_code"] is None
    assert body["reason"] is not None


def test_categorize_empty_and_short_abstain(client):
    for name in ("", "ab", "  "):
        res = client.post("/api/ml/categorize", json={"product_name": name})
        assert res.status_code == 200, name
        body = res.json()
        assert body["vsic_code"] is None, name
        assert body["reason"] == "empty_or_short_input", name


def test_categorize_never_invents_vsic_on_junk(client):
    res = client.post(
        "/api/ml/categorize",
        json={"product_name": "xyzqwerty 999 unrelated junk"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["vsic_code"] is None
    assert body["reason"] is not None
