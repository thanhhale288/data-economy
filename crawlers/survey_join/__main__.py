"""CLI: join / recode / plan unmatched. No invented websites or survey rows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from crawlers.survey_join.enrich import cohort_from_self_report, plan_unmatched
from crawlers.survey_join.join import (
    SurveyJoinError,
    join_survey,
    load_cascade_jsonl,
    load_frame_tax_codes,
    load_identity_tax_id_to_ticker,
    load_survey_csv,
)
from crawlers.survey_join.paths import CASCADE_JSONL, FRAME_PILOT_CSV, IDENTITY_28
from crawlers.survey_join.recode import RecodeError, recode_survey_csv

_SUBCOMMANDS = frozenset({"join", "recode", "plan"})


def _add_join_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--survey", required=True, type=Path, help="Locked 18-column survey CSV")
    parser.add_argument("--out", required=True, type=Path, help="Output directory")
    parser.add_argument(
        "--cascade",
        type=Path,
        default=CASCADE_JSONL,
        help="indicators_raw.jsonl",
    )
    parser.add_argument(
        "--frame-pilot",
        type=Path,
        default=FRAME_PILOT_CSV,
        help="frame_pilot.csv for tax_code mapping",
    )
    parser.add_argument(
        "--identity",
        type=Path,
        default=IDENTITY_28,
        help="identity_28.json (MST → listed ticker); missing file is skipped",
    )


def _run_join(args: argparse.Namespace) -> int:
    try:
        result = join_survey(
            survey_path=args.survey,
            out_dir=args.out,
            cascade_path=args.cascade,
            frame_pilot_path=args.frame_pilot,
            identity_path=args.identity,
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


def _run_recode(args: argparse.Namespace) -> int:
    try:
        result = recode_survey_csv(args.src, args.dest)
    except RecodeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    payload = {
        "n_rows": len(result.rows),
        "n_skipped": len(result.skipped),
        "skipped": result.skipped,
        "dest": str(result.dest) if result.dest else None,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if result.dest:
        print(f"locked_csv -> {result.dest}")
    return 0


def _run_plan(args: argparse.Namespace) -> int:
    try:
        survey_rows = load_survey_csv(args.survey)
        cascade_records = load_cascade_jsonl(args.cascade)
    except SurveyJoinError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    frame_tax_codes = load_frame_tax_codes(args.frame_pilot)
    listed_map = load_identity_tax_id_to_ticker(args.identity)
    plan = plan_unmatched(
        survey_rows,
        cascade_records,
        frame_tax_codes=frame_tax_codes,
        listed_tax_to_ticker=listed_map,
    )
    cohort = cohort_from_self_report(plan)
    args.out.mkdir(parents=True, exist_ok=True)
    plan_path = args.out / "unmatched_plan.json"
    cohort_path = args.out / "frame_urls_self_report.json"
    plan_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    cohort_path.write_text(
        json.dumps(cohort, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    counts: dict[str, int] = {}
    for row in plan:
        action = str(row.get("action") or "unknown")
        counts[action] = counts.get(action, 0) + 1
    summary = {
        "n_survey": len(survey_rows),
        "n_unmatched_plan": len(plan),
        "n_self_report_cohort": len(cohort),
        "by_action": counts,
        "unmatched_plan": str(plan_path),
        "frame_urls_self_report": str(cohort_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"unmatched_plan -> {plan_path}")
    print(f"frame_urls_self_report -> {cohort_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Legacy join parser (``--survey --out`` with no subcommand)."""
    parser = argparse.ArgumentParser(
        description=(
            "Join locked survey CSV to extraction-cascade web flags. "
            "Subcommands: join, recode, plan. Bare --survey --out still runs join."
        )
    )
    _add_join_args(parser)
    return parser


def build_subparsers() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Survey glue: recode Google Form CSV, join to cascade, plan unmatched MSTs. "
            "Does not scrape marketplaces or invent websites/financials."
        )
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_join = sub.add_parser("join", help="Join locked survey CSV to cascade flags")
    _add_join_args(p_join)

    p_recode = sub.add_parser("recode", help="Google Form Vietnamese CSV → 18 locked columns")
    p_recode.add_argument("--src", required=True, type=Path, help="Form export CSV")
    p_recode.add_argument("--dest", required=True, type=Path, help="Locked survey CSV")

    p_plan = sub.add_parser(
        "plan",
        help="Write unmatched-MST plan (self-report URL vs needs_url_finder); no fetch",
    )
    _add_join_args(p_plan)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in _SUBCOMMANDS:
        args = build_subparsers().parse_args(argv)
        if args.cmd == "recode":
            return _run_recode(args)
        if args.cmd == "plan":
            return _run_plan(args)
        return _run_join(args)
    args = build_parser().parse_args(argv)
    return _run_join(args)


if __name__ == "__main__":
    raise SystemExit(main())
