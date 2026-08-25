"""Tier-1 rules: cart, payments, marketplace/social links from HTML fixtures."""

from __future__ import annotations

from pathlib import Path

from crawlers.extraction_cascade.tier1_rules import analyze_page_rules

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_full_signals_detect_cart_payment_marketplace_social():
    result = analyze_page_rules(
        _load("site_full_signals.html"),
        base_url="https://abc.example/",
    )
    assert result.has_product_catalog is True
    assert result.has_order_cart is True
    assert "vnpay" in result.payment_methods
    assert "momo" in result.payment_methods
    assert "cod" in result.payment_methods
    platforms = {m["platform"] for m in result.marketplace_links}
    assert "shopee" in platforms
    assert "lazada" in platforms
    social = {s["platform"] for s in result.social_links}
    assert "facebook" in social
    assert result.website_language == "vi"


def test_corporate_en_has_no_ecommerce_signals():
    result = analyze_page_rules(_load("site_corporate_en.html"))
    assert result.has_order_cart is False
    assert result.payment_methods == []
    assert result.marketplace_links == []
    assert result.social_links == []
    assert result.website_language in {"en", "unknown", "mixed"}


def test_empty_html_has_no_signals():
    result = analyze_page_rules("")
    assert result.has_product_catalog is False
    assert result.has_order_cart is False
    assert result.payment_methods == []
