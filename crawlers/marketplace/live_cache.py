"""Small allowlist + versioned live-cache snapshots (Epic 3 Task #35).

Demo-stable path when Shopee/TikTok HTTP blocks. Never invents listings;
only loads allowlisted JSON under ``data/raw/marketplace_live_cache/``.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from crawlers.marketplace.common import DATA_DIR, annotate_provenance

logger = logging.getLogger(__name__)

LIVE_CACHE_DIR = DATA_DIR / "raw" / "marketplace_live_cache"
ALLOWLIST_FILE = LIVE_CACHE_DIR / "allowlist.json"

# Ops-only optional session cookies (never commit secrets). See ADR-0002.
SESSION_COOKIE_ENV = {
    "shopee": "SHOPEE_SESSION_COOKIE",
    "tiktok": "TIKTOK_SESSION_COOKIE",
}


def load_live_cache_allowlist(
    path: Path | None = None,
) -> dict[str, list[str]]:
    """Return ``{TICKER: [platform, …]}`` from allowlist.json (empty if missing)."""
    allow_path = path or ALLOWLIST_FILE
    if not allow_path.exists():
        return {}
    with open(allow_path, encoding="utf-8") as f:
        payload = json.load(f)
    raw = payload.get("tickers") or {}
    out: dict[str, list[str]] = {}
    for ticker, platforms in raw.items():
        code = str(ticker).strip().upper()
        if not code:
            continue
        out[code] = [str(p).strip().lower() for p in (platforms or []) if p]
    return out


def is_cache_allowed(stock_code: str, platform: str) -> bool:
    allow = load_live_cache_allowlist()
    platforms = allow.get(str(stock_code).strip().upper(), [])
    return str(platform).strip().lower() in platforms


def cache_file_path(stock_code: str, platform: str) -> Path:
    code = str(stock_code).strip().upper()
    plat = str(platform).strip().lower()
    return LIVE_CACHE_DIR / f"{code}.{plat}.json"


def provenance_tag(stock_code: str, platform: str) -> str:
    rel = cache_file_path(stock_code, platform).relative_to(DATA_DIR.parent)
    return f"live:cache:{rel.as_posix()}"


def load_cached_listings(
    stock_code: str,
    platform: str,
    *,
    allowlist_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Load + parse allowlisted cache snapshot; empty if not allowed or missing.

    Returns listings already annotated with ``source=live`` and
    ``provenance=live:cache:…``. Does not invent rows.
    """
    code = str(stock_code).strip().upper()
    plat = str(platform).strip().lower()
    allow = load_live_cache_allowlist(allowlist_path)
    if plat not in allow.get(code, []):
        return []

    path = cache_file_path(code, plat)
    if not path.exists():
        logger.info("Live cache miss (no file) for %s %s", code, plat)
        return []

    with open(path, encoding="utf-8") as f:
        payload = json.load(f)

    if plat == "shopee":
        from crawlers.marketplace.shopee import parse_shopee_listings

        listings = parse_shopee_listings(payload)
    elif plat == "tiktok":
        from crawlers.marketplace.tiktok import parse_tiktok_listings

        listings = parse_tiktok_listings(payload)
    else:
        logger.info("Live cache unsupported platform %s for %s", plat, code)
        return []

    if not listings:
        return []

    tag = provenance_tag(code, plat)
    logger.info(
        "Live cache hit for %s %s (%s items) provenance=%s",
        code,
        plat,
        len(listings),
        tag,
    )
    return annotate_provenance(listings, tag)


def session_cookie_headers(platform: str) -> dict[str, str]:
    """Optional Cookie header from env for ops-only live refresh. Empty if unset."""
    env_name = SESSION_COOKIE_ENV.get(str(platform).strip().lower())
    if not env_name:
        return {}
    value = os.environ.get(env_name, "").strip()
    if not value:
        return {}
    return {"Cookie": value}


def marketplace_request_headers(platform: str) -> dict[str, str]:
    """Default User-Agent plus optional ops session cookie."""
    headers = {"User-Agent": "mfg-data-economy/1.0"}
    headers.update(session_cookie_headers(platform))
    return headers
