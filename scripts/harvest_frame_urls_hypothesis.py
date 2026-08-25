"""Harvest candidate websites for frame_pilot firms via URL-finder domain hypothesis.

Does not scrape marketplaces. Writes ``data/raw/extraction_cascade/frame_urls.json``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from crawlers.extraction_cascade.cohort import sample_frame_for_url_finder
from crawlers.extraction_cascade.paths import RAW_DIR
from crawlers.url_finder.hypothesis import hypothesize_urls


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--per-division", type=int, default=80)
    p.add_argument("--offset", type=int, default=0, help="Skip first N rows per division")
    p.add_argument("--limit", type=int, default=120, help="Max firms to keep with a URL")
    p.add_argument(
        "--no-resolve",
        action="store_true",
        help="Skip DNS prefilter (faster, noisier).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=RAW_DIR / "frame_urls.json",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    sample = sample_frame_for_url_finder(
        per_division=args.per_division,
        offset=args.offset,
    )
    kept: list[dict] = []
    scanned = 0
    for row in sample:
        scanned += 1
        identity = {
            "legal_name": row.get("company_name") or "",
            "tax_id": row.get("tax_code") or "",
            "address": row.get("address") or "",
        }
        hits = hypothesize_urls(
            identity,
            locale="vi",
            resolve=not args.no_resolve,
            limit=3,
        )
        if not hits:
            continue
        url = hits[0].url
        kept.append(
            {
                "firm_id": str(row.get("tax_code") or ""),
                "tax_code": str(row.get("tax_code") or ""),
                "company_name": str(row.get("company_name") or ""),
                "vsic_4digit": str(row.get("vsic_4digit") or ""),
                "vsic_division": str(row.get("vsic_division") or ""),
                "website_url": url,
                "notes": (
                    "domain_hypothesis_dns" if not args.no_resolve else "domain_hypothesis"
                ),
            }
        )
        if len(kept) >= args.limit:
            break

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(kept, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "written": len(kept),
                "scanned": scanned,
                "resolve": not args.no_resolve,
                "path": str(args.out),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
