"""Marketplace shop finder and product scraper orchestration.

ShopMatcher lives in ``ml.shop_matcher``. This module only calls it.
Seed and discovered shops both must pass ``is_match`` at threshold 0.65
before linking to a company (CONTEXT). Seed rows still tagged
``match_source=seed_known_url`` for provenance when they pass.

Task #36 — marketplace discovery search is **OFF by default**. Enable only via
``MARKETPLACE_DISCOVERY_ENABLED=1`` plus a QA allowlist entry and threshold 0.65.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
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
    normalize_listing_source,
    provenance_counts,
)
from crawlers.marketplace.live_cache import load_cached_listings
from crawlers.marketplace.shopee import fetch_shopee_listings
from crawlers.marketplace.tiktok import fetch_tiktok_listings
from ml.shop_matcher import DEFAULT_THRESHOLD, ShopMatcher

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
DISCOVERY_ALLOWLIST_PATH = _REPO_ROOT / "data" / "mappings" / "discovery_allowlist.json"
DISCOVERY_ENABLED_ENV = "MARKETPLACE_DISCOVERY_ENABLED"
DISCOVERY_THRESHOLD_ENV = "MARKETPLACE_DISCOVERY_THRESHOLD"

# Backwards-compatible re-export
__all__ = [
    "ShopMatcher",
    "DEFAULT_THRESHOLD",
    "DISCOVERY_ALLOWLIST_PATH",
    "DISCOVERY_ENABLED_ENV",
    "DISCOVERY_THRESHOLD_ENV",
    "is_marketplace_discovery_enabled",
    "marketplace_discovery_threshold",
    "load_discovery_allowlist",
    "find_shops_for_company",
    "discover_shops_for_company",
    "scrape_marketplace_products",
    "run_marketplace_crawl",
    "evaluate_discovered_shop",
]

PLATFORM_PATTERNS = {
    "shopee": r"shopee\.vn/[\w.-]+",
    "tiktok": r"tiktok\.com/@[\w.-]+",
    "lazada": r"lazada\.vn/shop/[\w.-]+",
}


def is_marketplace_discovery_enabled() -> bool:
    """Discovery search is OFF unless env is an explicit truthy value."""
    raw = (os.environ.get(DISCOVERY_ENABLED_ENV) or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def marketplace_discovery_threshold() -> float:
    """Match threshold for discovery links (default CONTEXT 0.65)."""
    raw = (os.environ.get(DISCOVERY_THRESHOLD_ENV) or "").strip()
    if not raw:
        return float(DEFAULT_THRESHOLD)
    try:
        value = float(raw)
    except ValueError:
        logger.warning(
            "Invalid %s=%r — using DEFAULT_THRESHOLD %.2f",
            DISCOVERY_THRESHOLD_ENV,
            raw,
            DEFAULT_THRESHOLD,
        )
        return float(DEFAULT_THRESHOLD)
    if value < 0.0 or value > 1.0:
        logger.warning(
            "Out-of-range %s=%s — using DEFAULT_THRESHOLD %.2f",
            DISCOVERY_THRESHOLD_ENV,
            value,
            DEFAULT_THRESHOLD,
        )
        return float(DEFAULT_THRESHOLD)
    return value


def load_discovery_allowlist(
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Load QA discovery allowlist entries (empty list if missing/invalid)."""
    allowlist_path = path or DISCOVERY_ALLOWLIST_PATH
    if not allowlist_path.exists():
        return []
    try:
        with open(allowlist_path, encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Discovery allowlist unreadable at %s: %s", allowlist_path, exc)
        return []
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return []
    out: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        ticker = str(entry.get("ticker") or "").strip().upper()
        url = str(entry.get("url") or "").strip()
        channel = str(entry.get("channel_type") or entry.get("channel") or "").strip().lower()
        if not ticker or not url:
            continue
        if channel and channel not in MARKETPLACE_CHANNELS:
            continue
        if not channel:
            # Infer channel from URL when omitted
            lowered = url.lower()
            if "shopee" in lowered:
                channel = "shopee"
            elif "tiktok" in lowered:
                channel = "tiktok"
            elif "lazada" in lowered:
                channel = "lazada"
            else:
                continue
        out.append(
            {
                "ticker": ticker,
                "channel_type": channel,
                "url": url,
                "shop_name": entry.get("shop_name"),
                "has_checkout": bool(entry.get("has_checkout", False)),
            }
        )
    return out


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

    Below threshold → ``None`` (do not assign company). Product-level discovery
    must also pass ``discover_shops_for_company`` (flag + QA allowlist).
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


def discover_shops_for_company(
    company: Company,
    *,
    enabled: bool | None = None,
    allowlist: list[dict[str, Any]] | None = None,
    matcher: ShopMatcher | None = None,
    threshold: float | None = None,
) -> list[dict[str, Any]]:
    """Controlled discovery: OFF by default; ON only with flag + QA allowlist + 0.65.

    Does not invent shop URLs — candidates come only from the QA allowlist file
    (or an explicitly passed allowlist for tests). Returns ``[]`` when disabled
    or when the ticker has no allowlist entries.
    """
    if enabled is None:
        enabled = is_marketplace_discovery_enabled()
    if not enabled:
        return []

    cut = marketplace_discovery_threshold() if threshold is None else float(threshold)
    entries = allowlist if allowlist is not None else load_discovery_allowlist()
    ticker = (company.stock_code or "").strip().upper()
    candidates = [e for e in entries if str(e.get("ticker", "")).upper() == ticker]
    if not candidates:
        return []

    m = matcher or ShopMatcher()
    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for cand in candidates:
        url = str(cand["url"])
        if url in seen_urls:
            continue
        linked = evaluate_discovered_shop(
            company,
            channel_type=str(cand["channel_type"]),
            url=url,
            shop_name=cand.get("shop_name"),
            has_checkout=bool(cand.get("has_checkout", False)),
            matcher=m,
            threshold=cut,
        )
        if linked is None:
            continue
        linked["match_source"] = "qa_discovery"
        results.append(linked)
        seen_urls.add(url)
    return results


def find_shops_for_company(company: Company) -> list[dict]:
    """Find marketplace shops from seed known URLs; link only if score ≥ 0.65.

    Seed URLs are candidates with provenance ``seed_known_url``, but still
    must pass ``ShopMatcher.is_match`` (threshold 0.65). Below threshold →
    omitted (do not assign company). Does not run marketplace discovery search.
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
    stock_code: str,
    client: httpx.Client | None,
    rate_limiter,
    prefer_cache: bool = False,
) -> list[dict[str, Any]]:
    """Try live scrape for one shop; on fail use allowlisted cache; else empty.

    Order (Task #35): optional prefer_cache → HTTP live → allowlisted cache.
    Never invents listings. Empty return lets caller use seed/fallback.
    """
    channel = shop["channel_type"]
    url = shop["url"]

    if prefer_cache:
        cached = load_cached_listings(stock_code, channel)
        if cached:
            return cached

    if channel == "shopee":
        result = fetch_shopee_listings(url, client=client, rate_limiter=rate_limiter)
    elif channel == "tiktok":
        result = fetch_tiktok_listings(url, client=client, rate_limiter=rate_limiter)
    else:
        # Lazada optional — not implemented live; try cache then empty
        logger.info("Lazada live scrape not implemented for %s", url)
        cached = load_cached_listings(stock_code, channel)
        return cached if cached else []

    if result.status == "ok" and result.listings:
        return annotate_provenance(result.listings, "live")

    cached = load_cached_listings(stock_code, channel)
    if cached:
        logger.info(
            "Live scrape %s for %s (%s): %s — using allowlisted live cache",
            result.status,
            url,
            channel,
            result.detail,
        )
        return cached

    logger.warning(
        "Live marketplace scrape %s for %s (%s): %s — no cache; using sourced fallback",
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
    prefer_cache: bool = False,
) -> list[dict]:
    """Scrape listings for a company: live (+cache), then seed/fallback.

    Never invents sales numbers. On anti-bot → allowlisted live cache if present,
    else sourced seed/fallback with provenance.
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
                _attempt_live_scrape(
                    shop,
                    stock_code=company.stock_code,
                    client=client,
                    rate_limiter=limiter,
                    prefer_cache=prefer_cache,
                )
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
    source = normalize_listing_source(
        product.get("source") or product.get("provenance")
    )
    if existing:
        existing.price = price
        existing.units_sold_est = units
        existing.revenue_est = revenue
        existing.rating = product.get("rating")
        existing.source = source
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
            source=source,
        )
    )
    return True


