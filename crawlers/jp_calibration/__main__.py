"""CLI: NTA frame + gBizINFO silver labels + blind URL-finder eval (Evol-1 T08)."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from crawlers.jp_calibration.evaluate import open_labels_and_score, run_finder
from crawlers.jp_calibration.frame import build_sample
from crawlers.jp_calibration.nta import download_prefecture_zips, extract_csvs, load_nta_frame
from crawlers.jp_calibration.paths import (
    COMPARISON_FILE,
    DEFAULT_PREFECTURES,
    IDENTITY_FILE,
    METRICS_FILE,
    SAMPLE_N,
)
from crawlers.jp_calibration.provenance import write_provenance

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def cmd_download_nta(args: argparse.Namespace) -> int:
    zips = download_prefecture_zips(args.prefectures)
    csvs = extract_csvs(zips)
    frame = load_nta_frame(csvs)
    write_provenance(
        nta_prefs=list(args.prefectures),
        nta_zips=len(zips),
        nta_rows=len(frame),
    )
    print(json.dumps({"zips": len(zips), "csvs": len(csvs), "nta_rows": len(frame)}, ensure_ascii=False))
    return 0 if frame else 2


def cmd_sample(args: argparse.Namespace) -> int:
    manifest = build_sample(n=args.n, seed=args.seed, prefectures=args.prefectures)
    # Labels/identity hashes only — do not clobber NTA zip counts from download-nta.
    write_provenance(nta_prefs=list(args.prefectures), nta_zips=None, nta_rows=None)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"identity -> {IDENTITY_FILE}")
    return 0 if manifest["n"] else 2


def cmd_eval(args: argparse.Namespace) -> int:
    run_finder(allow_llm=args.llm, fetch_pages=not args.no_fetch, limit=args.limit)
    metrics = open_labels_and_score()
    keys = (
        "n",
        "hits",
        "abstain",
        "wrong",
        "hit_rate",
        "precision_among_decided",
        "recall",
        "abstain_rate",
        "hit_rate_wilson95",
        "search_blocked",
        "by_stratum",
    )
    print(json.dumps({k: metrics[k] for k in keys if k in metrics}, ensure_ascii=False, indent=2))
    print(f"metrics -> {METRICS_FILE}")
    print(f"comparison -> {COMPARISON_FILE}")
    return 0


def cmd_score(_: argparse.Namespace) -> int:
    metrics = open_labels_and_score()
    print(json.dumps({k: metrics[k] for k in ("n", "hits", "hit_rate", "abstain_rate")}, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_nta = sub.add_parser("download-nta", help="Download NTA prefecture Unicode CSVs")
    p_nta.add_argument("--prefectures", nargs="+", default=list(DEFAULT_PREFECTURES))
    p_nta.set_defaults(func=cmd_download_nta)

    p_sample = sub.add_parser("sample", help="Search gBizINFO, split labels, write identity_300")
    p_sample.add_argument("--n", type=int, default=SAMPLE_N)
    p_sample.add_argument("--seed", type=int, default=20260825)
    p_sample.add_argument("--prefectures", nargs="+", default=list(DEFAULT_PREFECTURES))
    p_sample.set_defaults(func=cmd_sample)

    p_eval = sub.add_parser("eval", help="Blind-run URL-finder then open silver labels")
    p_eval.add_argument("--llm", action="store_true")
    p_eval.add_argument("--no-fetch", action="store_true")
    p_eval.add_argument("--limit", type=int, default=None, help="Score only the first N identities (smoke)")
    p_eval.set_defaults(func=cmd_eval)

    p_score = sub.add_parser("score", help="Re-open labels on an existing predictions.json")
    p_score.set_defaults(func=cmd_score)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
