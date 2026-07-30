"""Small extraction eval helpers for Task #56 baseline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.services.bctc_extract import EXTRACT_FIELDS, extract_bctc


def load_golden_cases(golden_path: str | Path) -> list[dict[str, Any]]:
    """Load golden eval cases from JSON file."""
    raw = json.loads(Path(golden_path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Golden file must be a JSON list of cases.")
    return [dict(case) for case in raw]


def _value_matches(predicted: float | int | None, expected: float | int | None) -> bool:
    if expected is None:
        return predicted is None
    if predicted is None:
        return False
    if isinstance(expected, int) and isinstance(predicted, int):
        return predicted == expected
    exp = float(expected)
    pred = float(predicted)
    tol = max(1e-6, abs(exp) * 1e-6)
    return abs(pred - exp) <= tol


def evaluate_extract_cases(
    cases: list[dict[str, Any]],
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Evaluate extraction against golden set with accuracy and coverage."""
    root = Path(base_dir) if base_dir else Path.cwd()
    total_slots = 0
    expected_present_slots = 0
    predicted_present_slots = 0
    correct_slots = 0
    per_field_stats: dict[str, dict[str, int]] = {
        field: {"total": 0, "expected_present": 0, "predicted_present": 0, "correct": 0}
        for field in EXTRACT_FIELDS
    }
    case_results: list[dict[str, Any]] = []

    for case in cases:
        case_id = str(case.get("id", "unknown"))
        source_rel = case.get("source")
        expected_fields = case.get("expected_fields") or {}
        if not source_rel:
            raise ValueError(f"Golden case '{case_id}' missing source.")
        source = (root / str(source_rel)).resolve()
        if not source.exists():
            raise FileNotFoundError(f"Golden case source not found: {source}")

        result = extract_bctc(source, filename=source.name)
        predicted_fields = result.fields

        case_correct = 0
        case_expected_present = 0
        case_predicted_present = 0
        for field in EXTRACT_FIELDS:
            expected = expected_fields.get(field)
            predicted = predicted_fields.get(field)

            total_slots += 1
            per_field_stats[field]["total"] += 1

            if expected is not None:
                expected_present_slots += 1
                case_expected_present += 1
                per_field_stats[field]["expected_present"] += 1
            if predicted is not None:
                predicted_present_slots += 1
                case_predicted_present += 1
                per_field_stats[field]["predicted_present"] += 1
            if _value_matches(predicted, expected):
                correct_slots += 1
                case_correct += 1
                per_field_stats[field]["correct"] += 1

        case_results.append(
            {
                "id": case_id,
                "source": str(source_rel),
                "source_type": result.source_type,
                "warnings": list(result.warnings),
                "correct": case_correct,
                "total": len(EXTRACT_FIELDS),
                "expected_present": case_expected_present,
                "predicted_present": case_predicted_present,
            }
        )

    per_field_metrics: dict[str, dict[str, float | int]] = {}
    for field, stat in per_field_stats.items():
        present = stat["expected_present"]
        per_field_metrics[field] = {
            **stat,
            "accuracy": stat["correct"] / stat["total"] if stat["total"] else 0.0,
            "coverage": stat["predicted_present"] / present if present else 0.0,
        }

    return {
        "cases": len(cases),
        "fields": list(EXTRACT_FIELDS),
        "overall": {
            "correct": correct_slots,
            "total": total_slots,
            "accuracy": correct_slots / total_slots if total_slots else 0.0,
            "expected_present": expected_present_slots,
            "predicted_present": predicted_present_slots,
            "coverage_against_expected": (
                predicted_present_slots / expected_present_slots if expected_present_slots else 0.0
            ),
            "coverage_all_slots": predicted_present_slots / total_slots if total_slots else 0.0,
        },
        "per_field": per_field_metrics,
        "case_results": case_results,
    }
