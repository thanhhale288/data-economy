"""Fixtures for Task #11 feature-engineering tests (no network)."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import (
    Company,
    DigitalMetric,
    FinancialReport,
    GsoMacro,
    OecdIndicator,
    VsicCode,
)


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'features_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    for code, name_vi, level in (
        ("C", "Công nghiệp chế biến, chế tạo", 1),
        ("2740", "Sản xuất thiết bị chiếu sáng điện", 4),
        ("2410", "Sản xuất sắt, thép", 4),
    ):
        session.add(
            VsicCode(
                vsic_code=code,
                isic_code=code,
                level=level,
                name_vi=name_vi,
                name_en=name_vi,
            )
        )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def two_companies(db_session):
    firms = [
        Company(
            stock_code="RAL",
            name="Rang Dong",
            vsic_code="2740",
            exchange="HOSE",
        ),
        Company(
            stock_code="HPG",
            name="Hoa Phat",
            vsic_code="2410",
            exchange="HOSE",
        ),
    ]
    db_session.add_all(firms)
    db_session.commit()
    return firms


@pytest.fixture()
def macro_months():
    return pd.date_range("2024-01-01", periods=6, freq="MS")


@pytest.fixture()
def seeded_macro_db(db_session, macro_months):
    for i, period in enumerate(macro_months):
        db_session.add(
            GsoMacro(
                vsic_code="C",
                indicator_code="IIP_C",
                indicator_name="IIP Section C",
                period=period.date(),
                value=100.0 + i,
                unit="index",
                source="GSO",
            )
        )
        db_session.add(
            OecdIndicator(
                indicator_code="INDIGO",
                indicator_name="INDIGO",
                country="VNM",
                period=period.date(),
                value=90.0 + i,
                unit="index",
                source="OECD",
            )
        )
    db_session.commit()
    return db_session


@pytest.fixture()
def digital_rows(two_companies):
    a, b = two_companies
    return pd.DataFrame(
        [
            {
                "company_id": a.id,
                "period": date(2024, 6, 1),
                "digital_adoption_score": 0.4,
                "channel_diversity": 0.5,
                "online_revenue_ratio": 0.10,
            },
            {
                "company_id": b.id,
                "period": date(2024, 6, 1),
                "digital_adoption_score": 0.6,
                "channel_diversity": 0.7,
                "online_revenue_ratio": 0.20,
            },
        ]
    )


@pytest.fixture()
def seeded_digital(db_session, two_companies):
    a, b = two_companies
    db_session.add_all(
        [
            DigitalMetric(
                company_id=a.id,
                period=date(2024, 6, 1),
                digital_adoption_score=0.4,
                channel_diversity=0.5,
                online_revenue_ratio=0.10,
            ),
            DigitalMetric(
                company_id=b.id,
                period=date(2024, 6, 1),
                digital_adoption_score=0.6,
                channel_diversity=0.7,
                online_revenue_ratio=0.20,
            ),
        ]
    )
    db_session.commit()
    return db_session


@pytest.fixture()
def seeded_financial(db_session, two_companies):
    a, b = two_companies
    db_session.add_all(
        [
            FinancialReport(
                company_id=a.id,
                period=date(2024, 3, 31),
                report_type="quarterly",
                net_profit=100.0,
                total_assets=1000.0,
                total_equity=500.0,
                current_assets=200.0,
                current_liabilities=100.0,
            ),
            FinancialReport(
                company_id=b.id,
                period=date(2024, 3, 31),
                report_type="quarterly",
                net_profit=50.0,
                total_assets=500.0,
                total_equity=250.0,
                current_assets=150.0,
                current_liabilities=50.0,
            ),
        ]
    )
    db_session.commit()
    return db_session
