"""Task #43 — marketplace shop search candidates + QA allowlist formatting."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from crawlers.marketplace import shop_finder


def test_search_empty_query_returns_empty():
    out = shop_finder.search_marketplace_shop_candidates("")
    assert out["status"] == "empty"
    assert out["candidates"] == []


def test_search_unsupported_channel():
    out = shop_finder.search_marketplace_shop_candidates("rang dong", channel="lazada")
    assert out["status"] == "error"
    assert out["candidates"] == []


def test_search_parses_shopee_candidates_from_html():
    html = """
    <html><body>
      <a href="https://shopee.vn/rangdong_official">shop</a>
      <a href="https://shopee.vn/search">noise</a>
      <a href="https://shopee.vn/other_lamp_store">other</a>
    </body></html>
    """
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text=html, request=request)
    )
    with httpx.Client(transport=transport) as client:
        out = shop_finder.search_marketplace_shop_candidates(
            "rang dong", channel="shopee", client=client
        )
    assert out["status"] == "ok"
    urls = {c["url"] for c in out["candidates"]}
    assert "https://shopee.vn/rangdong_official" in urls
    assert "https://shopee.vn/other_lamp_store" in urls
    assert all(c["source"] == "marketplace_search" for c in out["candidates"])


def test_search_blocked_on_403():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(403, text="Access Denied", request=request)
    )
    with httpx.Client(transport=transport) as client:
        out = shop_finder.search_marketplace_shop_candidates(
            "rang dong", channel="shopee", client=client
        )
    assert out["status"] == "blocked"
    assert out["candidates"] == []


def test_search_blocked_on_antibot_body():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, text="Please verify you are human / captcha", request=request
        )
    )
    with httpx.Client(transport=transport) as client:
        out = shop_finder.search_marketplace_shop_candidates(
            "vinamilk", channel="shopee", client=client
        )
    assert out["status"] == "blocked"
    assert out["candidates"] == []


def test_candidates_to_qa_allowlist_entries_do_not_invent():
    entries = shop_finder.candidates_to_qa_allowlist_entries(
        "RAL",
        [
            {
                "channel_type": "shopee",
                "url": "https://shopee.vn/rangdong_official",
                "shop_name": "rangdong_official",
            }
        ],
    )
    assert len(entries) == 1
    assert entries[0]["ticker"] == "RAL"
    assert entries[0]["url"] == "https://shopee.vn/rangdong_official"
    assert "qa_note" in entries[0]
    # Empty candidates → empty allowlist rows
    assert shop_finder.candidates_to_qa_allowlist_entries("RAL", []) == []


def test_search_candidates_never_auto_link_without_gate(monkeypatch):
    """Search output must not bypass discover_shops_for_company (#36)."""
    monkeypatch.delenv(shop_finder.DISCOVERY_ENABLED_ENV, raising=False)
    company = MagicMock()
    company.stock_code = "RAL"
    company.name = "Công ty Cổ phần Bóng đèn Rạng Đông"
    qa_rows = shop_finder.candidates_to_qa_allowlist_entries(
        "RAL",
        [
            {
                "channel_type": "shopee",
                "url": "https://shopee.vn/rangdong_official",
                "shop_name": "rangdong_official",
            }
        ],
    )
    # Discovery OFF → still []
    assert (
        shop_finder.discover_shops_for_company(company, allowlist=qa_rows) == []
    )
    # Discovery ON + allowlist → qa_discovery
    monkeypatch.setenv(shop_finder.DISCOVERY_ENABLED_ENV, "1")
    linked = shop_finder.discover_shops_for_company(
        company, enabled=True, allowlist=qa_rows
    )
    assert len(linked) == 1
    assert linked[0]["match_source"] == "qa_discovery"
