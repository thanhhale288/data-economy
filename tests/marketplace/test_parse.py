"""Offline parser tests for Shopee / TikTok listing fixtures — no network."""

from __future__ import annotations

import pytest

from crawlers.marketplace.common import compute_revenue_est
from crawlers.marketplace.shopee import parse_shopee_listings, detect_shopee_block
from crawlers.marketplace.tiktok import parse_tiktok_listings
from tests.marketplace.conftest import load_fixture_json, load_fixture_text


def test_compute_revenue_est_only_when_price_and_units_present():
    assert compute_revenue_est(45000, 12500) == 562500000
    assert compute_revenue_est(45000, None) is None
    assert compute_revenue_est(None, 12500) is None
    assert compute_revenue_est(None, None) is None


def test_parse_shopee_listings_extracts_price_units_and_revenue():
    payload = load_fixture_json("shopee_ral_listings.json")
    listings = parse_shopee_listings(payload)

    assert len(listings) == 3

    led = listings[0]
    assert led["platform"] == "shopee"
    assert led["product_name"] == "Bóng LED Rạng Đông 9W"
    assert led["price"] == 45000
    assert led["units_sold_est"] == 12500
    assert led["revenue_est"] == 562500000
    assert led["rating"] == pytest.approx(4.8)

    panel = listings[1]
    assert panel["price"] == 285000
    assert panel["units_sold_est"] == 3200
    assert panel["revenue_est"] == 912000000

    # price without units → revenue stays null (never invent sales)
    price_only = listings[2]
    assert price_only["price"] == 159000
    assert price_only["units_sold_est"] is None
    assert price_only["revenue_est"] is None


def test_parse_shopee_partial_nulls_keeps_revenue_null():
    payload = load_fixture_json("shopee_partial_nulls.json")
    listings = parse_shopee_listings(payload)

    assert listings[0]["price"] == 100000
    assert listings[0]["units_sold_est"] is None
    assert listings[0]["revenue_est"] is None

    assert listings[1]["price"] is None
    assert listings[1]["units_sold_est"] == 50
    assert listings[1]["revenue_est"] is None


def test_detect_shopee_block_on_anti_bot_html():
    html = load_fixture_text("shopee_blocked.html")
    assert detect_shopee_block(html) is True


def test_parse_tiktok_listings_extracts_fields_and_null_revenue():
    payload = load_fixture_json("tiktok_vnm_listings.json")
    listings = parse_tiktok_listings(payload)

    assert len(listings) == 2
    assert listings[0]["platform"] == "tiktok"
    assert listings[0]["product_name"] == "Sữa tươi Vinamilk 1L (TikTok)"
    assert listings[0]["price"] == 32000
    assert listings[0]["units_sold_est"] == 1200
    assert listings[0]["revenue_est"] == 38400000
    assert listings[0]["rating"] == pytest.approx(4.9)

    assert listings[1]["price"] == 28000
    assert listings[1]["units_sold_est"] is None
    assert listings[1]["revenue_est"] is None
