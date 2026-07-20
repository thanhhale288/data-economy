"""Company detail Module 2 — timeline, quality score, RAL case study."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from backend.app.models import (
    Company,
    DigitalMetric,
    DigitalPresence,
    FinancialReport,
    MarketplaceListing,
)
from backend.app.services import company_service


@pytest.fixture()
def company_ral(db_session):
    ral = Company(
        stock_code="RAL",
        name="Công ty Cổ phần Bóng đèn Rạng Đông",
        vsic_code="2740",
        exchange="HOSE",
        website_url="https://rangdong.com.vn",
        has_ecommerce_site=True,
        description="Sản xuất thiết bị chiếu sáng",
        digital_channels={"website": True, "shopee": True, "tiktok": False},
    )
    db_session.add(ral)
    db_session.flush()

    t0 = datetime(2024, 6, 1, 10, 0, 0)
    t1 = datetime(2024, 6, 2, 11, 0, 0)
    db_session.add_all(
        [
            DigitalPresence(
                company_id=ral.id,
                channel_type="website",
                url="https://rangdong.com.vn",
                is_active=True,
                has_checkout=True,
                match_confidence=1.0,
                crawled_at=t0,
            ),
            DigitalPresence(
                company_id=ral.id,
                channel_type="shopee",
                url="https://shopee.vn/rangdong_official",
                is_active=True,
                has_checkout=True,
                match_confidence=0.95,
                crawled_at=t1,
            ),
            MarketplaceListing(
                company_id=ral.id,
                platform="shopee",
                product_name="Bóng LED Rạng Đông 9W",
                price=45000,
                units_sold_est=12500,
                revenue_est=562_500_000,
                rating=4.8,
                product_url="https://shopee.vn/product/1",
                crawled_at=t1,
            ),
            MarketplaceListing(
                company_id=ral.id,
                platform="website",
                product_name="Đèn downlight",
                price=195000,
                units_sold_est=1800,
                revenue_est=351_000_000,
                crawled_at=t0,
            ),
            FinancialReport(
                company_id=ral.id,
                period=date(2024, 12, 31),
                report_type="annual",
                revenue=5_200_000_000_000,
            ),
            DigitalMetric(
                company_id=ral.id,
                period=date(2024, 12, 1),
                online_revenue_est=1_474_500_000,
                digital_va_contribution=500_000_000,
                industry_share_pct=42.5,
                digital_adoption_score=0.8,
            ),
        ]
    )
    db_session.commit()
    return ral


@pytest.fixture()
def company_bmp(db_session):
    bmp = Company(
        stock_code="BMP",
        name="Nhựa Bình Minh",
        vsic_code="2220",
        exchange="HOSE",
        website_url="https://binhminhplastic.com.vn",
        has_ecommerce_site=False,
        digital_channels={"website": True, "shopee": False, "tiktok": False},
    )
    db_session.add(bmp)
    db_session.flush()
    db_session.add(
        DigitalPresence(
            company_id=bmp.id,
            channel_type="website",
            url="https://binhminhplastic.com.vn",
            is_active=True,
            has_checkout=False,
            match_confidence=1.0,
            crawled_at=datetime(2024, 5, 1),
        )
    )
    db_session.commit()
    return bmp


def test_list_includes_bmp_not_bwe(db_session, company_ral, company_bmp):
    codes = {c.stock_code for c in company_service.list_companies(db_session)}
    assert "BMP" in codes
    assert "BWE" not in codes
    assert "RAL" in codes


def test_get_company_case_insensitive(db_session, company_ral):
    detail = company_service.get_company(db_session, "ral")
    assert detail is not None
    assert detail.stock_code == "RAL"


def test_get_company_missing(db_session):
    assert company_service.get_company(db_session, "ZZZ") is None


def test_ral_case_study_from_persisted_fields(db_session, company_ral):
    detail = company_service.get_company(db_session, "RAL")
    assert detail.case_study is not None
    assert detail.case_study.stock_code == "RAL"
    assert detail.case_study.vsic_code == "2740"
    assert detail.case_study.website_url == "https://rangdong.com.vn"
    assert detail.case_study.shopee_url == "https://shopee.vn/rangdong_official"
    assert detail.case_study.tiktok_url is None
    assert any("rangdong.com.vn" in h for h in detail.case_study.highlights)
    assert any("Shopee" in h for h in detail.case_study.highlights)
    assert any("2740" in h for h in detail.case_study.highlights)
    # No invented TikTok URL
    assert all("tiktok.com" not in h.lower() for h in detail.case_study.highlights)


def test_bmp_has_no_case_study(db_session, company_bmp):
    detail = company_service.get_company(db_session, "BMP")
    assert detail.case_study is None


def test_crawl_timeline_sorted_and_includes_presence_and_listings(db_session, company_ral):
    detail = company_service.get_company(db_session, "RAL")
    assert len(detail.crawl_timeline) >= 3
    types = {e.event_type for e in detail.crawl_timeline}
    assert "digital_presence" in types
    assert "marketplace_listing" in types
    # Newest first when timestamps present
    stamped = [e for e in detail.crawl_timeline if e.crawled_at]
    assert stamped == sorted(stamped, key=lambda e: e.crawled_at, reverse=True)


def test_marketplace_listing_exposes_crawled_at(db_session, company_ral):
    detail = company_service.get_company(db_session, "RAL")
    assert detail.marketplace_listings
    assert all(ml.crawled_at is not None for ml in detail.marketplace_listings)


def test_data_quality_score_components(db_session, company_ral):
    detail = company_service.get_company(db_session, "RAL")
    q = detail.data_quality
    assert q is not None
    assert q.max_score == 100.0
    assert q.score > 70
    assert q.status == "ok"
    assert "website_presence" in q.components
    assert "marketplace_channel" in q.components
    assert q.components["website_presence"] == 20.0
    assert q.components["marketplace_channel"] == 20.0
    assert q.components["digital_metrics"] == 15.0
    assert any("không phải độ chính xác" in n.lower() or "không phải" in n for n in q.notes)


def test_sparse_quality_without_marketplace(db_session, company_bmp):
    detail = company_service.get_company(db_session, "BMP")
    q = detail.data_quality
    assert q.components["marketplace_channel"] == 0.0
    assert q.components["listing_completeness"] == 0.0
    assert q.score < 70
    assert q.status in {"partial", "sparse"}


def test_online_metric_passthrough_not_invented(db_session, company_ral):
    detail = company_service.get_company(db_session, "RAL")
    metrics = sorted(detail.digital_metrics, key=lambda m: m.period, reverse=True)
    assert metrics[0].online_revenue_est == 1_474_500_000
