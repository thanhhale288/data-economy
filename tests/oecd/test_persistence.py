"""Persistence idempotency on in-memory SQLite."""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import OecdIndicator
from crawlers.oecd.sdmx_client import save_oecd_records


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _sample_records():
    return [
        {
            "indicator_code": "MEI_IP",
            "indicator_name": "Industrial Production Index",
            "country": "EA20",
            "isic_code": "C",
            "period": date(2024, 1, 1),
            "value": 100.0,
            "unit": "IX",
            "frequency": "monthly",
            "source": "OECD_PEER",
        },
        {
            "indicator_code": "MEI_IP",
            "indicator_name": "Industrial Production Index",
            "country": "EA20",
            "isic_code": "C",
            "period": date(2024, 2, 1),
            "value": 101.5,
            "unit": "IX",
            "frequency": "monthly",
            "source": "OECD_PEER",
        },
    ]


def test_save_oecd_records_idempotent(db_session):
    first = save_oecd_records(db_session, _sample_records())
    assert first == 2
    assert db_session.query(OecdIndicator).count() == 2

    updated = [
        {**_sample_records()[0], "value": 110.0},
        {**_sample_records()[1], "value": 111.0},
    ]
    second = save_oecd_records(db_session, updated)
    assert second == 2
    assert db_session.query(OecdIndicator).count() == 2

    rows = {
        r.period: r.value
        for r in db_session.query(OecdIndicator).order_by(OecdIndicator.period)
    }
    assert rows[date(2024, 1, 1)] == 110.0
    assert rows[date(2024, 2, 1)] == 111.0
