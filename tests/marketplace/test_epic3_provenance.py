"""Epic 3 — marketplace provenance + Playwright follow-up."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx

from crawlers.marketplace.common import (
    SEED_SOURCE,
    FetchResult,
    normalize_listing_source,
    provenance_counts,
)
from crawlers.marketplace.shopee import fetch_shopee_listings, parse_shopee_listings
from crawlers.marketplace.shop_finder import scrape_marketplace_products
from tests.marketplace.conftest import load_fixture_json


def test_normalize_listing_source_tags():
    assert normalize_listing_source("live") == "live"
    assert normalize_listing_source(SEED_SOURCE) == "seed"
    assert normalize_listing_source("fallback:data/raw/marketplace_listings_fallback.json") == "fallback"


def test_annotate_sets_source_field():
    from crawlers.marketplace.common import annotate_provenance

    rows = annotate_provenance(
        [{"platform": "shopee", "product_name": "X", "price": 1, "units_sold_est": 2}],
        SEED_SOURCE,
    )
    assert rows[0]["source"] == "seed"
    assert rows[0]["provenance"] == SEED_SOURCE


def test_playwright_follow_up_parses_json(monkeypatch):
    html = "<html><body>no items</body></html>"

    def fake_get(self, url, **_kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(200, request=request, text=html, headers={"content-type": "text/html"})

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    payload = load_fixture_json("shopee_ral_listings.json")

    def fake_pw(url, *, parse_listings, detect_block, platform):
        listings = parse_listings(payload)
        return FetchResult(status="ok", detail="pw", listings=listings, source="live")

    monkeypatch.setattr(
        "crawlers.marketplace.browser_fetch.fetch_listings_via_playwright",
        fake_pw,
    )

    result = fetch_shopee_listings("https://shopee.vn/rangdong_official", use_playwright=True)
    assert result.status == "ok"
    assert result.source == "live"
    assert len(result.listings) >= 1


def test_block_still_falls_back_to_seed(monkeypatch, sample_company):
    def blocked(*_a, **_k):
        return FetchResult(status="blocked", detail="anti-bot", listings=[], source=None)

    monkeypatch.setattr(
        "crawlers.marketplace.shop_finder.fetch_shopee_listings",
        blocked,
    )
    products = scrape_marketplace_products(sample_company, attempt_live=True)
    assert products
    assert all(p.get("source") == "seed" for p in products)
    counts = provenance_counts(products)
    assert counts["seed"] >= 1
