"""TikTok Shop listing fetch + parse (offline-testable)."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

import httpx

from crawlers.marketplace.common import (
    HTTP_TIMEOUT,
    FetchResult,
    compute_revenue_est,
    parse_number,
)

logger = logging.getLogger(__name__)

BLOCK_MARKERS = (
    "access denied",
    "captcha",
    "verify you are human",
    "unusual traffic",
    "please wait",
    "tiktok_anti_bot",
)


def detect_tiktok_block(html_or_text: str) -> bool:
    lower = html_or_text.lower()
    return any(marker in lower for marker in BLOCK_MARKERS)


def parse_tiktok_listings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse a TikTok Shop products JSON document into listing dicts."""
    products = payload.get("products") or payload.get("items") or []
    listings: list[dict[str, Any]] = []
    for product in products:
        name = product.get("title") or product.get("name") or product.get("product_name")
        if not name:
            continue
        price_obj = product.get("price")
        if isinstance(price_obj, dict):
            price = parse_number(price_obj.get("sale_price") or price_obj.get("price"))
        else:
            price = parse_number(price_obj)
        units = parse_number(
            product.get("sold_count")
            or product.get("units_sold")
            or product.get("historical_sold")
        )
        units_int = int(units) if units is not None else None
        rating = parse_number(product.get("rating") or product.get("rating_star"))
        product_id = product.get("product_id") or product.get("id")
        product_url = None
        if product_id is not None:
            product_url = f"https://www.tiktok.com/shop/pdp/{product_id}"

        listings.append(
            {
                "platform": "tiktok",
                "product_name": str(name).strip(),
                "price": float(price) if price is not None else None,
                "units_sold_est": units_int,
                "revenue_est": compute_revenue_est(
                    float(price) if price is not None else None, units_int
                ),
                "rating": float(rating) if rating is not None else None,
                "product_url": product_url,
            }
        )
    return listings


def fetch_tiktok_listings(
    shop_url: str,
    *,
    client: httpx.Client | None = None,
    rate_limiter: Callable[[], None] | None = None,
) -> FetchResult:
    """Best-effort live TikTok fetch. On anti-bot / HTTP fail → empty + blocked/error."""
    if rate_limiter:
        rate_limiter()

    own_client = client is None
    http = client or httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True)
    try:
        response = http.get(shop_url, headers={"User-Agent": "mfg-data-economy/1.0"})
        if response.status_code in {403, 429, 503}:
            detail = f"HTTP {response.status_code} for {shop_url}"
            logger.warning("TikTok fetch blocked/error: %s", detail)
            return FetchResult(status="blocked", detail=detail, listings=[])

        if response.status_code >= 400:
            detail = f"HTTP {response.status_code} for {shop_url}"
            logger.warning("TikTok fetch error: %s", detail)
            return FetchResult(status="error", detail=detail, listings=[])

        content_type = response.headers.get("content-type", "")
        text = response.text

        if detect_tiktok_block(text):
            detail = "TikTok anti-bot / captcha / access denied"
            logger.warning("TikTok fetch blocked: %s (%s)", detail, shop_url)
            return FetchResult(status="blocked", detail=detail, listings=[])

        if "application/json" in content_type or text.strip().startswith("{"):
            try:
                payload = response.json()
            except json.JSONDecodeError:
                payload = json.loads(text)
            listings = parse_tiktok_listings(payload)
            if not listings:
                return FetchResult(
                    status="empty",
                    detail="TikTok JSON parsed but no products",
                    listings=[],
                    source="live",
                )
            return FetchResult(
                status="ok",
                detail=f"parsed {len(listings)} products",
                listings=listings,
                source="live",
            )

        logger.info("TikTok HTML without structured products for %s", shop_url)
        return FetchResult(
            status="empty",
            detail="TikTok HTML without parseable listings",
            listings=[],
            source="live",
        )
    except httpx.HTTPError as exc:
        detail = f"network error: {exc}"
        logger.warning("TikTok fetch network error for %s: %s", shop_url, exc)
        return FetchResult(status="error", detail=detail, listings=[])
    finally:
        if own_client:
            http.close()
