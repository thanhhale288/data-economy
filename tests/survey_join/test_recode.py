"""Google Form Vietnamese headers → locked 18-column survey CSV."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

import pytest

from crawlers.survey_join.join import load_survey_csv
from crawlers.survey_join.paths import SURVEY_COLUMNS
from crawlers.survey_join.recode import (
    RecodeError,
    map_headers,
    recode_bin,
    recode_marketplace_names,
    recode_payment_methods,
    recode_revenue_vnd,
    recode_survey_csv,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def test_recode_google_form_fixture_two_synthetic_rows(tmp_path: Path):
    dest = tmp_path / "locked.csv"
    result = recode_survey_csv(FIXTURES / "google_form_vi.csv", dest)
    assert [row["mst"] for row in result.rows] == ["0000000000", "1111111111"]
    assert result.skipped == []
    assert set(result.header_map) == set(SURVEY_COLUMNS)
    assert list(result.rows[0]) == list(SURVEY_COLUMNS)

    first = result.rows[0]
    assert first["company_name"] == "Fake MST Co"
    assert first["vsic_4digit"] == "1010"
    assert first["ticker"] == ""
    assert first["website_url_self_report"] == "https://fake-mst.example"
    assert first["has_website"] == "true"
    assert first["has_product_catalog"] == "true"
    assert first["has_order_cart"] == "false"
    assert first["payment_methods"] == "vnpay,cod"
    assert first["has_social_links"] == "true"
    assert first["has_marketplace_links"] == "false"
    assert first["marketplace_names"] == ""
    assert first["online_revenue_share_bin"] == "10to25"
    assert first["revenue_vnd"] == "1000000000"
    assert first["revenue_year"] == "2024"

    second = result.rows[1]
    assert second["company_name"] == "Fake Ticker Co"
    assert second["ticker"] == "TEST"
    assert second["has_website"] == "true"
    assert second["has_order_cart"] == "unknown"
    assert second["payment_methods"] == ""
    assert second["has_social_links"] == "false"
    assert second["has_marketplace_links"] == "true"
    assert second["marketplace_names"] == "Shopee,TikTok Shop"
    assert second["online_revenue_share_bin"] == "lt5"
    assert second["revenue_vnd"] == ""
    assert "Timestamp" not in dest.read_text(encoding="utf-8").splitlines()[0]
    assert "Đồng ý" not in dest.read_text(encoding="utf-8")


def test_recode_output_matches_join_survey_columns(tmp_path: Path):
    dest = tmp_path / "locked.csv"
    recode_survey_csv(FIXTURES / "google_form_vi.csv", dest)
    rows = load_survey_csv(dest)
    assert len(rows) == 2
    assert {row["mst"] for row in rows} == {"0000000000", "1111111111"}


def test_recode_idempotent_on_locked_csv(tmp_path: Path):
    first = tmp_path / "once.csv"
    second = tmp_path / "twice.csv"
    recode_survey_csv(FIXTURES / "google_form_vi.csv", first)
    recode_survey_csv(first, second)
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")
    locked = recode_survey_csv(FIXTURES / "survey.csv")
    again = recode_survey_csv(first)
    assert [row["mst"] for row in locked.rows] == ["0000000000", "1111111111", "9999999999"]
    assert again.rows == recode_survey_csv(second).rows


def test_missing_file_errors(tmp_path: Path):
    with pytest.raises(RecodeError, match="not found"):
        recode_survey_csv(tmp_path / "missing.csv")


def test_empty_file_errors(tmp_path: Path):
    empty = tmp_path / "empty.csv"
    empty.write_text("  \n", encoding="utf-8")
    with pytest.raises(RecodeError, match="empty"):
        recode_survey_csv(empty)


def test_no_mappable_mst_header_errors(tmp_path: Path):
    path = tmp_path / "no_mst.csv"
    _write_csv(
        path,
        ["Timestamp", "Tên doanh nghiệp", "Đồng ý"],
        [{"Timestamp": "x", "Tên doanh nghiệp": "Fake", "Đồng ý": "Đồng ý"}],
    )
    with pytest.raises(RecodeError, match="mst"):
        recode_survey_csv(path)


def test_skips_row_missing_has_website(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    path = tmp_path / "skip.csv"
    _write_csv(
        path,
        ["mst", "company_name", "has_website"],
        [
            {"mst": "0000000000", "company_name": "Has flag", "has_website": "Có"},
            {"mst": "1111111111", "company_name": "Missing flag", "has_website": ""},
        ],
    )
    with caplog.at_level(logging.WARNING, logger="crawlers.survey_join.recode"):
        result = recode_survey_csv(path)
    assert [row["mst"] for row in result.rows] == ["0000000000"]
    assert result.skipped == [
        {"row_number": "3", "mst": "1111111111", "recode_error": "missing_has_website"}
    ]
    assert any("recode_error" in rec.message for rec in caplog.records)
    assert any("missing_has_website" in rec.message for rec in caplog.records)


def test_skips_row_unknown_has_website(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    path = tmp_path / "unknown_web.csv"
    _write_csv(
        path,
        ["mst", "has_website"],
        [{"mst": "0000000000", "has_website": "Không biết"}],
    )
    with caplog.at_level(logging.WARNING, logger="crawlers.survey_join.recode"):
        result = recode_survey_csv(path)
    assert result.rows == []
    assert result.skipped[0]["recode_error"] == "invalid_has_website"
    assert "recode_error" in caplog.text


def test_bin_labels_and_passthrough_codes():
    assert recode_bin("0%") == "zero"
    assert recode_bin("Trên 0% đến dưới 5%") == "lt5"
    assert recode_bin("5% đến dưới 10%") == "5to10"
    assert recode_bin("10% đến dưới 25%") == "10to25"
    assert recode_bin("25% đến dưới 50%") == "25to50"
    assert recode_bin("50% trở lên") == "gt50"
    assert recode_bin("Không biết") == "unknown"
    assert recode_bin("Không tiện trả lời") == "refuse"
    for code in ("zero", "lt5", "5to10", "10to25", "25to50", "gt50", "unknown", "refuse"):
        assert recode_bin(code) == code
        assert recode_bin(code.upper()) == code


def test_payment_methods_tokens():
    assert recode_payment_methods("VNPay, COD (thanh toán khi nhận hàng)") == "vnpay,cod"
    assert recode_payment_methods("MoMo") == "momo"
    assert recode_payment_methods("Cổng / cách khác") == "other"
    assert recode_payment_methods("Không nhận thanh toán trên website") == "none"
    assert recode_payment_methods("VNPay, Không nhận thanh toán trên website") == "none"
    assert recode_payment_methods("") == ""
    assert recode_payment_methods("vnpay,momo") == "vnpay,momo"


def test_marketplace_names_kept():
    assert recode_marketplace_names("Shopee, TikTok Shop, Lazada, Khác") == (
        "Shopee,TikTok Shop,Lazada,khác"
    )
    assert recode_marketplace_names("") == ""


def test_mst_strips_spaces_keeps_hyphen_and_leading_zeros(tmp_path: Path):
    path = tmp_path / "mst.csv"
    _write_csv(
        path,
        ["mst", "has_website"],
        [{"mst": " 000 000 0000-001 ", "has_website": "Không"}],
    )
    result = recode_survey_csv(path)
    assert result.rows[0]["mst"] == "0000000000-001"
    assert result.rows[0]["has_website"] == "false"


def test_revenue_vnd_digits_only_empty_on_refuse():
    assert recode_revenue_vnd("1.500.000.000") == "1500000000"
    assert recode_revenue_vnd("Không tiện trả lời") == ""
    assert recode_revenue_vnd("Không biết") == ""
    assert recode_revenue_vnd("") == ""
    assert recode_revenue_vnd("abc") == ""
    assert recode_revenue_vnd("0") == "0"
    assert recode_revenue_vnd("0.0") == "0"


def test_map_headers_drops_timestamp_and_consent():
    mapping = map_headers(
        [
            "Timestamp",
            "Đồng ý",
            "Tên doanh nghiệp",
            "Mã số thuế (giữ hậu tố chi nhánh nếu có)",
        ]
    )
    assert mapping["company_name"] == "Tên doanh nghiệp"
    assert mapping["mst"] == "Mã số thuế (giữ hậu tố chi nhánh nếu có)"
    assert "Timestamp" not in mapping.values()
    assert "Đồng ý" not in mapping.values()


def test_fixture_survey_is_not_real_frame_pilot_rows():
    text = (FIXTURES / "google_form_vi.csv").read_text(encoding="utf-8")
    assert "0101552800" not in text
    assert "masothue" not in text.lower()
    result = recode_survey_csv(FIXTURES / "google_form_vi.csv")
    assert {row["mst"] for row in result.rows} == {"0000000000", "1111111111"}
    assert {row["ticker"] for row in result.rows} <= {"", "TEST"}
