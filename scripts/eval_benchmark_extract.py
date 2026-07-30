"""Run Task #56 extraction golden-set eval and print baseline metrics."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.services.bctc_extract_eval import evaluate_extract_cases, load_golden_cases


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    golden_path = repo_root / "tests" / "benchmark" / "golden" / "extract_golden_cases.json"

    cases = load_golden_cases(golden_path)
    report = evaluate_extract_cases(cases, base_dir=repo_root)

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
