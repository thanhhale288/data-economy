"""Tier compare: agree / conflict / abstain / skip."""

from __future__ import annotations

from crawlers.extraction_cascade.compare import compare_tiers
from crawlers.extraction_cascade.schema import Tier1Indicators


def _tier2(
    *,
    catalog: bool | None = True,
    cart: bool | None = True,
    pay: list | None = None,
    social: list | None = None,
    mkt: list | None = None,
    lang: str | None = "vi",
    abstain: bool = False,
) -> dict:
    def bf(value):
        return {
            "value": value,
            "confidence": 0.0 if abstain else 0.9,
            "abstain": abstain,
            "reason": "test",
        }

    return {
        "has_product_catalog": bf(catalog),
        "has_order_cart": bf(cart),
        "payment_methods": bf(pay or []),
        "social_links": bf(social or []),
        "marketplace_links": bf(mkt or []),
        "website_language": bf(lang),
    }


def test_compare_skip_when_fetch_fails():
    rows = compare_tiers("X", None, None, fetch_ok=False)
    assert len(rows) == 1
    assert rows[0].kind == "skip"


def test_compare_agree_on_matching_bools():
    t1 = Tier1Indicators(has_product_catalog=True, has_order_cart=True, website_language="vi")
    rows = compare_tiers("X", t1, _tier2(), fetch_ok=True)
    by_field = {r.field: r for r in rows}
    assert by_field["has_order_cart"].kind == "agree"
    assert by_field["has_product_catalog"].kind == "agree"


def test_compare_conflict_when_tier2_disagrees_cart():
    t1 = Tier1Indicators(has_product_catalog=True, has_order_cart=True)
    rows = compare_tiers("X", t1, _tier2(cart=False), fetch_ok=True)
    cart = next(r for r in rows if r.field == "has_order_cart")
    assert cart.kind == "conflict"


def test_compare_abstain_when_tier2_abstains():
    t1 = Tier1Indicators(has_order_cart=False)
    rows = compare_tiers("X", t1, _tier2(abstain=True), fetch_ok=True)
    assert all(r.kind == "abstain" for r in rows if r.field != "*")


def test_compare_marketplace_presence_conflict():
    t1 = Tier1Indicators(
        marketplace_links=[{"platform": "shopee", "url": "https://shopee.vn/a"}]
    )
    rows = compare_tiers("X", t1, _tier2(mkt=[]), fetch_ok=True)
    mkt = next(r for r in rows if r.field == "marketplace_links")
    assert mkt.kind == "conflict"
