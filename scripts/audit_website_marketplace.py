#!/usr/bin/env python3
"""Batch website detector + marketplace URL audit for the seed allowlist (~28).

Usage:
  PYTHONPATH=. python scripts/audit_website_marketplace.py
  PYTHONPATH=. python scripts/audit_website_marketplace.py --tickers RAL,DQC,MSN
  PYTHONPATH=. python scripts/audit_website_marketplace.py --no-db        # seed only
  PYTHONPATH=. python scripts/audit_website_marketplace.py --no-detect    # offline
  PYTHONPATH=. python scripts/audit_website_marketplace.py --fix-db       # sync DB URLs

Writes:
  .scratch/epic3-task33-website-url-audit.md
  .scratch/epic3-task33-website-url-audit.csv

Honesty: HTTP 403/timeout/block → website_ok=false and has_checkout stays
`unknown`; checkout is never written to the DB from a failed fetch.

Exit code 3 when a flag/URL mismatch remains (marketplace flag without URL).
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
        "--no-detect",
        action="store_true",
        help="Skip live website detection (website_ok/has_checkout stay unknown)",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Audit seed only; do not open a DB session",
    )
    parser.add_argument(
        "--fix-db",
        action="store_true",
        help="Sync DB digital_presence URLs to seed where they drifted",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.4,
        help="Seconds between website fetches (default 0.4)",
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

    from crawlers.companies.website_audit import (
        audit_allowlist,
        summarize,
        write_audit_report,
    )

    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    use_db = not args.no_db
    db = None
    if use_db:
        from backend.app.database import SessionLocal

        db = SessionLocal()
    try:
        rows = audit_allowlist(
            db,
            tickers,
            detect_enabled=not args.no_detect,
            fix_db=args.fix_db,
            sleep_s=args.sleep,
        )
        md_path, csv_path = write_audit_report(rows, report_dir=args.report_dir)
    finally:
        if db is not None:
            db.close()

    counts = summarize(rows)
    print(f"Tickers: {counts['tickers']}  counts={counts}")
    print(f"Report: {md_path}")
    print(f"CSV:    {csv_path}")
    for row in rows:
        checkout = "unknown" if row.has_checkout is None else str(row.has_checkout)
        print(
            f"  {row.stock_code:4} website_ok={str(row.website_ok):7} "
            f"checkout={checkout:7} mismatch={row.flag_vs_url_mismatch or '-':24} "
            f"db={row.db_mismatch or '-':24} {row.detect_detail}"
        )

    mismatched = [r.stock_code for r in rows if r.flag_vs_url_mismatch]
    if mismatched:
        print(f"FLAG/URL MISMATCH: {', '.join(mismatched)}")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
