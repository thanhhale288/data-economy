"""Epic 3 Task #26 — digital presence seed honesty."""

from __future__ import annotations

import json
from pathlib import Path

SEED = Path(__file__).resolve().parents[2] / "data" / "seeds" / "companies.json"


def _companies() -> list[dict]:
    raw = json.loads(SEED.read_text(encoding="utf-8"))
    return raw["companies"] if isinstance(raw, dict) else raw


def test_marketplace_channel_flags_require_digital_presence_url():
    for c in _companies():
        channels = c.get("digital_channels") or {}
        dps = c.get("digital_presence") or []
        for platform in ("shopee", "tiktok", "lazada"):
            if channels.get(platform):
                urls = [d for d in dps if d.get("channel_type") == platform and d.get("url")]
                assert urls, f"{c['stock_code']} flags {platform}=true without DP URL"


def test_dqc_has_shopee_url():
    dqc = next(c for c in _companies() if c["stock_code"] == "DQC")
    assert dqc["digital_channels"]["shopee"] is True
    assert any(d.get("channel_type") == "shopee" for d in dqc["digital_presence"])


def test_msn_tiktok_flag_honest_without_url():
    msn = next(c for c in _companies() if c["stock_code"] == "MSN")
    assert msn["digital_channels"]["tiktok"] is False


def test_dqc_listings_do_not_invent_marketplace_gmv():
    """Task #34: curated DQC depth must not invent units/revenue."""
    dqc = next(c for c in _companies() if c["stock_code"] == "DQC")
    listings = dqc.get("marketplace_listings") or []
    assert listings, "DQC should have curated catalog listings after #34"
    assert all(ml.get("units_sold_est") is None for ml in listings)
    assert all(ml.get("revenue_est") is None for ml in listings)


def test_zero_marketplace_flags_without_url_across_allowlist():
    """Task #33 AC: 0 flag marketplace=true missing DP URL."""
    bad: list[str] = []
    for c in _companies():
        channels = c.get("digital_channels") or {}
        dps = c.get("digital_presence") or []
        for platform in ("shopee", "tiktok", "lazada"):
            if not channels.get(platform):
                continue
            if not any(
                d.get("channel_type") == platform and d.get("url") for d in dps
            ):
                bad.append(f"{c['stock_code']}:{platform}")
    assert bad == []


def test_ecommerce_site_flag_has_website_or_marketplace_url():
    for c in _companies():
        if not c.get("has_ecommerce_site"):
            continue
        dps = c.get("digital_presence") or []
        assert any(d.get("url") for d in dps), (
            f"{c['stock_code']} has_ecommerce_site=true without any DP URL"
        )
