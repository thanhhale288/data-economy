"""Persistence / upsert tests for digital_presence + marketplace_listings."""

from __future__ import annotations

from backend.app.models import DigitalPresence, MarketplaceListing
from crawlers.marketplace.shop_finder import run_marketplace_crawl


def test_run_marketplace_crawl_persists_shops_and_listings(
    db_session, ten_companies, monkeypatch
):
    # Force seed/fallback path — no live network in unit tests
    monkeypatch.setattr(
        "crawlers.marketplace.shop_finder._attempt_live_scrape",
        lambda *a, **k: [],
    )

    count = run_marketplace_crawl(db_session, attempt_live=False)
    assert count > 0

    presence = (
        db_session.query(DigitalPresence)
        .filter(DigitalPresence.channel_type.in_(["shopee", "tiktok", "lazada"]))
        .all()
    )
    assert len(presence) >= 1
    urls = {p.url for p in presence}
    assert "https://shopee.vn/rangdong_official" in urls
    assert "https://shopee.vn/vinamilk_official" in urls

    listings = db_session.query(MarketplaceListing).all()
    assert len(listings) >= 1
    led = next(l for l in listings if l.product_name == "Bóng LED Rạng Đông 9W")
    assert led.price == 45000
    assert led.units_sold_est == 12500
    assert led.revenue_est == 562500000


def test_run_marketplace_crawl_is_idempotent(db_session, ten_companies, monkeypatch):
    monkeypatch.setattr(
        "crawlers.marketplace.shop_finder._attempt_live_scrape",
        lambda *a, **k: [],
    )

    run_marketplace_crawl(db_session, attempt_live=False)
    n_presence = (
        db_session.query(DigitalPresence)
        .filter(DigitalPresence.channel_type.in_(["shopee", "tiktok", "lazada"]))
        .count()
    )
    n_listings = db_session.query(MarketplaceListing).count()

    run_marketplace_crawl(db_session, attempt_live=False)
    assert (
        db_session.query(DigitalPresence)
        .filter(DigitalPresence.channel_type.in_(["shopee", "tiktok", "lazada"]))
        .count()
        == n_presence
    )
    assert db_session.query(MarketplaceListing).count() == n_listings


def test_upsert_listing_updates_price_without_duplicating(
    db_session, sample_company, monkeypatch
):
    monkeypatch.setattr(
        "crawlers.marketplace.shop_finder._attempt_live_scrape",
        lambda *a, **k: [],
    )
    # Only RAL in DB — crawl still only touches existing companies
    run_marketplace_crawl(db_session, attempt_live=False)

    row = (
        db_session.query(MarketplaceListing)
        .filter(
            MarketplaceListing.company_id == sample_company.id,
            MarketplaceListing.product_name == "Bóng LED Rạng Đông 9W",
        )
        .one()
    )
    assert row.price == 45000
    listing_id = row.id

    # Second run updates same row
    run_marketplace_crawl(db_session, attempt_live=False)
    row2 = (
        db_session.query(MarketplaceListing)
        .filter(
            MarketplaceListing.company_id == sample_company.id,
            MarketplaceListing.product_name == "Bóng LED Rạng Đông 9W",
        )
        .one()
    )
    assert row2.id == listing_id
