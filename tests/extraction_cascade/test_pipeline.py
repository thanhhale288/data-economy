"""Cascade pipeline offline: HTML in → tiers out (LLM disabled)."""

from __future__ import annotations

from pathlib import Path

from crawlers.extraction_cascade.pipeline import flatten_indicator_rows, run_on_page
from crawlers.extraction_cascade.schema import RenderedPage

FIXTURES = Path(__file__).parent / "fixtures"


def test_run_on_page_tier1_and_disabled_tier2():
    html = (FIXTURES / "site_full_signals.html").read_text(encoding="utf-8")
    page = RenderedPage(
        url="https://abc.example/",
        final_url="https://abc.example/",
        ok=True,
        detail="ok",
        html=html,
        text="giỏ hàng VNPay Shopee",
    )
    result = run_on_page(
        firm_id="DEMO",
        source_cohort="listed28",
        website_url="https://abc.example/",
        page=page,
        llm_enabled=False,
    )
    assert result.fetch_ok is True
    assert result.tier1 is not None
    assert result.tier1.has_order_cart is True
    assert result.tier2_decision == "disabled"
    assert result.tier2 is not None
    assert result.tier2["has_order_cart"]["abstain"] is True
    assert any(c.kind == "abstain" for c in result.conflicts)

    rows = flatten_indicator_rows(result)
    tiers = {r["tier"] for r in rows}
    assert 1 in tiers and 2 in tiers


def test_run_on_page_fetch_fail_skips():
    page = RenderedPage(
        url="https://x.example/",
        final_url="https://x.example/",
        ok=False,
        detail="http_fail status=403",
    )
    result = run_on_page(
        firm_id="X",
        source_cohort="listed28",
        website_url="https://x.example/",
        page=page,
        llm_enabled=False,
    )
    assert result.fetch_ok is False
    assert result.tier1 is None
    assert result.conflicts[0].kind == "skip"
