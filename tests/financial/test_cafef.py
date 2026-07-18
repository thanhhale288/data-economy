"""CafeF BCTC HTML adapter tests — offline fixture only."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from crawlers.financial.cafef import (
    UNIT_SCALE,
    cafef_bctc_url,
    parse_cafef_bctc_html,
)

FIXTURE = Path(__file__).parent / "fixtures" / "cafef_bmp_bctc.html"


def test_cafef_url_template():
    assert cafef_bctc_url("bmp") == "https://s.cafef.vn/BMP/bao-cao-tai-chinh.chn"


def test_parse_cafef_bmp_fixture_latest_quarter_with_revenue():
    html = FIXTURE.read_text(encoding="utf-8")
    report = parse_cafef_bctc_html(
        html,
        stock_code="BMP",
        source_url="https://s.cafef.vn/BMP/bao-cao-tai-chinh.chn",
    )

    # Q1-2026 doanh thu empty → pick Quý 4-2025
    assert report["period"] == date(2025, 12, 31)
    assert report["report_type"] == "quarterly"
    assert report["stock_code"] == "BMP"
    assert report["source_url"].startswith("https://s.cafef.vn/BMP")

    # CafeF cell 1.306.013.232 × 1000 VND
    assert report["revenue"] == 1_306_013_232 * UNIT_SCALE
    assert report["cost_of_goods"] == 681_649_155 * UNIT_SCALE
    assert report["profit_before_tax"] == 328_132_555 * UNIT_SCALE
    assert report["net_profit"] == 261_343_223 * UNIT_SCALE
    assert report["total_assets"] == 3_378_833_590 * UNIT_SCALE
    assert report["total_equity"] == 2_877_457_822 * UNIT_SCALE
    assert report["current_assets"] == 2_758_363_783 * UNIT_SCALE
    assert report["current_liabilities"] == 483_661_960 * UNIT_SCALE
    assert report["gross_margin"] is not None
    assert 0.4 < report["gross_margin"] < 0.5
    # Not on CafeF summary table
    assert report["employees"] is None
    assert report["rental_cost"] is None


def test_parse_cafef_missing_table_raises():
    import pytest

    with pytest.raises(ValueError, match="KQKD"):
        parse_cafef_bctc_html("<html><body>no table</body></html>", stock_code="BMP")
