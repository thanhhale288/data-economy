"""Task #52 — digital-text PDF → BenchmarkInput field spike."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.services.bctc_extract import (
    EXTRACT_FIELDS,
    extract_bctc_pdf,
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
