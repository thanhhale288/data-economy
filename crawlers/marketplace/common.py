"""Shared marketplace crawl helpers: rate limit, revenue, provenance, fetch result."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SEED_FILE = DATA_DIR / "seeds" / "companies.json"
FALLBACK_FILE = DATA_DIR / "raw" / "marketplace_listings_fallback.json"

SEED_SOURCE = "seed:companies.json"
FALLBACK_SOURCE = "fallback:data/raw/marketplace_listings_fallback.json"

# Shopee API often encodes VND as integer * 100_000
SHOPEE_PRICE_DIVISOR = 100_000

HTTP_TIMEOUT = 20.0
DEFAULT_MIN_INTERVAL_SEC = 1.5

MARKETPLACE_CHANNELS = frozenset({"shopee", "tiktok", "lazada"})


@dataclass
class FetchResult:
    """Outcome of a marketplace listing fetch."""

    status: str  # ok | blocked | error | empty
    detail: str
    listings: list[dict[str, Any]] = field(default_factory=list)
    source: str | None = None


class RateLimiter:
    """Simple minimum-interval rate limiter for marketplace HTTP calls."""

    def __init__(self, min_interval_sec: float = DEFAULT_MIN_INTERVAL_SEC):
        self.min_interval_sec = min_interval_sec
        self._last_call = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        if self._last_call > 0 and elapsed < self.min_interval_sec:
            time.sleep(self.min_interval_sec - elapsed)
        self._last_call = time.monotonic()


def compute_revenue_est(
    price: float | int | None, units_sold: int | None
) -> float | None:
    """Revenue estimate only when both price and units are known — never invent."""
    if price is None or units_sold is None:
        return None
    return float(price) * int(units_sold)


def parse_number(raw: Any) -> float | int | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return raw
    text = str(raw).strip().replace(",", "").replace(" ", "")
    if not text or text.lower() in {"null", "none", "n/a", "-", "—"}:
        return None
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return None


def load_seed_companies() -> list[dict[str, Any]]:
    with open(SEED_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_seed_for_ticker(stock_code: str) -> dict[str, Any] | None:
    return next(
        (s for s in load_seed_companies() if s["stock_code"] == stock_code), None
    )


def load_fallback_listings(stock_code: str) -> list[dict[str, Any]]:
    """Load sourced fallback listings; empty if file missing."""
    if not FALLBACK_FILE.exists():
        return []
    with open(FALLBACK_FILE, encoding="utf-8") as f:
        payload = json.load(f)
    for row in payload.get("companies", []):
        if row.get("stock_code") == stock_code:
            return list(row.get("marketplace_listings") or [])
    return []


def annotate_provenance(
    listings: list[dict[str, Any]], provenance: str
) -> list[dict[str, Any]]:
    out = []
    for item in listings:
        row = dict(item)
        row["provenance"] = provenance
        # Recompute revenue only from present fields — never invent units/price
        row["revenue_est"] = compute_revenue_est(
            row.get("price"), row.get("units_sold_est")
        )
        out.append(row)
    return out


def default_rate_limiter() -> Callable[[], None]:
    limiter = RateLimiter()
    return limiter.wait
