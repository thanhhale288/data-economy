"""Tests for ml.shop_matcher — positive / negative pairs at threshold 0.65."""

from __future__ import annotations

import pytest

from ml.shop_matcher import DEFAULT_THRESHOLD, ShopMatcher
from ml.shop_matcher.matcher import labeled_seed_pairs

POSITIVE_PAIRS = [
    ("RAL", "rangdong_official"),
    ("VNM", "vinamilk_official"),
    ("VNM", "@vinamilk"),
    ("FPT", "fpt_official"),
    ("MSN", "masan_consumer"),
    ("PNJ", "pnj_official"),
    ("PNJ", "@pnj"),
    ("DQC", "dienquang_officialstore"),
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
    ("DQC", "rangdong_official"),
    ("VHC", "dienquang_officialstore"),
]

NO_MARKETPLACE_TICKERS = (
    "HPG",
    "GVR",
    "DGC",
    "REE",
    "BMP",
    "VHC",
    "AAA",
    "ANV",
    "IDI",
    "SBT",
    "QNS",
    "HSG",
    "NKG",
    "POM",
    "TLH",
    "GEE",
    "TYA",
    "DPR",
    "CSM",
    "DCM",
    "BFC",
    "CSV",
)

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
    "DQC": "Công ty Cổ phần Điện Quang",
    "VHC": "Công ty Cổ phần Vĩnh Hoàn",
    "AAA": "Công ty Cổ phần Nhựa An Phát Xanh",
}

# Rubber peers — short token "dong" ⊂ rangdong was a known FP; Task #43 hygiene.
RUBBER_PEERS = {
    "DPR": "Công ty Cổ phần Cao su Đồng Phú",
    "CSM": "Công ty Cổ phần Cao su miền Nam",
}


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
    # Brand-aligned handle can score ≥ 0.65 (matcher behaviour). Product linking
    # still requires discover_shops_for_company (flag + QA allowlist) — see gate tests.
    linked = evaluate_discovered_shop(
        company,
        channel_type="shopee",
        url="https://shopee.vn/hoaphat_official",
    )
    assert linked is not None
    assert linked["is_match"] is True
    assert linked["match_source"] == "fuzzy_threshold"
    assert linked["match_confidence"] >= DEFAULT_THRESHOLD


def test_discovery_disabled_by_default(monkeypatch):
    from crawlers.marketplace import shop_finder

    monkeypatch.delenv(shop_finder.DISCOVERY_ENABLED_ENV, raising=False)
    assert shop_finder.is_marketplace_discovery_enabled() is False

    company = type("C", (), {"stock_code": "HPG", "name": COMPANIES["HPG"]})()
    candidates = [
        {
            "ticker": "HPG",
            "channel_type": "shopee",
            "url": "https://shopee.vn/hoaphat_official",
        }
    ]
    assert (
        shop_finder.discover_shops_for_company(
            company, enabled=None, allowlist=candidates
        )
        == []
    )
    assert (
        shop_finder.discover_shops_for_company(
            company, enabled=False, allowlist=candidates
        )
        == []
    )


def test_discovery_enabled_requires_allowlist_and_threshold(monkeypatch):
    from backend.app.models import Company
    from crawlers.marketplace import shop_finder

    monkeypatch.setenv(shop_finder.DISCOVERY_ENABLED_ENV, "1")
    assert shop_finder.is_marketplace_discovery_enabled() is True
    assert shop_finder.marketplace_discovery_threshold() == 0.65

    hpg = Company(
        stock_code="HPG",
        name=COMPANIES["HPG"],
        vsic_code="2410",
        exchange="HOSE",
    )
    ral = Company(
        stock_code="RAL",
        name=COMPANIES["RAL"],
        vsic_code="2740",
        exchange="HOSE",
    )
    # Enabled but ticker not on QA list → still unlinked (no invent)
    assert (
        shop_finder.discover_shops_for_company(
            hpg,
            enabled=True,
            allowlist=[
                {
                    "ticker": "RAL",
                    "channel_type": "shopee",
                    "url": "https://shopee.vn/rangdong_official",
                }
            ],
        )
        == []
    )
    # HPG brand-perfect URL still unlinked without allowlist entry
    assert (
        shop_finder.discover_shops_for_company(
            hpg,
            enabled=True,
            allowlist=[],
        )
        == []
    )
    # QA allowlisted RAL candidate that passes 0.65 → linked with qa_discovery
    linked = shop_finder.discover_shops_for_company(
        ral,
        enabled=True,
        allowlist=[
            {
                "ticker": "RAL",
                "channel_type": "shopee",
                "url": "https://shopee.vn/rangdong_official",
            }
        ],
    )
    assert len(linked) == 1
    assert linked[0]["is_match"] is True
    assert linked[0]["match_source"] == "qa_discovery"
    assert linked[0]["match_confidence"] >= DEFAULT_THRESHOLD

    # Allowlisted but wrong brand for company → below threshold → empty
    assert (
        shop_finder.discover_shops_for_company(
            ral,
            enabled=True,
            allowlist=[
                {
                    "ticker": "RAL",
                    "channel_type": "shopee",
                    "url": "https://shopee.vn/vinamilk_official",
                }
            ],
        )
        == []
    )


