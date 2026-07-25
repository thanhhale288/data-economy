"""Optional Playwright fetch for JS-heavy marketplace shop pages.

Used when httpx returns HTML without parseable listings. Never invents
price/units — empty/blocked stays empty for seed/fallback in the orchestrator.
"""

from __future__ import annotations

import json
import logging
from typing import Callable

from crawlers.marketplace.common import FetchResult

logger = logging.getLogger(__name__)

PLAYWRIGHT_TIMEOUT_MS = 30_000


def fetch_page_text_playwright(url: str) -> tuple[str, str]:
    """Return (text, content_type_hint). Raises on hard browser failures."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT_MS)
            text = page.content()
            return text, "text/html"
        finally:
            browser.close()


def fetch_listings_via_playwright(
    shop_url: str,
    *,
    parse_listings: Callable[[dict], list[dict]],
    detect_block: Callable[[str], bool],
    platform: str,
) -> FetchResult:
    """Load shop page with Chromium; parse JSON body or embedded JSON only."""
    try:
        text, _ = fetch_page_text_playwright(shop_url)
    except ImportError:
        return FetchResult(
            status="error",
            detail="playwright not installed",
            listings=[],
            source="live",
        )
    except Exception as exc:  # network / browser
        detail = f"playwright error: {exc}"
        logger.warning("Playwright fetch failed for %s: %s", shop_url, exc)
        return FetchResult(status="error", detail=detail, listings=[], source="live")

    if detect_block(text):
        return FetchResult(
            status="blocked",
            detail=f"{platform} anti-bot via Playwright",
            listings=[],
            source="live",
        )

    stripped = text.strip()
    payload = None
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
    if payload is None:
        # Try to extract a JSON blob from HTML (fixture-friendly)
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            try:
                payload = json.loads(stripped[start : end + 1])
            except json.JSONDecodeError:
                payload = None

    if not isinstance(payload, dict):
        return FetchResult(
            status="empty",
            detail=f"{platform} Playwright HTML without parseable listings",
            listings=[],
            source="live",
        )

    listings = parse_listings(payload)
    if not listings:
        return FetchResult(
            status="empty",
            detail=f"{platform} Playwright JSON parsed but no items",
            listings=[],
            source="live",
        )
    return FetchResult(
        status="ok",
        detail=f"playwright parsed {len(listings)} items",
        listings=listings,
        source="live",
    )
