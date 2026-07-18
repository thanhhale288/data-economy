"""Shared fixtures for digital metrics tests."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import (
    Company,
    DigitalPresence,
    FinancialReport,
    MarketplaceListing,
    VsicCode,
)


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'digital_metrics_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    for code, name_vi in [
        ("2740", "Sản xuất thiết bị chiếu sáng điện"),
        ("2410", "Sản xuất sắt, thép"),
        ("1050", "Chế biến sữa"),
    ]:
        session.add(
            VsicCode(
                vsic_code=code,
                isic_code=code,
                level=4,
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
def company_ral(db_session):
    """RAL-like company: website + shopee presence; marketplace + website listings."""
    company = Company(
        stock_code="RAL",
        name="Công ty Cổ phần Bóng đèn Rạng Đông",
        vsic_code="2740",
        exchange="HOSE",
        website_url="https://rangdong.com.vn",
        has_ecommerce_site=True,
    )
    db_session.add(company)
    db_session.flush()

    db_session.add_all(
        [
            DigitalPresence(
                company_id=company.id,
                channel_type="website",
                url="https://rangdong.com.vn",
                is_active=True,
                has_checkout=True,
                match_confidence=1.0,
            ),
            DigitalPresence(
                company_id=company.id,
                channel_type="shopee",
                url="https://shopee.vn/rangdong_official",
                is_active=True,
                has_checkout=True,
                match_confidence=0.95,
            ),
            FinancialReport(
                company_id=company.id,
                period=date(2024, 12, 31),
                report_type="annual",
                revenue=5_200_000_000_000,
                gross_margin=0.38,
                source_url="seed:companies.json",
            ),
            MarketplaceListing(
                company_id=company.id,
                platform="shopee",
                product_name="Bóng LED Rạng Đông 9W",
                price=45_000,
                units_sold_est=12_500,
                revenue_est=562_500_000,
            ),
            MarketplaceListing(
                company_id=company.id,
                platform="shopee",
                product_name="Đèn LED Panel 600x600",
                price=285_000,
                units_sold_est=3_200,
                revenue_est=912_000_000,
            ),
            # Seed website row — must NOT count toward online_revenue_est
            MarketplaceListing(
                company_id=company.id,
                platform="website",
                product_name="Bộ đèn downlight âm trần",
                price=195_000,
                units_sold_est=1_800,
                revenue_est=351_000_000,
            ),
        ]
    )
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture()
def company_hpg(db_session):
    """HPG-like: website only, no marketplace listings."""
    company = Company(
        stock_code="HPG",
        name="Tập đoàn Hòa Phát",
        vsic_code="2410",
        exchange="HOSE",
        website_url="https://hoaphat.com.vn",
        has_ecommerce_site=False,
    )
    db_session.add(company)
    db_session.flush()
    db_session.add_all(
        [
            DigitalPresence(
                company_id=company.id,
                channel_type="website",
                url="https://hoaphat.com.vn",
                is_active=True,
                has_checkout=False,
                match_confidence=1.0,
            ),
            FinancialReport(
                company_id=company.id,
                period=date(2024, 12, 31),
                report_type="annual",
                revenue=162_000_000_000_000,
                gross_margin=0.23,
                source_url="seed:companies.json",
            ),
        ]
    )
    db_session.commit()
    db_session.refresh(company)
    return company
