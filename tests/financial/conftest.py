"""Shared helpers for financial (BCTC) crawler tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import Company, VsicCode

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def load_fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'financial_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(
        VsicCode(
            vsic_code="2740",
            isic_code="2740",
            level=4,
            name_vi="Sản xuất thiết bị chiếu sáng điện",
            name_en="Manufacture of electric lighting equipment",
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def sample_company(db_session):
    company = Company(
        stock_code="RAL",
        name="Công ty Cổ phần Bóng đèn Rạng Đông",
        vsic_code="2740",
        exchange="HOSE",
        website_url="https://rangdong.com.vn",
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company
