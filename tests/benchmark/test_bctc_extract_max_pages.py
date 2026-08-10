"""MAX_BCTC_PAGES cap for text + OCR PDF paths."""

from __future__ import annotations

import io

import pypdfium2 as pdfium

from backend.app.services.bctc_extract import (
    MAX_BCTC_PAGES,
    _pages_capped_warning,
    extract_bctc_pdf,
)
from backend.app.services.bctc_extract_ocr import pdf_bytes_to_images


def _blank_pdf_bytes(n_pages: int) -> bytes:
    """Build a blank multi-page PDF with pypdfium2 (already a project dep)."""
    doc = pdfium.PdfDocument.new()
    try:
        for _ in range(n_pages):
            doc.new_page(200, 200)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()
    finally:
        doc.close()


def test_max_bctc_pages_constant():
    assert MAX_BCTC_PAGES == 15


def test_pages_capped_warning():
    assert _pages_capped_warning(15) is None
    assert _pages_capped_warning(16) == "pages_capped:15"


def test_pdf_bytes_to_images_caps_at_max_pages():
    raw = _blank_pdf_bytes(MAX_BCTC_PAGES + 3)
    images, total = pdf_bytes_to_images(raw)
    assert total == MAX_BCTC_PAGES + 3
    assert len(images) == MAX_BCTC_PAGES


def test_extract_bctc_pdf_warns_when_capped():
    raw = _blank_pdf_bytes(MAX_BCTC_PAGES + 2)
    result = extract_bctc_pdf(raw)
    assert "pages_capped:15" in result.warnings
