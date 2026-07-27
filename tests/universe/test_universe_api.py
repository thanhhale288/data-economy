"""Task #50 — UniverseCoverageNote API (empty stub is valid)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import Company, VsicCode
from backend.app.schemas.universe import DIGITAL_VA_COVERAGE_CLAIM
from backend.app.services.universe_service import get_coverage_note, load_universe_rows


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'universe_api_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(
        VsicCode(
            vsic_code="2740",
            isic_code="2740",
            level=4,
            name_vi="Sản xuất thiết bị chiếu sáng điện",
            name_en="Electric lighting",
            parent_code="27",
        )
    )
    session.commit()
    yield session
    session.close()


def _client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_coverage_endpoint_empty_db_and_empty_universe(db_session):
    """Stub universe [] + no companies still returns a valid honesty note."""
    assert load_universe_rows() == []
    client = _client(db_session)
    try:
        res = client.get("/api/universe/coverage")
        assert res.status_code == 200
        body = res.json()
        assert body["claim"] == DIGITAL_VA_COVERAGE_CLAIM
        assert body["claim"] == "prototype_listed_sample"
        assert body["coverage_label"] == "prototype_estimate"
        assert body["deep_sample_size"] == 0
        assert body["universe_row_count"] == 0
        assert "Section C" in body["detail"] or "national" in body["detail"].lower()
        # Must not imply national Section C coverage from company count.
        assert "national Section C" in body["detail"] or "not national" in body["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_coverage_endpoint_deep_sample_count_is_not_section_c(db_session):
    """companies count feeds deep_sample_size only — universe stays 0."""
    db_session.add(
        Company(
            stock_code="TST",
            name="Test Mfg",
            vsic_code="2740",
            exchange="HOSE",
        )
    )
    db_session.commit()
    note = get_coverage_note(db_session)
    assert note.deep_sample_size == 1
    assert note.universe_row_count == 0
    assert note.claim == "prototype_listed_sample"

    client = _client(db_session)
    try:
        res = client.get("/api/universe/coverage")
        assert res.status_code == 200
        body = res.json()
        assert body["deep_sample_size"] == 1
        assert body["universe_row_count"] == 0
        assert body["claim"] == "prototype_listed_sample"
    finally:
        app.dependency_overrides.clear()
