"""Midpoint estimate: only survey revenue × bin. Never seed financials."""

from __future__ import annotations

from crawlers.survey_join.estimate import (
    BIN_MIDPOINTS,
    GT50_CAVEAT,
    estimate_online_revenue,
)


def test_midpoints_when_revenue_positive():
    est = estimate_online_revenue(revenue_vnd=1_000_000_000, online_revenue_share_bin="10to25")
    assert est.skipped_reason is None
    assert est.midpoint == BIN_MIDPOINTS["10to25"] == 0.175
    assert est.estimated_online_revenue == 175_000_000
    assert est.caveat is None


def test_zero_bin_is_zero_not_skip():
    est = estimate_online_revenue(revenue_vnd="1000", online_revenue_share_bin="zero")
    assert est.estimated_online_revenue == 0.0
    assert est.skipped_reason is None


def test_gt50_records_wide_bin_caveat():
    est = estimate_online_revenue(revenue_vnd=200, online_revenue_share_bin="gt50")
    assert est.estimated_online_revenue == 150.0
    assert est.caveat == GT50_CAVEAT


def test_skip_when_revenue_missing():
    est = estimate_online_revenue(revenue_vnd="", online_revenue_share_bin="lt5")
    assert est.estimated_online_revenue is None
    assert est.skipped_reason == "missing_revenue"


def test_skip_when_revenue_not_positive():
    est = estimate_online_revenue(revenue_vnd="0", online_revenue_share_bin="lt5")
    assert est.estimated_online_revenue is None
    assert est.skipped_reason == "non_positive_revenue"


def test_skip_unknown_and_refuse_even_with_revenue():
    unknown = estimate_online_revenue(revenue_vnd=5000, online_revenue_share_bin="unknown")
    refuse = estimate_online_revenue(revenue_vnd=5000, online_revenue_share_bin="refuse")
    assert unknown.estimated_online_revenue is None
    assert unknown.skipped_reason == "bin_unknown"
    assert refuse.estimated_online_revenue is None
    assert refuse.skipped_reason == "bin_refuse"


def test_invalid_bin_skips():
    est = estimate_online_revenue(revenue_vnd=10, online_revenue_share_bin="almost_half")
    assert est.estimated_online_revenue is None
    assert est.skipped_reason == "invalid_bin"


def test_estimate_has_no_file_io():
    """Midpoints come from the survey cells, not CafeF/seed/GSO files."""
    from pathlib import Path

    import crawlers.survey_join.estimate as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "open(" not in source
    assert "companies.json" not in source
    assert "Path(" not in source
