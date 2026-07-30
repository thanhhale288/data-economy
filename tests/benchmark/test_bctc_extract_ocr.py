"""Task #53 — OCR path + router for scanned BCTC (optional PaddleOCR)."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.services.bctc_extract import (
    EXTRACT_FIELDS,
    extract_bctc,
    extract_bctc_pdf,
    extract_fields_from_lines,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"

GOLDEN_SAMPLE = {
    "operating_revenue": 5_200_000_000_000.0,
    "profit_before_tax": 420_000_000_000.0,
    "employees": 3200,
    "total_assets": 6_800_000_000_000.0,
    "total_equity": 3_200_000_000_000.0,
}

pytestmark_ocr = pytest.mark.ocr


def test_shared_mapper_from_ocr_like_lines():
    """Mapper reuse without PaddleOCR — same numbers as text-PDF golden."""
    lines = [
        "Bao cao tai chinh mau (synthetic) - don vi: VND",
        "Doanh thu thuan 5.200.000.000.000",
        "Loi nhuan truoc thue 420.000.000.000",
        "So lao dong 3.200",
        "Tong tai san 6.800.000.000.000",
        "Von chu so huu 3.200.000.000.000",
    ]
    result = extract_fields_from_lines(
        lines,
        "\n".join(lines),
        source_type="image_ocr",
        confidence_scale=0.85,
    )
    payload = result.to_dict()
    assert payload["source_type"] == "image_ocr"
    for key, expected in GOLDEN_SAMPLE.items():
        assert payload["fields"][key] == expected, key
        assert 0.0 < payload["confidence"][key] <= 0.85 * 0.9 + 1e-9


def test_router_keeps_digital_text_pdf_as_pdf_text():
    result = extract_bctc(FIXTURES / "sample_bctc_text.pdf")
    payload = result.to_dict()
    assert payload["source_type"] == "pdf_text"
    for key, expected in GOLDEN_SAMPLE.items():
        assert payload["fields"][key] == expected, key


def test_extract_bctc_pdf_still_no_ocr_on_emptyish():
    """Direct text path must not switch to OCR (regression #52)."""
    result = extract_bctc_pdf(FIXTURES / "empty_bctc.pdf")
    assert result.source_type == "pdf_text"
    for key in EXTRACT_FIELDS:
        assert result.fields[key] is None


@pytestmark_ocr
def test_image_ocr_maps_benchmark_fields():
    pytest.importorskip("paddleocr")
    result = extract_bctc(FIXTURES / "sample_bctc_scan.png")
    payload = result.to_dict()
    assert payload["source_type"] == "image_ocr"
    for key, expected in GOLDEN_SAMPLE.items():
        assert payload["fields"][key] == expected, key
        assert payload["confidence"][key] > 0.0


@pytestmark_ocr
def test_scan_pdf_ocr_source_type_and_fields():
    pytest.importorskip("paddleocr")
    result = extract_bctc(FIXTURES / "sample_bctc_scan.pdf")
    payload = result.to_dict()
    assert payload["source_type"] == "pdf_ocr"
    assert "pdf_text_empty" in payload["warnings"] or "pdf_text_sparse" in payload["warnings"]
    for key, expected in GOLDEN_SAMPLE.items():
        assert payload["fields"][key] == expected, key


@pytestmark_ocr
def test_empty_scan_image_nulls_with_warnings():
    pytest.importorskip("paddleocr")
    result = extract_bctc(FIXTURES / "empty_bctc_scan.png")
    payload = result.to_dict()
    assert payload["source_type"] == "image_ocr"
    for key in EXTRACT_FIELDS:
        assert payload["fields"][key] is None
        assert payload["confidence"][key] == 0.0
    assert "no_extractable_fields" in payload["warnings"] or any(
        w.startswith("missing_field:") for w in payload["warnings"]
    )


def test_source_type_distinguishes_text_vs_ocr_contract():
    """Text path always pdf_text; OCR markers only on OCR sources when deps present."""
    text = extract_bctc(FIXTURES / "sample_bctc_text.pdf")
    assert text.source_type == "pdf_text"

    paddleocr = pytest.importorskip("paddleocr")
    assert paddleocr is not None
    image = extract_bctc(FIXTURES / "sample_bctc_scan.png")
    scan_pdf = extract_bctc(FIXTURES / "sample_bctc_scan.pdf")
    assert image.source_type == "image_ocr"
    assert scan_pdf.source_type == "pdf_ocr"
    assert text.source_type != image.source_type
