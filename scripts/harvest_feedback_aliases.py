#!/usr/bin/env python3
"""Harvest alias/unit-rule proposals from feedback JSONL (Epic 5 Task #79).

Reads training signals (field diffs only) and writes a markdown + optional JSON
report. Does **not** patch ``_LABEL_ALIASES`` in bctc_extract.py, does not call
Prefect, and does not retrain models.

Usage:
  PYTHONPATH=. python scripts/harvest_feedback_aliases.py --help
  PYTHONPATH=. python scripts/harvest_feedback_aliases.py \
      --input tests/benchmark/fixtures/feedback_alias_harvest.jsonl \
      --markdown-out /tmp/feedback-alias-harvest.md \
      --json-out /tmp/feedback-alias-harvest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.app.services.feedback_alias_harvest import (
    DEFAULT_MIN_COUNT,
    MIN_COUNT_ENV,
    default_min_count,
    harvest_from_jsonl,
    write_reports,
)
from backend.app.services.feedback_signal import DEFAULT_STORE_PATH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DEFAULT_STORE_PATH,
        help=f"JSONL store (default: {DEFAULT_STORE_PATH})",
    )
    parser.add_argument(
        "--min-count",
        "-n",
        type=int,
        default=None,
        help=(
            f"Minimum corrections per field to emit a proposal "
            f"(default: env {MIN_COUNT_ENV} or {DEFAULT_MIN_COUNT})"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=None,
        help="Write markdown report to this path (also printed to stdout)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional JSON report path",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print markdown to stdout (still writes --markdown-out / --json-out)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    min_count = args.min_count if args.min_count is not None else default_min_count()
    report = harvest_from_jsonl(args.input, min_count=min_count)
    markdown, payload = write_reports(
        report,
        markdown_path=args.markdown_out,
        json_path=args.json_out,
    )
    if not args.quiet:
        sys.stdout.write(markdown if markdown.endswith("\n") else markdown + "\n")
    if args.quiet and args.json_out is None and args.markdown_out is None:
        sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
