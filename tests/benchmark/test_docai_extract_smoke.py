"""Epic 5 Task #68 — repeatable DocAI extract smoke (upload → extract → confirm).

Hits ``POST /api/benchmark/extract`` with FastAPI TestClient. Confirm-before-compare
is a frontend gate (``requireConfirm`` / checkbox in ``Benchmark.jsx``); this module
does not run compare and does not invent GSO/OECD/CafeF numbers.

Playwright is not in this task: default CI is ``pytest -q`` with no marker filter, and
existing ``tests/e2e/`` API TestClient tests must keep running. Browser UI remain a
manual checklist in ``docs/ops-demo.md``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.main import app
from backend.app.services.bctc_extract import EXTRACT_FIELDS

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FRONTEND_BENCHMARK = (
    Path(__file__).resolve().parents[2] / "frontend" / "src" / "pages" / "Benchmark.jsx"
)

GOLDEN_SAMPLE = {
    "operating_revenue": 5_200_000_000_000.0,
    "profit_before_tax": 420_000_000_000.0,
    "employees": 3200,
    "total_assets": 6_800_000_000_000.0,
    "total_equity": 3_200_000_000_000.0,
}

CONFIRM_LABEL = "Tôi đã kiểm tra/chỉnh sửa dữ liệu prefill từ file trước khi so sánh"
SUBMIT_LABEL = "So sánh benchmark"


def _client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _fields_empty(fields: dict) -> bool:
    return all(fields.get(key) is None for key in EXTRACT_FIELDS)


def test_text_pdf_extract_smoke_populates_fields(db_session):
    """Documented smoke: selectable-text PDF goes through extract with honest fields."""
    client = _client(db_session)
    try:
        with (FIXTURES / "sample_bctc_text.pdf").open("rb") as f:
            res = client.post(
                "/api/benchmark/extract",
                files={"file": ("sample_bctc_text.pdf", f, "application/pdf")},
            )
        assert res.status_code == 200
        body = res.json()
        assert set(body.keys()) == {"fields", "confidence", "warnings", "source_type"}
        assert body["source_type"] == "pdf_text"
        assert "ocr_unavailable" not in body["warnings"]
        for key, expected in GOLDEN_SAMPLE.items():
            assert body["fields"][key] == expected, key
            assert body["confidence"][key] > 0.0, key
        assert not any(w.startswith("missing_field:") for w in body["warnings"])
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "filename, content_type, expected_source",
    [
        ("sample_bctc_scan.png", "image/png", "image_ocr"),
        ("sample_bctc_scan.pdf", "application/pdf", "pdf_ocr"),
    ],
)
def test_scan_extract_honesty_without_requiring_ocr(
    db_session, filename, content_type, expected_source
):
    """Scan path must stay honest when PaddleOCR is missing (null fields + warning)."""
    client = _client(db_session)
    try:
        with (FIXTURES / filename).open("rb") as f:
            res = client.post(
                "/api/benchmark/extract",
                files={"file": (filename, f, content_type)},
            )
        assert res.status_code == 200
        body = res.json()
        assert body["source_type"] == expected_source
        warnings = body["warnings"]
        fields = body["fields"]

        if "ocr_unavailable" in warnings:
            assert _fields_empty(fields)
            assert all(body["confidence"].get(key) == 0.0 for key in EXTRACT_FIELDS)
            return

        # OCR extra present: still no invented empty payload. Golden match is the
        # optional @ocr extra below — default CI must not require PaddleOCR.
        assert isinstance(warnings, list)
        assert set(fields) >= set(EXTRACT_FIELDS)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.ocr
def test_scan_png_ocr_extra_maps_fields_when_paddleocr_installed(db_session):
    """Optional OCR extra — skipped via importorskip when PaddleOCR is absent."""
    pytest.importorskip("paddleocr")
    client = _client(db_session)
    try:
        with (FIXTURES / "sample_bctc_scan.png").open("rb") as f:
            res = client.post(
                "/api/benchmark/extract",
                files={"file": ("sample_bctc_scan.png", f, "image/png")},
            )
        assert res.status_code == 200
        body = res.json()
        assert body["source_type"] == "image_ocr"
        assert "ocr_unavailable" not in body["warnings"]
        for key, expected in GOLDEN_SAMPLE.items():
            assert body["fields"][key] == expected, key
            assert body["confidence"][key] > 0.0, key
    finally:
        app.dependency_overrides.clear()


def test_confirm_before_compare_is_frontend_gate():
    """Extract does not compare; Benchmark.jsx locks submit until the confirm checkbox.

    Task #81 owns ``Benchmark.jsx`` — this smoke only documents the existing gate
    (``requireConfirm`` / ``#benchmark-upload-input`` / submit label).
    """
    src = FRONTEND_BENCHMARK.read_text(encoding="utf-8")
    assert 'id="benchmark-upload-input"' in src
    assert "requireConfirm" in src
    assert "compareLockedByConfirm" in src
    assert CONFIRM_LABEL in src
    assert SUBMIT_LABEL in src
    assert "disabled={loading || compareLockedByConfirm}" in src
