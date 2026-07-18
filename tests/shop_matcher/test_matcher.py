"""Tests for ml.shop_matcher — positive / negative pairs at threshold 0.65."""

from __future__ import annotations

import pytest

from ml.shop_matcher import DEFAULT_THRESHOLD, ShopMatcher
from ml.shop_matcher.matcher import labeled_seed_pairs

# Seed legal names (10 DN)
COMPANIES = {
    "RAL": "Công ty Cổ phần Bóng đèn Rạng Đông",
    "HPG": "Tập đoàn Hòa Phát",
    "VNM": "Công ty Cổ phần Sữa Việt Nam",
    "FPT": "Tập đoàn FPT",
    "GVR": "Tập đoàn Công nghiệp Cao su Việt Nam",
    "DGC": "Công ty Cổ phần Hóa chất Đức Giang",
    "MSN": "Tập đoàn Masan",
    "PNJ": "Công ty Cổ phần Vàng bạc Đá quý Phú Nhuận",
    "REE": "Công ty Cổ phần Cơ điện lạnh",
    "BMP": "Công ty Cổ phần Nhựa Bình Minh",
}

POSITIVE_PAIRS = [
    ("RAL", "rangdong_official"),
    ("VNM", "vinamilk_official"),
    ("VNM", "@vinamilk"),
    ("FPT", "fpt_official"),
    ("MSN", "masan_consumer"),
    ("PNJ", "pnj_official"),
    ("PNJ", "@pnj"),
]

# Wrong company ↔ shop (must stay below threshold)
NEGATIVE_PAIRS = [
    ("HPG", "rangdong_official"),
    ("HPG", "vinamilk_official"),
    ("HPG", "fpt_official"),
    ("GVR", "vinamilk_official"),
    ("GVR", "rangdong_official"),
    ("DGC", "masan_consumer"),
    ("DGC", "vinamilk_official"),
    ("REE", "fpt_official"),
    ("REE", "pnj_official"),
    ("BMP", "pnj_official"),
    ("BMP", "masan_consumer"),
    ("MSN", "rangdong_official"),
    ("RAL", "fpt_official"),
    ("VNM", "masan_consumer"),
    ("FPT", "vinamilk_official"),
    ("PNJ", "rangdong_official"),
]

NO_MARKETPLACE_TICKERS = ("HPG", "GVR", "DGC", "REE", "BMP")


@pytest.fixture
def matcher() -> ShopMatcher:
    return ShopMatcher()


def test_default_threshold_is_065():
    assert DEFAULT_THRESHOLD == 0.65
    assert ShopMatcher().threshold == 0.65


@pytest.mark.parametrize("ticker,shop", POSITIVE_PAIRS)
def test_positive_seed_pairs_match(matcher: ShopMatcher, ticker: str, shop: str):
    company = COMPANIES[ticker]
    score = matcher.match_score(company, shop)
    assert score >= DEFAULT_THRESHOLD, f"{ticker}↔{shop} score={score}"
    assert matcher.is_match(company, shop) is True


@pytest.mark.parametrize("ticker,shop", NEGATIVE_PAIRS)
def test_negative_pairs_below_threshold(matcher: ShopMatcher, ticker: str, shop: str):
    company = COMPANIES[ticker]
    score = matcher.match_score(company, shop)
    assert score < DEFAULT_THRESHOLD, f"{ticker}↔{shop} unexpectedly matched score={score}"
    assert matcher.is_match(company, shop) is False


def test_seed_labeled_positives_all_match(matcher: ShopMatcher):
    pairs = labeled_seed_pairs()
    assert len(pairs) >= 5
    for p in pairs:
        assert matcher.is_match(p["company"], p["shop"]), (
            f"seed positive failed: {p['ticker']}↔{p['shop']} "
            f"score={matcher.match_score(p['company'], p['shop'])}"
        )


def test_no_marketplace_tickers_have_no_seed_shops():
    """HPG/GVR/DGC/REE/BMP must not invent seed marketplace links."""
    seed_tickers_with_shops = {p["ticker"] for p in labeled_seed_pairs()}
    for t in NO_MARKETPLACE_TICKERS:
        assert t not in seed_tickers_with_shops


def test_match_dict_api(matcher: ShopMatcher):
    out = matcher.match(COMPANIES["RAL"], "rangdong_official")
    assert out["is_match"] is True
    assert out["score"] >= DEFAULT_THRESHOLD

    out_neg = matcher.match(COMPANIES["HPG"], "rangdong_official")
    assert out_neg["is_match"] is False
    assert out_neg["score"] < DEFAULT_THRESHOLD


def test_empty_inputs_score_zero(matcher: ShopMatcher):
    assert matcher.match_score("", "shop") == 0.0
    assert matcher.match_score("Company", "") == 0.0
    assert matcher.is_match("", "shop") is False


def test_cross_matrix_precision_over_90(matcher: ShopMatcher):
    """All seed shops × 10 DN: precision of predicted matches > 90%."""
    shops = [(p["ticker"], p["shop"]) for p in labeled_seed_pairs()]
    tp = fp = 0
    for owner, shop in shops:
        for ticker, company in COMPANIES.items():
            pred = matcher.is_match(company, shop)
            truth = ticker == owner
            if pred and truth:
                tp += 1
            elif pred and not truth:
                fp += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    assert tp >= 5
    assert fp == 0
    assert precision > 0.90


def test_shop_finder_reexports_matcher():
    from crawlers.marketplace.shop_finder import ShopMatcher as FinderMatcher
    from crawlers.marketplace import ShopMatcher as PkgMatcher

    assert FinderMatcher is ShopMatcher
    assert PkgMatcher is ShopMatcher


def test_evaluate_discovered_shop_gates_on_threshold():
    from backend.app.models import Company
    from crawlers.marketplace.shop_finder import evaluate_discovered_shop

    company = Company(
        stock_code="HPG",
        name=COMPANIES["HPG"],
        vsic_code="2410",
        exchange="HOSE",
    )
    # Wrong shop — must not link
    assert (
        evaluate_discovered_shop(
            company,
            channel_type="shopee",
            url="https://shopee.vn/rangdong_official",
        )
        is None
    )
    # Plausible brand handle for Hòa Phát — would pass fuzzy; gating is caller's
    # responsibility only when discovery finds such a URL (not invented here).
    linked = evaluate_discovered_shop(
        company,
        channel_type="shopee",
        url="https://shopee.vn/hoaphat_official",
    )
    assert linked is not None
    assert linked["is_match"] is True
    assert linked["match_source"] == "fuzzy_threshold"
    assert linked["match_confidence"] >= DEFAULT_THRESHOLD
