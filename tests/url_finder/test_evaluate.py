import json

import pytest

from crawlers.url_finder.decide import decide_rules
from crawlers.url_finder.evaluate import classify_error, summarize, wilson_interval
from crawlers.url_finder.evidence import ScoredCandidate
from crawlers.url_finder.identity import assert_no_url_fields, load_identity


def _cand(url: str, score: float, **kwargs) -> ScoredCandidate:
    return ScoredCandidate(
        url=url,
        title="",
        snippet="",
        score=score,
        domain=url.split("/")[2],
        final_url=url,
        **kwargs,
    )


def test_abstain_when_margin_thin():
    decision = decide_rules(
        [
            _cand("https://alpha.example", 5.0),
            _cand("https://beta.example", 4.8),
        ]
    )
    assert decision.abstain is True
    assert "thin_margin" in decision.reason


def test_ticker_breaks_score_tie():
    decision = decide_rules(
        [
            _cand("https://fptcorp.com.vn", 8.5, fetch_ok=True),
            _cand("https://fpt.com.vn", 8.5, fetch_ok=True),
        ],
        identity={"ticker": "FPT"},
    )
    assert decision.abstain is False
    assert decision.domain == "fpt.com.vn"
    assert "ticker_breaks_tie" in decision.reason


def test_collapse_redirect_twins(tmp_path):
    from crawlers.url_finder.pipeline import collapse_scored_by_domain

    twins = [
        _cand("https://a.example", 8.5, fetch_ok=True),
        _cand("https://b.example", 8.5, fetch_ok=True),
    ]
    # Force same registrable domain (redirect twins).
    twins[0].domain = "binhdien.com"
    twins[1].domain = "binhdien.com"
    twins[1].score = 8.0
    collapsed = collapse_scored_by_domain(twins)
    assert len(collapsed) == 1
    assert collapsed[0].score == 8.5


def test_fptshop_is_related_wrong():
    assert classify_error("https://fptshop.com.vn", "https://fpt.com.vn", False) == (
        "wrong_related_domain"
    )


def test_wilson_interval_bounded():
    low, high = wilson_interval(24, 28)
    assert 0.0 <= low <= 24 / 28 <= high <= 1.0
    assert high - low > 0.05  # n=28 stays wide


def test_summarize_separates_abstain():
    rows = [
        {"hit": True, "error_type": "hit"},
        {"hit": False, "error_type": "abstain"},
        {"hit": False, "error_type": "wrong_other"},
    ]
    metrics = summarize(rows)
    assert metrics["n"] == 3
    assert metrics["hits"] == 1
    assert metrics["abstain"] == 1
    assert metrics["precision_among_decided"] == 0.5
    assert metrics["recall"] == pytest.approx(1 / 3, abs=1e-3)


def test_identity_rejects_url_fields(tmp_path):
    path = tmp_path / "identity.json"
    path.write_text(
        json.dumps(
            [
                {
                    "ticker": "RAL",
                    "legal_name": "Rạng Đông",
                    "tax_id": "0101526991",
                    "website_url": "https://rangdong.com.vn",
                }
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must not contain URL"):
        load_identity(path)


def test_assert_no_url_fields_ok():
    assert_no_url_fields(
        {"ticker": "RAL", "legal_name": "X", "tax_id": "0101526991"},
        context="test",
    )
