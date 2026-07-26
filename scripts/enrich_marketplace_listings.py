#!/usr/bin/env python3
"""Listing depth smoke + report for the seed allowlist (Epic 3 Task #34/#35).

Usage:
  PYTHONPATH=. python scripts/enrich_marketplace_listings.py
  PYTHONPATH=. python scripts/enrich_marketplace_listings.py --no-live
  PYTHONPATH=. python scripts/enrich_marketplace_listings.py --prefer-cache
  PYTHONPATH=. python scripts/enrich_marketplace_listings.py --tickers DQC,RAL,HPG
  PYTHONPATH=. python scripts/enrich_marketplace_listings.py --playwright

Writes:
  .scratch/epic3-task34-listing-depth.md
  .scratch/epic3-task34-listing-depth.csv

Honesty:
  - Live ok → listings tagged source=live (report only unless --persist-db).
  - Live blocked/error → allowlisted live cache (Task #35) then seed/fallback;
    never invent units/GMV.
  - B2B peers without shop stay empty.
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
        "--no-live",
        action="store_true",
        help="Skip live scrape and cache; report seed coverage only",
    )
    parser.add_argument(
        "--prefer-cache",
        action="store_true",
        help="Task #35: try allowlisted live-cache before HTTP (demo-stable)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable allowlisted live-cache fallback after HTTP fail",
    )
    parser.add_argument(
        "--playwright",
        action="store_true",
        help="Allow Playwright follow-up on Shopee HTML (still no invent on fail)",
    )
    parser.add_argument(
        "--persist-db",
        action="store_true",
        help="Upsert listings via run_marketplace_crawl (live→cache→seed→fallback)",
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

    from crawlers.marketplace.listing_depth import (
        assert_seed_file_readable,
        before_counts_from_prior_snapshot,
        smoke_live_listing_depth,
        summarize_coverage,
        write_listing_depth_report,
    )

    assert_seed_file_readable()
    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    rows = smoke_live_listing_depth(
        tickers=tickers,
        use_playwright=args.playwright,
        attempt_live=not args.no_live,
        prefer_cache=args.prefer_cache,
        use_cache_on_fail=not args.no_cache,
    )
    md_path, csv_path = write_listing_depth_report(
        rows,
        report_dir=args.report_dir,
        before=before_counts_from_prior_snapshot(),
    )
    summary = summarize_coverage(rows)
    print(
        f"Tickers={summary['tickers']} with_shop={summary['with_shop']} "
        f"with_listing={summary['with_listing']} with_gmv={summary['with_gmv_listing']} "
        f"live_ok={summary['live_ok']}"
    )
    print(f"Report: {md_path}")
    print(f"CSV:    {csv_path}")

    if args.persist_db:
        from backend.app.database import SessionLocal
        from crawlers.marketplace.shop_finder import run_marketplace_crawl

        db = SessionLocal()
        try:
            n = run_marketplace_crawl(db, attempt_live=not args.no_live)
            print(f"Persisted marketplace upserts: {n}")
        finally:
            db.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