def run_marketplace_crawl(
    db: Session,
    *,
    attempt_live: bool = True,
    client: httpx.Client | None = None,
    discover: bool | None = None,
) -> int:
    """Crawl marketplace shops + listings for companies in DB. Idempotent upserts.

    Signature kept compatible with pipeline: ``run_marketplace_crawl(db)``.
    Discovery is OFF by default (``discover=None`` → env flag); when ON, only
    QA-allowlisted candidates that pass threshold 0.65 are linked.
    """
    matcher = ShopMatcher()
    try:
        matcher.train(db)
    except Exception as exc:  # joblib / disk optional — do not fail crawl
        logger.warning("ShopMatcher.train skipped: %s", exc)

    discovery_on = (
        is_marketplace_discovery_enabled() if discover is None else bool(discover)
    )
    allowlist = load_discovery_allowlist() if discovery_on else []
    discovery_cut = marketplace_discovery_threshold()

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
    aggregate_counts = {"live": 0, "seed": 0, "fallback": 0, "empty": 0, "other": 0}

    for company in companies:
        shops = list(find_shops_for_company(company))
        if discovery_on:
            shops.extend(
                discover_shops_for_company(
                    company,
                    enabled=True,
                    allowlist=allowlist,
                    matcher=matcher,
                    threshold=discovery_cut,
                )
            )
        # Deduplicate by URL (seed wins over discovery)
        seen: set[str] = set()
        unique_shops: list[dict[str, Any]] = []
        for shop in shops:
            url = shop.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            unique_shops.append(shop)

        for shop in unique_shops:
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
        pc = provenance_counts(products)
        for key, val in pc.items():
            aggregate_counts[key] = aggregate_counts.get(key, 0) + val
        for product in products:
            if _upsert_listing(db, company, product):
                count += 1

    logger.info(
        "Marketplace crawl provenance counts: live=%s seed=%s fallback=%s empty=%s other=%s "
        "(discovery=%s)",
        aggregate_counts.get("live", 0),
        aggregate_counts.get("seed", 0),
        aggregate_counts.get("fallback", 0),
        aggregate_counts.get("empty", 0),
        aggregate_counts.get("other", 0),
        discovery_on,
    )
    db.commit()
    return count
