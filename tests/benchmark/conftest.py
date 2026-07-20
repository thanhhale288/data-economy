"""Fixtures for Task #18 benchmark service / API tests."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import Company, FinancialReport, VsicCode


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'benchmark_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add_all(
        [
            VsicCode(
                vsic_code="2740",
                isic_code="2740",
                level=4,
                name_vi="Sản xuất thiết bị chiếu sáng điện",
                name_en="Electric lighting",
                parent_code="27",
            ),
            VsicCode(
                vsic_code="2710",
                isic_code="2710",
                level=4,
                name_vi="Sản xuất động cơ điện",
                name_en="Electric motors",
                parent_code="27",
            ),
            VsicCode(
                vsic_code="2410",
                isic_code="2410",
                level=4,
                name_vi="Sản xuất sắt, thép, gang",
                name_en="Iron and steel",
                parent_code="24",
            ),
            VsicCode(
                vsic_code="3290",
                isic_code="3290",
                level=4,
                name_vi="Sản xuất khác",
                name_en="Other manufacturing",
                parent_code="32",
            ),
        ]
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _add_company_with_report(session, *, stock_code, vsic_code, name, **financial):
    company = Company(
        stock_code=stock_code,
        name=name,
        vsic_code=vsic_code,
        exchange="HOSE",
    )
    session.add(company)
    session.flush()
    session.add(
        FinancialReport(
            company_id=company.id,
            period=financial.pop("period", date(2025, 12, 31)),
            report_type="annual",
            **financial,
        )
    )
    session.commit()
    return company


@pytest.fixture()
def peers_division_27(db_session):
    """RAL + REE share VSIC division 27 — enough for real percentiles."""
    _add_company_with_report(
        db_session,
        stock_code="RAL",
        vsic_code="2740",
        name="Rạng Đông",
        revenue=5_200_000_000_000,
        profit_before_tax=420_000_000_000,
        total_assets=6_800_000_000_000,
        total_equity=3_200_000_000_000,
        current_assets=3_100_000_000_000,
        current_liabilities=2_100_000_000_000,
        employees=3200,
        cost_of_goods=3_200_000_000_000,
        rental_cost=85_000_000_000,
        remuneration=680_000_000_000,
    )
    _add_company_with_report(
        db_session,
        stock_code="REE",
        vsic_code="2710",
        name="REE",
        revenue=8_000_000_000_000,
        profit_before_tax=900_000_000_000,
        total_assets=10_000_000_000_000,
        total_equity=5_000_000_000_000,
        current_assets=4_000_000_000_000,
        current_liabilities=2_000_000_000_000,
        employees=3200,
    )
    return db_session


@pytest.fixture()
def singleton_peer(db_session):
    """Single firm in division 24 — small sample warning path."""
    _add_company_with_report(
        db_session,
        stock_code="HPG",
        vsic_code="2410",
        name="Hòa Phát",
        revenue=120_000_000_000_000,
        profit_before_tax=15_000_000_000_000,
        total_assets=200_000_000_000_000,
        total_equity=100_000_000_000_000,
        current_assets=80_000_000_000_000,
        current_liabilities=40_000_000_000_000,
        employees=32000,
    )
    return db_session
