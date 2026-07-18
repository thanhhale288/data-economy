"""Unit tests for online revenue, adoption, Digital VA, and persistence."""

from __future__ import annotations

from datetime import date

from backend.app.models import (
    Company,
    DigitalMetric,
    DigitalPresence,
    FinancialReport,
    MarketplaceListing,
)
from pipeline.cleaning.digital_metrics import (
    compute_adoption_score,
    compute_all_digital_metrics,
    compute_channel_diversity,
    compute_digital_va,
    compute_industry_share,
    estimate_online_revenue,
    listing_contribution,
    marketplace_listings_for_revenue,
)


# Fixed RAL marketplace sum: 45000*12500 + 285000*3200 = 562_500_000 + 912_000_000
RAL_MARKETPLACE_ONLINE = 1_474_500_000.0
# Website listing intentionally excluded: 195000*1800 = 351_000_000


def test_listing_contribution_prefers_price_times_units():
    listing = MarketplaceListing(
        company_id=1,
        platform="shopee",
        product_name="x",
        price=100.0,
        units_sold_est=5,
        revenue_est=999.0,  # ignored when price×units present
    )
    assert listing_contribution(listing) == 500.0


def test_listing_contribution_falls_back_to_revenue_est():
    listing = MarketplaceListing(
        company_id=1,
        platform="tiktok",
        product_name="y",
        price=None,
        units_sold_est=None,
        revenue_est=42_000.0,
    )
    assert listing_contribution(listing) == 42_000.0


def test_listing_contribution_none_when_incomplete():
    listing = MarketplaceListing(
        company_id=1,
        platform="shopee",
        product_name="z",
        price=10.0,
        units_sold_est=None,
        revenue_est=None,
    )
    assert listing_contribution(listing) is None


def test_marketplace_listings_exclude_website_platform(company_ral):
    plats = {ml.platform for ml in marketplace_listings_for_revenue(company_ral)}
    assert plats == {"shopee"}
    assert all(ml.platform != "website" for ml in marketplace_listings_for_revenue(company_ral))


def test_online_revenue_sums_marketplace_not_website(company_ral):
    rev = estimate_online_revenue(company_ral)
    assert rev == RAL_MARKETPLACE_ONLINE
    # If website were included: 1_474_500_000 + 351_000_000
    assert rev != RAL_MARKETPLACE_ONLINE + 351_000_000


def test_online_revenue_uses_revenue_est_when_price_units_missing(db_session, company_ral):
    db_session.add(
        MarketplaceListing(
            company_id=company_ral.id,
            platform="tiktok",
            product_name="Promo pack",
            price=None,
            units_sold_est=None,
            revenue_est=100_000.0,
        )
    )
    db_session.commit()
    db_session.refresh(company_ral)
    assert estimate_online_revenue(company_ral) == RAL_MARKETPLACE_ONLINE + 100_000.0


def test_online_revenue_zero_when_no_listings_no_silent_ratio(company_hpg):
    """HPG has BCTC revenue but no marketplace listings — must not invent 0.15×revenue."""
    rev = estimate_online_revenue(company_hpg)
    assert rev == 0.0
    # Old silent invent would be ~162e12 * 0.35 * 0.15 >> 0
    assert rev < 1.0


def test_online_revenue_industry_ratio_only_when_explicit(company_hpg):
    """Interpolation allowed only with an explicitly passed (sourced) ratio."""
    rev = estimate_online_revenue(company_hpg, industry_ratio=0.02)
    assert rev == 162_000_000_000_000 * 0.02


def test_adoption_and_diversity_from_active_presence(company_ral, company_hpg):
    # RAL: website 0.35 + shopee 0.30 + ecommerce bonus 0.1 = 0.75
    assert compute_adoption_score(company_ral) == 0.75
    assert compute_channel_diversity(company_ral) == round(2 / 4.0, 3)

    # HPG: website only 0.35
    assert compute_adoption_score(company_hpg) == 0.35
    assert compute_channel_diversity(company_hpg) == round(1 / 4.0, 3)


