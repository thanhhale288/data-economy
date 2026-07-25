"""Epic 3 Task #25 — BCTC fallback covers full seed allowlist."""

from __future__ import annotations

import json
from pathlib import Path

from crawlers.financial.bctc_crawler import (
    FALLBACK_FILE,
    FINANCIAL_FIELDS,
    SEED_FILE,
    load_fallback_financial,
    load_seed_financial,
)


def _seed_companies() -> list[dict]:
    raw = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    return raw["companies"] if isinstance(raw, dict) else raw


def test_bctc_fallback_covers_full_seed_allowlist():
    companies = _seed_companies()
    seed_codes = {c["stock_code"] for c in companies if (c.get("financial") or {}).get("period")}
    fallback = json.loads(FALLBACK_FILE.read_text(encoding="utf-8"))
    fb_codes = {row["stock_code"] for row in fallback}
    assert seed_codes == fb_codes
    assert len(fb_codes) >= 25


def test_bmp_fallback_employees_matches_seed_null():
    seed = load_seed_financial("BMP")
    fb = load_fallback_financial("BMP")
    assert seed is not None and fb is not None
    assert seed.get("employees") is None
    assert fb.get("employees") is None


def test_new_ticker_fallback_fields_subset_of_seed():
    """VHC (Epic 2 peer) fallback must not invent fields beyond seed."""
    seed = load_seed_financial("VHC")
    fb = load_fallback_financial("VHC")
    assert seed is not None and fb is not None
    for key in FINANCIAL_FIELDS:
        assert fb.get(key) == seed.get(key)
