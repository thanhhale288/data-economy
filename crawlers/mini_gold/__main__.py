"""CLI: build mini-gold worksheet from T05; eval after human labels."""

from __future__ import annotations

import argparse
import json
import sys

from crawlers.mini_gold.evaluate import evaluate_worksheet, write_eval_artifacts
from crawlers.mini_gold.paths import (
    ERROR_ANALYSIS_MD,
    METRICS_JSON,
    PREDICTIONS_VS_GOLD_CSV,
    WORKSHEET_CSV,
)
from crawlers.mini_gold.worksheet import write_worksheet


def cmd_build(_: argparse.Namespace) -> int:
    meta = write_worksheet()
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"worksheet -> {WORKSHEET_CSV}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    scored, metrics = evaluate_worksheet(require_reviewed=not args.include_unreviewed)
    n = metrics["n_firms_reviewed"]
    if n == 0:
        print(
            "No reviewed rows. Fill gold_* and set reviewed=true "
            f"(≥20 useful, 89 complete) in {WORKSHEET_CSV}, then re-run.",
            file=sys.stderr,
        )
        return 2
    write_eval_artifacts(scored, metrics)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"metrics -> {METRICS_JSON}")
    print(f"error_analysis -> {ERROR_ANALYSIS_MD}")
    print(f"predictions_vs_gold -> {PREDICTIONS_VS_GOLD_CSV}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evol-1 T06 mini gold tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Write worksheet_89.csv from T05 fetch_ok")
    p_build.set_defaults(func=cmd_build)

    p_eval = sub.add_parser("eval", help="Score tier1/tier2 vs reviewed gold labels")
    p_eval.add_argument(
        "--include-unreviewed",
        action="store_true",
        help="Score all rows even if reviewed!=true (debug only)",
    )
    p_eval.set_defaults(func=cmd_eval)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