def test_inactive_presence_excluded_from_adoption(db_session, company_hpg):
    db_session.add(
        DigitalPresence(
            company_id=company_hpg.id,
            channel_type="shopee",
            url="https://shopee.vn/fake",
            is_active=False,
            has_checkout=True,
            match_confidence=0.9,
        )
    )
    db_session.commit()
    db_session.refresh(company_hpg)
    assert compute_adoption_score(company_hpg) == 0.35


def test_digital_va_matches_context_formula():
    """Digital_VA = (OR × GM) + (Cost_savings × AS) - DI with fixed proxies."""
    online = 1_000_000.0
    margin = 0.40
    adoption = 0.5
    expected = (
        online * margin
        + (online * 0.05) * adoption
        - online * 0.02
    )
    assert compute_digital_va(online, margin, adoption) == expected


def test_digital_va_default_margin_when_none():
    online = 100.0
    adoption = 1.0
    # default GM 0.25
    expected = online * 0.25 + (online * 0.05) * adoption - online * 0.02
    assert compute_digital_va(online, None, adoption) == expected


def test_industry_share_by_vsic_prefix():
    all_va = [("2740", 100.0), ("2710", 300.0), ("1050", 50.0)]
    # prefix 27 → 100+300=400 → 100/400*100 = 25
    assert compute_industry_share(100.0, "2740", all_va) == 25.0
    assert compute_industry_share(50.0, "1050", all_va) == 100.0


def test_compute_all_persists_and_is_idempotent(db_session, company_ral, company_hpg):
    n1 = compute_all_digital_metrics(db_session)
    assert n1 == 2
    rows = db_session.query(DigitalMetric).all()
    assert len(rows) == 2

    ral = next(r for r in rows if r.company_id == company_ral.id)
    assert ral.online_revenue_est == RAL_MARKETPLACE_ONLINE
    assert ral.digital_adoption_score == 0.75
    assert ral.channel_diversity == 0.5
    expected_va = compute_digital_va(RAL_MARKETPLACE_ONLINE, 0.38, 0.75)
    assert ral.digital_va_contribution == round(expected_va, 2)
    assert ral.online_revenue_ratio == round(
        RAL_MARKETPLACE_ONLINE / 5_200_000_000_000, 4
    )

    hpg = next(r for r in rows if r.company_id == company_hpg.id)
    assert hpg.online_revenue_est == 0.0
    assert hpg.digital_va_contribution == 0.0
    assert hpg.digital_adoption_score == 0.35

    n2 = compute_all_digital_metrics(db_session)
    assert n2 == 0  # updates existing, no new inserts
    assert db_session.query(DigitalMetric).count() == 2


def test_peer_industry_share_persisted(db_session):
    """Two firms same VSIC-2 prefix → industry_share splits Digital VA."""
    from backend.app.models import VsicCode

    if not db_session.query(VsicCode).filter_by(vsic_code="2710").first():
        db_session.add(
            VsicCode(
                vsic_code="2710",
                isic_code="2710",
                level=4,
                name_vi="Sản xuất động cơ điện",
                name_en="Motors",
            )
        )
        db_session.commit()

    a = Company(stock_code="A1", name="A", vsic_code="2740", exchange="HOSE")
    b = Company(stock_code="B1", name="B", vsic_code="2710", exchange="HOSE")
    db_session.add_all([a, b])
    db_session.flush()
    for co, rev in [(a, 1_000_000.0), (b, 3_000_000.0)]:
        db_session.add(
            MarketplaceListing(
                company_id=co.id,
                platform="shopee",
                product_name="p",
                price=rev,
                units_sold_est=1,
                revenue_est=rev,
            )
        )
        db_session.add(
            DigitalPresence(
                company_id=co.id,
                channel_type="shopee",
                url=f"https://shopee.vn/{co.stock_code}",
                is_active=True,
            )
        )
        db_session.add(
            FinancialReport(
                company_id=co.id,
                period=date(2024, 12, 31),
                report_type="annual",
                revenue=10_000_000.0,
                gross_margin=0.25,
                source_url="test",
            )
        )
    db_session.commit()

    compute_all_digital_metrics(db_session)
    metrics = {m.company_id: m for m in db_session.query(DigitalMetric).all()}
    share_a = metrics[a.id].industry_share_pct or 0
    share_b = metrics[b.id].industry_share_pct or 0
    assert abs(share_a + share_b - 100.0) < 0.1
