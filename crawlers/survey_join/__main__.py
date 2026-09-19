"""CLI: PYTHONPATH=. python3 -m crawlers.survey_join --survey path.csv --out dir"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from crawlers.survey_join.join import SurveyJoinError, join_survey
from crawlers.survey_join.paths import CASCADE_JSONL, FRAME_PILOT_CSV


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Join survey CSV to extraction-cascade web flags and estimate "
            "online revenue (DT × bin midpoint) only when revenue_vnd is present. "
            "Does not scrape, does not invent websites or seed financials."
        )
    )
    parser.add_argument("--survey", required=True, type=Path, help="Survey CSV path")
    parser.add_argument("--out", required=True, type=Path, help="Output directory")
    parser.add_argument(
        "--cascade",
        type=Path,
        default=CASCADE_JSONL,
        help="indicators_raw.jsonl (default: data/processed/extraction_cascade/)",
    )
    parser.add_argument(
        "--frame-pilot",
        type=Path,
        default=FRAME_PILOT_CSV,
        help="frame_pilot.csv for tax_code mapping (default: data/raw/frame_pilot/)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = join_survey(
            survey_path=args.survey,
            out_dir=args.out,
            cascade_path=args.cascade,
            frame_pilot_path=args.frame_pilot,
        )
    except SurveyJoinError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    summary = result["summary"]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    paths = result["paths"]
    print(f"joined_csv -> {paths['joined_csv']}")
    print(f"joined_jsonl -> {paths['joined_jsonl']}")
    print(f"summary -> {paths['summary_json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
