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

    assert report["cases"] == 4
    assert report["overall"]["total"] == 20
    assert report["overall"]["expected_present"] == 11
    assert report["overall"]["correct"] == 20
    assert report["overall"]["accuracy"] == 1.0
    assert report["overall"]["coverage_against_expected"] == 1.0
    assert report["overall"]["coverage_all_slots"] == 0.55


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
