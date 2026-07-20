"""Fixtures for dashboard service unit tests (in-memory SQLite)."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import (
    Company,
    DigitalMetric,
    GsoMacro,
    ModelRegistry,
    OecdIndicator,
    VsicCode,
)


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'dashboard_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.add_all(
        [
            VsicCode(
                vsic_code="C",
                isic_code="C",
                level=1,
                name_vi="Công nghiệp chế biến, chế tạo",
                name_en="Manufacturing",
            ),
            VsicCode(
                vsic_code="2740",
                isic_code="2740",
                level=4,
                name_vi="Sản xuất thiết bị chiếu sáng điện",
                name_en="Electric lighting",
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
        ]
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def seeded_iip(db_session):
    rows = [
        GsoMacro(
            vsic_code="C",
            indicator_code="IIP_C",
            indicator_name="IIP Section C",
            period=date(2024, m, 1),
            value=100.0 + m,
            source="GSO",
        )
        for m in range(1, 7)
    ]
    db_session.add_all(rows)
    db_session.commit()
    return rows


@pytest.fixture()
def seeded_peer_mei(db_session):
    rows = [
        OecdIndicator(
            indicator_code="MEI_IP",
            indicator_name="MEI Industrial Production",
            country="EA20",
            isic_code="C",
            period=date(2024, m, 1),
            value=90.0 + m,
            source="OECD_PEER",
        )
        for m in range(1, 5)
    ]
    db_session.add_all(rows)
    db_session.commit()
    return rows


@pytest.fixture()
def seeded_companies_va(db_session):
    ral = Company(
        stock_code="RAL",
        name="Rạng Đông",
        vsic_code="2740",
        exchange="HOSE",
        has_ecommerce_site=True,
    )
    hpg = Company(
        stock_code="HPG",
        name="Hòa Phát",
        vsic_code="2410",
        exchange="HOSE",
        has_ecommerce_site=False,
    )
    db_session.add_all([ral, hpg])
    db_session.flush()
    db_session.add_all(
        [
            DigitalMetric(
                company_id=ral.id,
                period=date(2024, 12, 1),
                digital_adoption_score=0.8,
                online_revenue_est=1e9,
                digital_va_contribution=5e8,
            ),
            DigitalMetric(
                company_id=hpg.id,
                period=date(2024, 12, 1),
                digital_adoption_score=0.3,
                online_revenue_est=2e8,
                digital_va_contribution=1e8,
            ),
        ]
    )
    db_session.commit()
    return ral, hpg
