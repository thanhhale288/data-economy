#!/usr/bin/env python3
"""Onboard a listed manufacturing company into the seed allowlist + DB.

Usage:
  PYTHONPATH=. python scripts/onboard_company.py \\
    --code XYZ --name "Công ty ..." --vsic 2410 \\
    --website https://example.com [--exchange HOSE] [--enrich]

Does not invent marketplace listings or industry-ratio online revenue.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_FILE = ROOT / "data" / "seeds" / "companies.json"
MAPPING_FILE = ROOT / "data" / "mappings" / "vsic_isic_section_c.json"


def _load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_seed(rows: list[dict]) -> None:
    SEED_FILE.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _ensure_vsic(vsic_code: str) -> None:
    mappings = _load_json(MAPPING_FILE)
    codes = {m["vsic_code"] for m in mappings}
    if vsic_code not in codes:
        raise SystemExit(
            f"VSIC {vsic_code} chưa có trong {MAPPING_FILE.name}. "
            "Thêm mã level-4 (và parent division) rồi chạy lại seed mappings."
        )


def append_seed_row(
    *,
    code: str,
    name: str,
    vsic: str,
    website: str | None,
    exchange: str,
    description: str | None,
) -> dict:
    rows = _load_json(SEED_FILE)
    code = code.upper().strip()
    for row in rows:
        if str(row.get("stock_code", "")).upper() == code:
            print(f"Seed already has {code} — skipping JSON append.")
            return row

    presence = []
    if website:
        presence.append(
            {
                "channel_type": "website",
                "url": website,
                "has_checkout": False,
                "match_confidence": 1.0,
            }
        )
    row = {
        "stock_code": code,
        "name": name,
        "vsic_code": vsic,
        "exchange": exchange,
        "website_url": website,
        "has_ecommerce_site": False,
        "description": description
        or f"Onboarded listed manufacturer ({code}, VSIC {vsic}).",
        "digital_channels": {
            "website": bool(website),
            "shopee": False,
            "tiktok": False,
        },
        "financial": None,
        "digital_presence": presence,
        "marketplace_listings": [],
    }
    rows.append(row)
    _save_seed(rows)
    print(f"Appended {code} to {SEED_FILE.relative_to(ROOT)}")
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--vsic", required=True)
    parser.add_argument("--website", default=None)
    parser.add_argument("--exchange", default="HOSE")
    parser.add_argument("--description", default=None)
    parser.add_argument("--enrich", action="store_true")
    parser.add_argument("--seed-only", action="store_true")
    args = parser.parse_args(argv)

    _ensure_vsic(args.vsic.strip())
    row = append_seed_row(
        code=args.code,
        name=args.name,
        vsic=args.vsic.strip(),
        website=args.website,
        exchange=args.exchange,
        description=args.description,
    )

    sys.path.insert(0, str(ROOT))
    from crawlers.companies.listed_companies import (
        enrich_company,
        refresh_allowed_tickers,
        upsert_company_metadata,
    )

    tickers = refresh_allowed_tickers()
    print(f"Allowlist size: {len(tickers)}")

    if args.seed_only:
        return 0

    from backend.app.database import SessionLocal
    from backend.app.seed import load_vsic_mappings

    db = SessionLocal()
    try:
        load_vsic_mappings(db)
        if args.enrich:
            enrich_company(db, row)
            print(f"Enriched {row['stock_code']}.")
        else:
            upsert_company_metadata(db, row)
            print(f"Upserted {row['stock_code']} metadata.")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