def test_gvr_aliases_do_not_contaminate_dpr_csm(matcher: ShopMatcher):
    """GVR marker is specific; DPR/CSM must not inherit gvr ticker handle as a match."""
    assert matcher.is_match(COMPANIES["GVR"], "gvr_official") is True
    assert matcher.is_match(RUBBER_PEERS["DPR"], "gvr_official") is False
    assert matcher.is_match(RUBBER_PEERS["CSM"], "gvr_official") is False


def test_dpr_does_not_match_rangdong_official(matcher: ShopMatcher):
    """Task #43: short token dong ⊂ rangdong must not link DPR to Rạng Đông shop."""
    from ml.shop_matcher.matcher import MIN_TOKEN_CONTAINMENT_LEN

    assert MIN_TOKEN_CONTAINMENT_LEN >= 5
    score = matcher.match_score(RUBBER_PEERS["DPR"], "rangdong_official")
    assert score < DEFAULT_THRESHOLD, f"DPR↔rangdong unexpectedly matched score={score}"
    assert matcher.is_match(RUBBER_PEERS["DPR"], "rangdong_official") is False
    # RAL still matches via brand alias (not token containment alone)
    assert matcher.is_match(COMPANIES["RAL"], "rangdong_official") is True


def test_ral_does_not_match_dongphu_via_short_token(matcher: ShopMatcher):
    """Symmetric hygiene: RAL must not match dongphu via token 'dong'."""
    score = matcher.match_score(COMPANIES["RAL"], "dongphu_official")
    assert score < DEFAULT_THRESHOLD, f"RAL↔dongphu unexpectedly matched score={score}"
    assert matcher.is_match(COMPANIES["RAL"], "dongphu_official") is False


def test_cross_matrix_includes_rubber_peers_after_hygiene(matcher: ShopMatcher):
    """After Task #43 hygiene, DPR/CSM can sit in the precision matrix without FP."""
    shops = [(p["ticker"], p["shop"]) for p in labeled_seed_pairs()]
    pool = {**COMPANIES, **RUBBER_PEERS}
    tp = fp = 0
    for owner, shop in shops:
        for ticker, company in pool.items():
            pred = matcher.is_match(company, shop)
            truth = ticker == owner
            if pred and truth:
                tp += 1
            elif pred and not truth:
                fp += 1
    assert tp >= 5
    assert fp == 0


def test_train_skips_website_aliases_for_no_shop_tickers(tmp_path, monkeypatch):
    """Do not force website-host aliases onto the 22 no-shop tickers."""
    from ml.shop_matcher import matcher as matcher_mod

    monkeypatch.setattr(matcher_mod, "MODEL_PATH", tmp_path / "shop_matcher.joblib")
    m = ShopMatcher()
    m.train()
    # HPG has website but no marketplace shop — no seed_aliases forced
    hpg_key = matcher_mod._normalize_text(COMPANIES["HPG"])
    assert hpg_key not in m._seed_aliases
    # RAL has shop — aliases present
    ral_key = matcher_mod._normalize_text(COMPANIES["RAL"])
    assert ral_key in m._seed_aliases
    assert any("rangdong" in a for a in m._seed_aliases[ral_key])
