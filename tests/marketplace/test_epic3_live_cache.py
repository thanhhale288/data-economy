"""Task #35 — allowlist live cache + block→seed honesty."""

from __future__ import annotations

from crawlers.marketplace.common import (
    SEED_SOURCE,
    FetchResult,
    normalize_listing_source,
    provenance_counts,
)
from crawlers.marketplace.live_cache import (
    is_cache_allowed,
    load_cached_listings,
    load_live_cache_allowlist,
    marketplace_request_headers,
    provenance_tag,
    session_cookie_headers,
)
from crawlers.marketplace.shop_finder import scrape_marketplace_products


def test_session_cookie_headers_ops_only(monkeypatch):
    """ADR-0002 §2: Cookie header only when env set; never invent listings."""
    monkeypatch.delenv("SHOPEE_SESSION_COOKIE", raising=False)
    monkeypatch.delenv("TIKTOK_SESSION_COOKIE", raising=False)
    assert session_cookie_headers("shopee") == {}
    assert session_cookie_headers("tiktok") == {}

    monkeypatch.setenv("SHOPEE_SESSION_COOKIE", "spc_test=1")
    monkeypatch.setenv("TIKTOK_SESSION_COOKIE", "tt_test=1")
    assert session_cookie_headers("shopee") == {"Cookie": "spc_test=1"}
    assert session_cookie_headers("tiktok") == {"Cookie": "tt_test=1"}
    headers = marketplace_request_headers("shopee")
    assert headers["Cookie"] == "spc_test=1"
    assert "User-Agent" in headers


def test_live_cache_allowlist_includes_ral_vnm():
    allow = load_live_cache_allowlist()
    assert "shopee" in allow.get("RAL", [])
    assert "tiktok" in allow.get("VNM", [])
    assert not is_cache_allowed("HPG", "shopee")


def test_cache_hit_ral_shopee_source_live_no_invent():
    listings = load_cached_listings("RAL", "shopee")
    assert listings
    assert all(normalize_listing_source(r.get("source")) == "live" for r in listings)
    assert all(
        str(r.get("provenance", "")).startswith("live:cache:") for r in listings
    )
    # Revenue only when both price and units present
    for row in listings:
        if row.get("price") is None or row.get("units_sold_est") is None:
            assert row.get("revenue_est") is None
        else:
            assert row["revenue_est"] == float(row["price"]) * int(row["units_sold_est"])


def test_cache_miss_outside_allowlist():
    assert load_cached_listings("FPT", "shopee") == []
    assert load_cached_listings("RAL", "tiktok") == []


def test_block_falls_back_to_cache_then_seed(monkeypatch, sample_company):
    """HTTP block on RAL → allowlisted cache (source=live), not invent."""

    def blocked(*_a, **_k):
        return FetchResult(status="blocked", detail="anti-bot", listings=[], source=None)

    monkeypatch.setattr(
        "crawlers.marketplace.shop_finder.fetch_shopee_listings",
        blocked,
    )
    products = scrape_marketplace_products(sample_company, attempt_live=True)
    assert products
    assert all(p.get("source") == "live" for p in products)
    assert all("live:cache:" in str(p.get("provenance", "")) for p in products)
    counts = provenance_counts(products)
    assert counts["live"] >= 1
    assert counts["seed"] == 0


def test_block_without_cache_falls_to_seed(monkeypatch, sample_company):
    """If cache disabled/missing for ticker, block → seed (honesty contract)."""

    def blocked(*_a, **_k):
        return FetchResult(status="blocked", detail="anti-bot", listings=[], source=None)

    monkeypatch.setattr(
        "crawlers.marketplace.shop_finder.fetch_shopee_listings",
        blocked,
    )
    monkeypatch.setattr(
        "crawlers.marketplace.shop_finder.load_cached_listings",
        lambda *_a, **_k: [],
    )
    products = scrape_marketplace_products(sample_company, attempt_live=True)
    assert products
    assert all(p.get("source") == "seed" for p in products)
    assert provenance_counts(products)["seed"] >= 1


def test_prefer_cache_skips_http(monkeypatch, sample_company):
    called = {"n": 0}

    def boom(*_a, **_k):
        called["n"] += 1
        raise AssertionError("HTTP must not be called when prefer_cache hits")

    monkeypatch.setattr(
        "crawlers.marketplace.shop_finder.fetch_shopee_listings",
        boom,
    )
    products = scrape_marketplace_products(
        sample_company, attempt_live=True, prefer_cache=True
    )
    assert products
    assert called["n"] == 0
    assert all(p.get("source") == "live" for p in products)


def test_normalize_live_cache_provenance():
    tag = provenance_tag("RAL", "shopee")
    assert normalize_listing_source(tag) == "live"
    assert tag.startswith("live:cache:")
    assert SEED_SOURCE  # contract still imports
