"""Task #52 — digital-text PDF → BenchmarkInput field spike."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.services.bctc_extract import (
    EXTRACT_FIELDS,
    _detect_unit_scale,
    extract_bctc_pdf,
    extract_fields_from_lines,
    parse_vn_number,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"

GOLDEN_SAMPLE = {
    "operating_revenue": 5_200_000_000_000.0,
    "profit_before_tax": 420_000_000_000.0,
    "employees": 3200,
    "total_assets": 6_800_000_000_000.0,
    "total_equity": 3_200_000_000_000.0,
}


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("5.200.000.000.000", 5_200_000_000_000.0),
        ("3.200", 3200.0),
        ("1,234,567", 1_234_567.0),
        ("(12.000)", -12_000.0),
        ("-", None),
        ("", None),
    ],
)
def test_parse_vn_number(raw, expected):
    assert parse_vn_number(raw) == expected


def test_sample_text_pdf_maps_benchmark_fields():
    result = extract_bctc_pdf(FIXTURES / "sample_bctc_text.pdf")
    payload = result.to_dict()

    assert payload["source_type"] == "pdf_text"
    for key, expected in GOLDEN_SAMPLE.items():
        assert payload["fields"][key] == expected, key
        assert payload["confidence"][key] >= 0.7
    assert not any(w.startswith("missing_field:") for w in payload["warnings"])


def test_empty_pdf_nulls_and_warnings():
    result = extract_bctc_pdf(FIXTURES / "empty_bctc.pdf")
    payload = result.to_dict()

    assert payload["source_type"] == "pdf_text"
    for key in EXTRACT_FIELDS:
        assert payload["fields"][key] is None
        assert payload["confidence"][key] == 0.0
    assert "no_extractable_fields" in payload["warnings"] or any(
        w.startswith("missing_field:") for w in payload["warnings"]
    )


def test_partial_pdf_does_not_invent_missing_fields():
    result = extract_bctc_pdf(FIXTURES / "partial_bctc.pdf")
    payload = result.to_dict()

    assert payload["fields"]["operating_revenue"] == 1_000_000_000.0
    assert payload["fields"]["profit_before_tax"] is None
    assert payload["fields"]["employees"] is None
    assert payload["fields"]["total_assets"] is None
    assert payload["fields"]["total_equity"] is None
    assert "missing_field:profit_before_tax" in payload["warnings"]
    assert "missing_field:employees" in payload["warnings"]


def test_bytes_input_same_as_path():
    raw = (FIXTURES / "sample_bctc_text.pdf").read_bytes()
    from_bytes = extract_bctc_pdf(raw).fields
    from_path = extract_bctc_pdf(FIXTURES / "sample_bctc_text.pdf").fields
    assert from_bytes == from_path

def test_sample_english_text_pdf_maps_benchmark_fields():
    result = extract_bctc_pdf(FIXTURES / "sample_bctc_text_en.pdf")
    payload = result.to_dict()

    assert payload["source_type"] == "pdf_text"
    for key, expected in GOLDEN_SAMPLE.items():
        assert payload["fields"][key] == expected, key
        assert payload["confidence"][key] >= 0.7
    assert not any(w.startswith("missing_field:") for w in payload["warnings"])
    assert "unit_detected_million_vnd" in payload["warnings"]


@pytest.mark.parametrize(
    "label_line,field_name,raw_expected",
    [
        ("Revenue from sales 1,000,000", "operating_revenue", 1_000_000.0),
        ("Net revenue 2,000,000", "operating_revenue", 2_000_000.0),
        ("Profit before tax 300,000", "profit_before_tax", 300_000.0),
        ("Total assets 9,000,000", "total_assets", 9_000_000.0),
        ("Owners equity 4,000,000", "total_equity", 4_000_000.0),
        ("Total equity 4,500,000", "total_equity", 4_500_000.0),
        ("Number of employees 88", "employees", 88),
        ("Employees 120", "employees", 120),
    ],
)
def test_english_label_aliases_map_whitelist(label_line, field_name, raw_expected):
    result = extract_fields_from_lines([label_line], label_line)
    assert result.fields[field_name] == raw_expected
    for key in EXTRACT_FIELDS:
        if key != field_name:
            assert result.fields[key] is None


def test_english_current_assets_does_not_steal_total_assets():
    lines = ["Total current assets 1,000,000"]
    result = extract_fields_from_lines(lines, "\n".join(lines))
    assert result.fields["total_assets"] is None
    assert "missing_field:total_assets" in result.warnings


@pytest.mark.parametrize(
    "header,scale",
    [
        ("Unit: in millions of VND", 1_000_000),
        ("Unit: in millions of dong", 1_000_000),
        ("Unit: VND million", 1_000_000),
        ("Figures in thousands", 1_000),
        ("in thousands of VND", 1_000),
        ("Don vi: trieu dong", 1_000_000),
        ("Don vi: nghin VND", 1_000),
    ],
)
def test_english_and_vietnamese_unit_phrases(header, scale):
    detected, warning = _detect_unit_scale(header)
    assert detected == scale
    assert warning is not None
