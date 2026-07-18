"""Website ecommerce/checkout detector — offline HTML fixtures + HTTP fail semantics."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx

from crawlers.companies.website_detector import (
    DetectionResult,
    analyze_html,
    detect_website,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_analyze_html_detects_checkout_on_ecommerce_page():
    result = analyze_html(_load("site_with_checkout.html"))
    assert result.ok is True
    assert result.has_ecommerce is True
    assert result.has_checkout is True


def test_analyze_html_corporate_site_has_neither_flag():
    result = analyze_html(_load("site_without_checkout.html"))
    assert result.ok is True
    assert result.has_ecommerce is False
    assert result.has_checkout is False


def test_analyze_html_empty_page_has_neither_flag():
    result = analyze_html(_load("site_empty.html"))
    assert result.ok is True
    assert result.has_ecommerce is False
    assert result.has_checkout is False


def test_analyze_html_shop_catalog_without_checkout():
    result = analyze_html(_load("site_shop_no_checkout.html"))
    assert result.ok is True
    assert result.has_ecommerce is True
    assert result.has_checkout is False


def test_detect_website_ok_uses_html_body(monkeypatch):
    html = _load("site_with_checkout.html")

    def ok(self, url, **_kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(200, request=request, text=html)

    monkeypatch.setattr(httpx.Client, "get", ok)

    result = detect_website("https://example.com/shop")
    assert result.ok is True
    assert result.has_ecommerce is True
    assert result.has_checkout is True


def test_detect_website_http_error_does_not_guess(monkeypatch):
    def blocked(self, url, **_kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(403, request=request, text="forbidden")

    monkeypatch.setattr(httpx.Client, "get", blocked)

    result = detect_website("https://blocked.example/")
    assert result.ok is False
    assert result.has_ecommerce is False
    assert result.has_checkout is False
    assert result.detail  # explicit fail reason


def test_detect_website_network_error_does_not_guess(monkeypatch):
    def boom(self, url, **_kwargs):
        raise httpx.ConnectError("connection refused", request=MagicMock())

    monkeypatch.setattr(httpx.Client, "get", boom)

    result = detect_website("https://down.example/")
    assert isinstance(result, DetectionResult)
    assert result.ok is False
    assert result.has_ecommerce is False
    assert result.has_checkout is False
    assert result.detail
