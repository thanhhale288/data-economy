"""Epic 3 — marketplace provenance + Playwright follow-up."""

from __future__ import annotations

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


def test_new_listings_source_in_live_seed_fallback_contract():
    """Task #34: every seed listing source normalizes to live|seed|fallback."""
    import json
    from pathlib import Path

    seed = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "seeds" / "companies.json").read_text(
            encoding="utf-8"
        )
    )
    companies = seed["companies"] if isinstance(seed, dict) else seed
    allowed = {"live", "seed", "fallback"}
    for company in companies:
        for ml in company.get("marketplace_listings") or []:
            src = normalize_listing_source(ml.get("source") or "seed")
            assert src in allowed, f"{company['stock_code']} bad source={src!r}"


def test_dqc_curated_listings_no_invented_gmv():
    """DQC has shop + curated catalog rows; units/revenue stay null (no fake GMV)."""
    import json
    from pathlib import Path

    seed = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "seeds" / "companies.json").read_text(
            encoding="utf-8"
        )
    )
    companies = seed["companies"] if isinstance(seed, dict) else seed
    dqc = next(c for c in companies if c["stock_code"] == "DQC")
    assert any(d.get("channel_type") == "shopee" for d in dqc["digital_presence"])
    listings = dqc.get("marketplace_listings") or []
    assert len(listings) >= 1
    for ml in listings:
        assert normalize_listing_source(ml.get("source") or "seed") == "seed"
        assert ml.get("units_sold_est") is None
        assert ml.get("revenue_est") is None
        assert ml.get("price") is not None


def test_b2b_peers_without_shop_keep_empty_listings():
    """Task #34: B2B peers must not silently gain invented listings."""
    import json
    from pathlib import Path

    seed = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "seeds" / "companies.json").read_text(
            encoding="utf-8"
        )
    )
    companies = seed["companies"] if isinstance(seed, dict) else seed
    b2b = {"HPG", "BMP", "NKG", "POM", "TLH", "DCM", "BFC", "CSV"}
    for company in companies:
        if company["stock_code"] not in b2b:
            continue
        shops = [
            d
            for d in (company.get("digital_presence") or [])
            if d.get("channel_type") in {"shopee", "tiktok", "lazada"} and d.get("url")
        ]
        assert not shops, company["stock_code"]
        assert (company.get("marketplace_listings") or []) == []


def test_seed_listing_coverage_counts(monkeypatch):
    from crawlers.marketplace import listing_depth as ld

    rows = ld.seed_listing_coverage()
    summary = ld.summarize_coverage(rows)
    assert summary["tickers"] == 28
    assert summary["with_shop"] == 6
    assert summary["with_listing"] == 6
    assert summary["with_gmv_listing"] == 5
    assert "DQC" in summary["listing_tickers"]
    assert "DQC" not in summary["gmv_tickers"]
    assert "HPG" not in summary["listing_tickers"]


def test_live_smoke_tags_source_live_when_ok(monkeypatch):
    from crawlers.marketplace import listing_depth as ld
    from crawlers.marketplace.common import FetchResult

    def fake_shopee(url, **_kwargs):
        return FetchResult(
            status="ok",
            detail="mock",
            listings=[
                {
                    "platform": "shopee",
                    "product_name": "Mock LED",
                    "price": 1000,
                    "units_sold_est": 2,
                    "revenue_est": 2000,
                }
            ],
            source="live",
        )

    monkeypatch.setattr(ld, "fetch_shopee_listings", fake_shopee)
    monkeypatch.setattr(
        ld,
        "fetch_tiktok_listings",
        lambda *a, **k: FetchResult(status="empty", detail="skip", listings=[]),
    )
    status, _detail, listings = ld.attempt_live_for_shops(
        [("shopee", "https://shopee.vn/dienquang_officialstore")]
    )
    assert status == "ok"
    assert listings
    assert all(item.get("source") == "live" for item in listings)


def test_seed_fallback_listing_parity_for_allowlist():
    """Task #27/#34: fallback JSON mirrors seed listing keys per ticker."""
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    seed = json.loads((root / "data" / "seeds" / "companies.json").read_text(encoding="utf-8"))
    fb = json.loads(
        (root / "data" / "raw" / "marketplace_listings_fallback.json").read_text(
            encoding="utf-8"
        )
    )
    companies = seed["companies"] if isinstance(seed, dict) else seed
    by_seed = {
        c["stock_code"]: [
            (ml.get("platform"), ml.get("product_name"))
            for ml in (c.get("marketplace_listings") or [])
        ]
        for c in companies
    }
    by_fb = {
        c["stock_code"]: [
            (ml.get("platform"), ml.get("product_name"))
            for ml in (c.get("marketplace_listings") or [])
        ]
        for c in fb.get("companies", [])
    }
    assert set(by_seed) == set(by_fb)
    for code in by_seed:
        assert sorted(by_seed[code]) == sorted(by_fb[code]), code


def test_reseed_upserts_curated_listings_for_existing_company(db_session):
    """Re-seed must upsert listings (DQC curated) — not only on first insert."""
    from backend.app.models import Company, MarketplaceListing
    from backend.app.seed import load_companies

    company = Company(
        stock_code="DQC",
        name="Công ty Cổ phần Điện Quang",
        vsic_code="2740",
        exchange="HOSE",
        website_url="https://dienquang.com",
        has_ecommerce_site=True,
        digital_channels={"website": True, "shopee": True, "tiktok": False},
    )
    db_session.add(company)
    db_session.commit()
    assert (
        db_session.query(MarketplaceListing)
        .filter(MarketplaceListing.company_id == company.id)
        .count()
        == 0
    )

    load_companies(db_session)
    rows = (
        db_session.query(MarketplaceListing)
        .filter(MarketplaceListing.company_id == company.id)
        .all()
    )
    assert len(rows) >= 2
    assert all(r.source == "seed" for r in rows)
    assert all(r.units_sold_est is None for r in rows)
    assert all(r.revenue_est is None for r in rows)
