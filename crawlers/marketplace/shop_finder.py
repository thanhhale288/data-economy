"""Marketplace shop finder and product scraper orchestration.

ShopMatcher lives in ``ml.shop_matcher``. This module only calls it.
Seed and discovered shops both must pass ``is_match`` at threshold 0.65
before linking to a company (CONTEXT). Seed rows still tagged
``match_source=seed_known_url`` for provenance when they pass.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from backend.app.models import Company, DigitalPresence, MarketplaceListing
from crawlers.marketplace.common import (
    FALLBACK_SOURCE,
    MARKETPLACE_CHANNELS,
    SEED_SOURCE,
    annotate_provenance,
    default_rate_limiter,
    load_fallback_listings,
    load_seed_for_ticker,
)
from crawlers.marketplace.shopee import fetch_shopee_listings
from crawlers.marketplace.tiktok import fetch_tiktok_listings
from ml.shop_matcher import DEFAULT_THRESHOLD, ShopMatcher

logger = logging.getLogger(__name__)

# Backwards-compatible re-export
__all__ = [
    "ShopMatcher",
    "DEFAULT_THRESHOLD",
    "find_shops_for_company",
    "scrape_marketplace_products",
    "run_marketplace_crawl",
    "evaluate_discovered_shop",
]

PLATFORM_PATTERNS = {
    "shopee": r"shopee\.vn/[\w.-]+",
    "tiktok": r"tiktok\.com/@[\w.-]+",
    "lazada": r"lazada\.vn/shop/[\w.-]+",
}


def evaluate_discovered_shop(
    company: Company,
    *,
    channel_type: str,
    url: str,
    shop_name: str | None = None,
    has_checkout: bool = False,
    matcher: ShopMatcher | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, Any] | None:
    """Score a non-seed shop; return a link dict only when ``is_match``.

    Below threshold → ``None`` (do not assign company).
    """
    handle = shop_name or url.rstrip("/").split("/")[-1]
    m = matcher or ShopMatcher()
    result = m.match(company.name, handle, threshold=threshold)
    if not result["is_match"]:
        logger.info(
            "Shop below threshold for %s: %s score=%.3f < %.2f — not linking",
            company.stock_code,
            handle,
            result["score"],
            threshold,
        )
        return None
    return {
        "channel_type": channel_type,
        "url": url,
        "has_checkout": has_checkout,
        "match_confidence": round(float(result["score"]), 3),
        "is_match": True,
        "match_source": "fuzzy_threshold",
    }


def find_shops_for_company(company: Company) -> list[dict]:
    """Find marketplace shops from seed known URLs; link only if score ≥ 0.65.

    Seed URLs are candidates with provenance ``seed_known_url``, but still
    must pass ``ShopMatcher.is_match`` (threshold 0.65). Below threshold →
    omitted (do not assign company).
    """
    results: list[dict] = []
    seed = load_seed_for_ticker(company.stock_code)
    if not seed:
        return results

    matcher = ShopMatcher()
    for dp in seed.get("digital_presence", []):
        channel = dp.get("channel_type")
        if channel not in MARKETPLACE_CHANNELS:
            continue
        url = dp["url"]
        shop_name = url.rstrip("/").split("/")[-1]
        result = matcher.match(company.name, shop_name)
        if not result["is_match"]:
            logger.info(
                "Seed shop below threshold for %s: %s score=%.3f < %.2f — not linking",
                company.stock_code,
                shop_name,
                result["score"],
                DEFAULT_THRESHOLD,
            )
            continue
        results.append(
            {
                "channel_type": channel,
                "url": url,
                "has_checkout": bool(dp.get("has_checkout", False)),
                "match_confidence": round(float(result["score"]), 3),
                "fuzzy_score": round(float(result["score"]), 3),
                "is_match": True,
                "match_source": "seed_known_url",
            }
        )
    return results


def _attempt_live_scrape(
    shop: dict[str, Any],
    *,
    client: httpx.Client | None,
    rate_limiter,
) -> list[dict[str, Any]]:
    """Try live scrape for one shop; return listings or empty on block/error."""
    channel = shop["channel_type"]
    url = shop["url"]
    if channel == "shopee":
        result = fetch_shopee_listings(url, client=client, rate_limiter=rate_limiter)
    elif channel == "tiktok":
        result = fetch_tiktok_listings(url, client=client, rate_limiter=rate_limiter)
    else:
        # Lazada optional — not implemented live; empty triggers fallback
        logger.info("Lazada live scrape not implemented; falling back for %s", url)
        return []

    if result.status == "ok" and result.listings:
        return annotate_provenance(result.listings, "live")

    logger.warning(
        "Live marketplace scrape %s for %s (%s): %s — using sourced fallback",
        result.status,
        url,
        channel,
        result.detail,
    )
    return []


def scrape_marketplace_products(
    company: Company,
    *,
    client: httpx.Client | None = None,
    attempt_live: bool = True,
    rate_limiter=None,
) -> list[dict]:
    """Scrape listings for a company: live first (optional), then seed/fallback.

    Never invents sales numbers. On anti-bot → empty live result + log +
    sourced seed/fallback with provenance.
    """
    seed = load_seed_for_ticker(company.stock_code)
    shops = find_shops_for_company(company)

    live_listings: list[dict] = []
    if attempt_live and shops:
        limiter = rate_limiter or default_rate_limiter()
        for shop in shops:
            if not shop.get("is_match"):
                continue
            live_listings.extend(
                _attempt_live_scrape(shop, client=client, rate_limiter=limiter)
            )

    if live_listings:
        return live_listings

    # Prefer seed listings (sourced demo micro-level)
    if seed and seed.get("marketplace_listings"):
        logger.info(
            "Using seed marketplace listings for %s (%s)",
            company.stock_code,
            SEED_SOURCE,
        )
        return annotate_provenance(seed["marketplace_listings"], SEED_SOURCE)

    fallback = load_fallback_listings(company.stock_code)
    if fallback:
        logger.info(
            "Using fallback marketplace listings for %s (%s)",
            company.stock_code,
            FALLBACK_SOURCE,
        )
        return annotate_provenance(fallback, FALLBACK_SOURCE)

    return []


def _upsert_digital_presence(
    db: Session, company: Company, shop: dict[str, Any]
) -> bool:
    """Upsert one marketplace digital_presence row. Returns True if inserted."""
    existing = (
        db.query(DigitalPresence)
        .filter(
            DigitalPresence.company_id == company.id,
            DigitalPresence.url == shop["url"],
        )
        .first()
    )
    if existing:
        existing.channel_type = shop["channel_type"]
        existing.has_checkout = bool(shop.get("has_checkout", False))
        existing.match_confidence = shop.get("match_confidence")
        existing.is_active = True
        existing.crawled_at = datetime.utcnow()
        return False

    db.add(
        DigitalPresence(
            company_id=company.id,
            channel_type=shop["channel_type"],
            url=shop["url"],
            has_checkout=bool(shop.get("has_checkout", False)),
            match_confidence=shop.get("match_confidence"),
            is_active=True,
        )
    )
    return True


def _upsert_listing(
    db: Session, company: Company, product: dict[str, Any]
) -> bool:
    """Upsert by (company_id, platform, product_name). Returns True if inserted."""
    platform = product["platform"]
    name = product["product_name"]
    existing = (
        db.query(MarketplaceListing)
        .filter(
            MarketplaceListing.company_id == company.id,
            MarketplaceListing.platform == platform,
            MarketplaceListing.product_name == name,
        )
        .first()
    )
    price = product.get("price")
    units = product.get("units_sold_est")
    # Never invent revenue — only price × units when both present
    from crawlers.marketplace.common import compute_revenue_est

    revenue = compute_revenue_est(price, units)
    if existing:
        existing.price = price
        existing.units_sold_est = units
        existing.revenue_est = revenue
        existing.rating = product.get("rating")
        if product.get("product_url"):
            existing.product_url = product["product_url"]
        existing.crawled_at = datetime.utcnow()
        return False

    db.add(
        MarketplaceListing(
            company_id=company.id,
            platform=platform,
            product_name=name,
            price=price,
            units_sold_est=units,
            revenue_est=revenue,
            rating=product.get("rating"),
            product_url=product.get("product_url"),
        )
    )
    return True


def run_marketplace_crawl(
    db: Session,
    *,
    attempt_live: bool = True,
    client: httpx.Client | None = None,
) -> int:
    """Crawl marketplace shops + listings for companies in DB. Idempotent upserts.

    Signature kept compatible with pipeline: ``run_marketplace_crawl(db)``.
    """
    matcher = ShopMatcher()
    try:
        matcher.train(db)
    except Exception as exc:  # joblib / disk optional — do not fail crawl
        logger.warning("ShopMatcher.train skipped: %s", exc)

    # Fixed sample allowlist only — ignore accidental extras in DB.
    from crawlers.companies.listed_companies import ALLOWED_TICKER_SET, refresh_allowed_tickers

    refresh_allowed_tickers()

    count = 0
    companies = (
        db.query(Company)
        .filter(Company.stock_code.in_(ALLOWED_TICKER_SET))
        .all()
    )
    rate_limiter = default_rate_limiter() if attempt_live else None

    for company in companies:
        shops = find_shops_for_company(company)
        for shop in shops:
            if not shop.get("is_match"):
                continue
            if _upsert_digital_presence(db, company, shop):
                count += 1

        products = scrape_marketplace_products(
            company,
            client=client,
            attempt_live=attempt_live,
            rate_limiter=rate_limiter,
        )
        for product in products:
            if _upsert_listing(db, company, product):
                count += 1

    db.commit()
    return count
