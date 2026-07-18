"""Fetch / fallback tests — network mocked; never invent sales on block."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from backend.app.models import Company
from crawlers.marketplace import shop_finder
from crawlers.marketplace.common import SEED_SOURCE, FALLBACK_SOURCE
from crawlers.marketplace.shopee import fetch_shopee_listings
from crawlers.marketplace.tiktok import fetch_tiktok_listings
from tests.marketplace.conftest import load_fixture_json, load_fixture_text


def _mock_response(status_code: int, text: str = "", json_data=None) -> httpx.Response:
    request = httpx.Request("GET", "https://example.test/")
    if json_data is not None:
        import json

        content = json.dumps(json_data).encode()
        headers = {"content-type": "application/json"}
    else:
        content = text.encode()
        headers = {"content-type": "text/html"}
    return httpx.Response(status_code, content=content, headers=headers, request=request)


def test_fetch_shopee_ok_parses_live_json():
    payload = load_fixture_json("shopee_ral_listings.json")
    client = MagicMock()
    client.get.return_value = _mock_response(200, json_data=payload)

    result = fetch_shopee_listings(
        "https://shopee.vn/rangdong_official",
        client=client,
        rate_limiter=lambda: None,
    )

    assert result.status == "ok"
    assert result.source == "live"
    assert len(result.listings) == 3
    assert result.listings[0]["revenue_est"] == 562500000


def test_fetch_shopee_block_returns_empty_status():
    html = load_fixture_text("shopee_blocked.html")
    client = MagicMock()
    client.get.return_value = _mock_response(200, text=html)

    result = fetch_shopee_listings(
        "https://shopee.vn/rangdong_official",
        client=client,
        rate_limiter=lambda: None,
    )

    assert result.status == "blocked"
    assert result.listings == []
    assert "block" in result.detail.lower() or "captcha" in result.detail.lower() or "denied" in result.detail.lower()


def test_fetch_shopee_http_error_returns_empty():
    client = MagicMock()
    client.get.return_value = _mock_response(403, text="Forbidden")

    result = fetch_shopee_listings(
        "https://shopee.vn/rangdong_official",
        client=client,
        rate_limiter=lambda: None,
    )

    assert result.status in {"error", "blocked"}
    assert result.listings == []


def test_fetch_tiktok_ok_parses_live_json():
    payload = load_fixture_json("tiktok_vnm_listings.json")
    client = MagicMock()
    client.get.return_value = _mock_response(200, json_data=payload)

    result = fetch_tiktok_listings(
        "https://www.tiktok.com/@vinamilk",
        client=client,
        rate_limiter=lambda: None,
    )

    assert result.status == "ok"
    assert len(result.listings) == 2
    assert result.listings[0]["units_sold_est"] == 1200


def test_scrape_products_falls_back_to_seed_on_block(sample_company, monkeypatch):
    def fake_fetch(*_args, **_kwargs):
        from crawlers.marketplace.common import FetchResult

        return FetchResult(status="blocked", detail="anti-bot", listings=[], source=None)

    monkeypatch.setattr(shop_finder, "fetch_shopee_listings", fake_fetch)
    monkeypatch.setattr(shop_finder, "fetch_tiktok_listings", fake_fetch)

    products = shop_finder.scrape_marketplace_products(
        sample_company, client=MagicMock(), attempt_live=True
    )

    assert len(products) >= 1
    assert all(p.get("provenance") in {SEED_SOURCE, FALLBACK_SOURCE} for p in products)
    # Seed RAL listings include known LED product — not invented
    names = {p["product_name"] for p in products}
    assert "Bóng LED Rạng Đông 9W" in names
    for p in products:
        if p.get("price") is not None and p.get("units_sold_est") is not None:
            assert p["revenue_est"] == p["price"] * p["units_sold_est"]
        else:
            assert p.get("revenue_est") is None


def test_find_shops_only_from_seed_known_urls(sample_company):
    shops = shop_finder.find_shops_for_company(sample_company)
    assert shops
    assert all(s["channel_type"] in {"shopee", "tiktok", "lazada"} for s in shops)
    assert all(s["url"].startswith("http") for s in shops)
    # Seed shops must still pass matcher threshold 0.65
    assert all(s["is_match"] is True for s in shops)
    assert all(s["match_confidence"] >= 0.65 for s in shops)
    assert all(s["match_source"] == "seed_known_url" for s in shops)


def test_find_shops_empty_for_company_without_marketplace(db_session):
    company = Company(
        stock_code="HPG",
        name="Tập đoàn Hòa Phát",
        vsic_code="2740",
        exchange="HOSE",
    )
    db_session.add(company)
    db_session.commit()

    shops = shop_finder.find_shops_for_company(company)
    assert shops == []
