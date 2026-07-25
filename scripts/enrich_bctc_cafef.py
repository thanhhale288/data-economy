#!/usr/bin/env python3
"""Batch enrich financial_reports via CafeF for the seed allowlist (~28).

Usage:
  PYTHONPATH=. python scripts/enrich_bctc_cafef.py
  PYTHONPATH=. python scripts/enrich_bctc_cafef.py --tickers RAL,BMP,HPG
  PYTHONPATH=. python scripts/enrich_bctc_cafef.py --dry-run   # fetch only, no DB write
  PYTHONPATH=. python scripts/enrich_bctc_cafef.py --no-fallback

Writes:
  .scratch/epic3-task32-cafef-bctc-report.md
  .scratch/epic3-task32-cafef-bctc-report.csv

Honesty: CafeF missing fields (employees, …) stay null — not filled from seed.
On network/parse fail → status=fallback with detail (or error if no fallback).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tickers",
        default=None,
        help="Comma-separated subset (default: full seed allowlist)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch + report only; do not upsert financial_reports",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Do not use seed/fallback when CafeF fails (status=error)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.4,
        help="Seconds between tickers (default 0.4)",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=None,
        help="Directory for MD/CSV report (default .scratch/)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    from backend.app.database import SessionLocal
    from crawlers.financial.batch_enrich import (
        enrich_allowlist,
        load_allowlist_tickers,
        write_enrich_report,
    )

    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    else:
        tickers = load_allowlist_tickers()

    persist = not args.dry_run
    db = SessionLocal() if persist else None
    try:
        rows = enrich_allowlist(
            db,
            tickers,
            persist=persist,
            use_fallback=not args.no_fallback,
            sleep_s=args.sleep,
        )
        md_path, csv_path = write_enrich_report(
            rows, report_dir=args.report_dir
        )
    finally:
        if db is not None:
            db.close()

    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1

    print(f"Tickers: {len(rows)}  counts={counts}")
    print(f"Report: {md_path}")
    print(f"CSV:    {csv_path}")
    for row in rows:
        print(
            f"  {row.ticker:4} {row.status:10} period={row.period or '-':10} "
            f"persisted={row.persisted} {row.source_url or ''}"
        )

    # Non-zero exit only if everything errored with no usable row
    if rows and all(r.status == "error" for r in rows):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
