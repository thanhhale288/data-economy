"""Task #56 — extraction eval baseline + honesty guardrails."""

from __future__ import annotations

from pathlib import Path

from backend.app.services.bctc_extract import extract_fields_from_lines
from backend.app.services.bctc_extract_eval import evaluate_extract_cases, load_golden_cases

GOLDEN_PATH = Path(__file__).resolve().parent / "golden" / "extract_golden_cases.json"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_eval_baseline_metrics_from_golden_set():
    cases = load_golden_cases(GOLDEN_PATH)
    report = evaluate_extract_cases(cases, base_dir=REPO_ROOT)

    # Task #70 expanded the synthetic golden set (4 → 9). Accuracy 1.0 here
    # means expected_fields match honest extract output — including nulls for
    # missing labels — not that every real BCTC would extract perfectly.
    assert report["cases"] >= 6
    assert report["cases"] == 9
    assert report["overall"]["total"] == 45
    assert report["overall"]["expected_present"] == 33
    assert report["overall"]["correct"] == 45
    assert report["overall"]["accuracy"] == 1.0
    assert report["overall"]["coverage_against_expected"] == 1.0
    assert report["overall"]["coverage_all_slots"] == 33 / 45


def test_golden_includes_task70_synthetic_case_ids():
    cases = load_golden_cases(GOLDEN_PATH)
    ids = {c["id"] for c in cases}
    assert {"hose_like_trieu", "en_sales_layout", "partial_revenue_assets",
            "hose_notes_noise", "hose_nghin_dong"} <= ids
    for case in cases:
        source = REPO_ROOT / case["source"]
        assert source.is_file(), case["id"]


def test_confidence_threshold_guardrail_nulls_low_confidence_field():
    lines = ["Doanh thu thuan 12"]
    result = extract_fields_from_lines(
        lines,
        "\n".join(lines),
        source_type="pdf_text",
        confidence_scale=1.0,
        confidence_threshold=0.75,
    )

    assert result.confidence["operating_revenue"] == 0.7
    assert result.fields["operating_revenue"] is None
    assert any(w.startswith("low_confidence_field:operating_revenue") for w in result.warnings)
