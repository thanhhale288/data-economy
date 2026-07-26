"""Listing depth helpers — count coverage, live smoke, report (Epic 3 Task #34).

Honesty: only live scrape (`source=live`) or curated seed with PROVENANCE
may add listings. Never invent `units_sold_est` / `revenue_est` for B2B peers.
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crawlers.marketplace.common import (
    MARKETPLACE_CHANNELS,
    SEED_FILE,
    annotate_provenance,
    load_seed_companies,
    normalize_listing_source,
)
from crawlers.marketplace.shopee import fetch_shopee_listings
from crawlers.marketplace.tiktok import fetch_tiktok_listings

logger = logging.getLogger(__name__)

SCRATCH_DIR = Path(__file__).resolve().parents[2] / ".scratch"
DEFAULT_REPORT_STEM = "epic3-task34-listing-depth"


@dataclass
class TickerListingRow:
    stock_code: str
    has_shop: bool
    shop_urls: list[str] = field(default_factory=list)
    n_seed_listings: int = 0
    n_gmv_listings: int = 0  # price + units both present
    seed_sources: list[str] = field(default_factory=list)
    live_status: str = "skipped"  # ok | blocked | error | empty | skipped | no_shop
    live_detail: str = ""
    n_live_listings: int = 0


def _shop_urls(company: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for dp in company.get("digital_presence") or []:
        channel = dp.get("channel_type")
        url = dp.get("url")
        if channel in MARKETPLACE_CHANNELS and url:
            out.append((str(channel), str(url)))
    return out


def _gmv_count(listings: list[dict[str, Any]]) -> int:
    n = 0
    for ml in listings:
        if ml.get("price") is not None and ml.get("units_sold_est") is not None:
            n += 1
    return n


def seed_listing_coverage(
    companies: list[dict[str, Any]] | None = None,
) -> list[TickerListingRow]:
    """Summarize seed allowlist: shop URLs vs listings vs GMV-capable rows."""
    rows: list[TickerListingRow] = []
    for company in companies or load_seed_companies():
        code = company["stock_code"]
        shops = _shop_urls(company)
        listings = list(company.get("marketplace_listings") or [])
        sources = sorted(
            {
                normalize_listing_source(ml.get("source") or "seed")
                for ml in listings
            }
        )
        rows.append(
            TickerListingRow(
                stock_code=code,
                has_shop=bool(shops),
                shop_urls=[u for _, u in shops],
                n_seed_listings=len(listings),
                n_gmv_listings=_gmv_count(listings),
                seed_sources=sources,
                live_status="skipped",
            )
        )
    return rows


def attempt_live_for_shops(
    shops: list[tuple[str, str]],
    *,
    use_playwright: bool = False,
) -> tuple[str, str, list[dict[str, Any]]]:
    """Try live scrape for shop URLs. Returns (status, detail, listings)."""
    if not shops:
        return "no_shop", "no marketplace shop URL", []

    collected: list[dict[str, Any]] = []
    details: list[str] = []
    worst = "empty"

    for channel, url in shops:
        if channel == "shopee":
            result = fetch_shopee_listings(url, use_playwright=use_playwright)
        elif channel == "tiktok":
            result = fetch_tiktok_listings(url)
        else:
            details.append(f"{channel}:not_implemented")
            continue

        details.append(f"{channel}:{result.status}:{result.detail}")
        if result.status == "ok" and result.listings:
            collected.extend(annotate_provenance(result.listings, "live"))
            worst = "ok"
        elif result.status in {"blocked", "error"} and worst != "ok":
            worst = result.status
        elif worst not in {"ok", "blocked", "error"}:
            worst = result.status or "empty"

    detail = "; ".join(details) if details else "no fetch attempted"
    return worst, detail, collected


def smoke_live_listing_depth(
    *,
    tickers: list[str] | None = None,
    use_playwright: bool = False,
    attempt_live: bool = True,
) -> list[TickerListingRow]:
    """Seed coverage + optional live smoke for tickers that have shop URLs."""
    companies = load_seed_companies()
    if tickers:
        want = {t.upper() for t in tickers}
        companies = [c for c in companies if c["stock_code"] in want]

    rows = seed_listing_coverage(companies)
    if not attempt_live:
        return rows

    by_code = {c["stock_code"]: c for c in companies}
    for row in rows:
        company = by_code[row.stock_code]
        shops = _shop_urls(company)
        if not shops:
            row.live_status = "no_shop"
            row.live_detail = "B2B / no marketplace shop — keep listings empty"
            continue
        status, detail, live_listings = attempt_live_for_shops(
            shops, use_playwright=use_playwright
        )
        row.live_status = status
        row.live_detail = detail
        row.n_live_listings = len(live_listings)
    return rows


def summarize_coverage(rows: list[TickerListingRow]) -> dict[str, Any]:
    listed = [r for r in rows if r.n_seed_listings > 0]
    gmv = [r for r in rows if r.n_gmv_listings > 0]
    shops = [r for r in rows if r.has_shop]
    live_ok = [r for r in rows if r.live_status == "ok" and r.n_live_listings > 0]
    return {
        "tickers": len(rows),
        "with_shop": len(shops),
        "with_listing": len(listed),
        "with_gmv_listing": len(gmv),
        "live_ok": len(live_ok),
        "shop_tickers": [r.stock_code for r in shops],
        "listing_tickers": [r.stock_code for r in listed],
        "gmv_tickers": [r.stock_code for r in gmv],
        "live_ok_tickers": [r.stock_code for r in live_ok],
    }


def write_listing_depth_report(
    rows: list[TickerListingRow],
    *,
    report_dir: Path | None = None,
    stem: str = DEFAULT_REPORT_STEM,
    before: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    """Write MD + CSV coverage report under ``.scratch/``."""
    out_dir = report_dir or SCRATCH_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{stem}.md"
    csv_path = out_dir / f"{stem}.csv"
    summary = summarize_coverage(rows)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "# Epic 3 Task #34 — listing depth (no invented GMV)",
        "",
        f"**Generated (UTC):** {generated}",
        f"**Counts:** tickers={summary['tickers']}, with_shop={summary['with_shop']}, "
        f"with_listing={summary['with_listing']}, with_gmv_listing={summary['with_gmv_listing']}, "
        f"live_ok={summary['live_ok']}",
        "",
    ]
    if before:
        lines.extend(
            [
                "## Before → after (seed)",
                "",
                "| Metric | Before | After |",
                "|--------|--------|-------|",
                f"| Tickers with ≥1 listing | {before.get('with_listing')} | {summary['with_listing']} |",
                f"| Tickers with GMV listing (price×units) | {before.get('with_gmv_listing')} | {summary['with_gmv_listing']} |",
                f"| Tickers with marketplace shop URL | {before.get('with_shop')} | {summary['with_shop']} |",
                "",
                f"- Listing tickers after: {', '.join(summary['listing_tickers']) or '—'}",
                f"- GMV tickers after: {', '.join(summary['gmv_tickers']) or '—'}",
                "",
            ]
        )

    lines.extend(
        [
            "## Sample definitions",
            "",
            "| Sample | Meaning | n |",
            "|--------|---------|---|",
            f"| Mẫu niêm yết | Seed allowlist | {summary['tickers']} |",
            f"| Mẫu có shop TMĐT | digital_presence shopee/tiktok/lazada URL | {summary['with_shop']} |",
            f"| Mẫu có listing | ≥1 `marketplace_listings` row | {summary['with_listing']} |",
            f"| Mẫu có GMV listing | listing với cả price và units_sold_est | {summary['with_gmv_listing']} |",
            "",
            "B2B peers without shop keep `marketplace_listings: []` — no invented GMV.",
            "",
            "| stock_code | has_shop | n_seed | n_gmv | seed_sources | live_status | n_live | live_detail |",
            "|------------|----------|--------|-------|--------------|-------------|--------|-------------|",
        ]
    )
    for row in rows:
        sources = ",".join(row.seed_sources) if row.seed_sources else "-"
        detail = (row.live_detail or "-").replace("|", "/")
        lines.append(
            f"| {row.stock_code} | {str(row.has_shop).lower()} | {row.n_seed_listings} | "
            f"{row.n_gmv_listings} | {sources} | {row.live_status} | {row.n_live_listings} | {detail} |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "stock_code",
                "has_shop",
                "n_seed_listings",
                "n_gmv_listings",
                "seed_sources",
                "live_status",
                "n_live_listings",
                "live_detail",
                "shop_urls",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "stock_code": row.stock_code,
                    "has_shop": row.has_shop,
                    "n_seed_listings": row.n_seed_listings,
                    "n_gmv_listings": row.n_gmv_listings,
                    "seed_sources": ",".join(row.seed_sources),
                    "live_status": row.live_status,
                    "n_live_listings": row.n_live_listings,
                    "live_detail": row.live_detail,
                    "shop_urls": " ".join(row.shop_urls),
                }
            )

    return md_path, csv_path


def before_counts_from_prior_snapshot() -> dict[str, Any]:
    """Historical baseline before Task #34 DQC curation (5 brands with GMV)."""
    return {
        "with_shop": 6,
        "with_listing": 5,
        "with_gmv_listing": 5,
        "listing_tickers": ["RAL", "VNM", "FPT", "MSN", "PNJ"],
        "note": "Pre-#34: DQC had shop URL but empty listings",
    }


def assert_seed_file_readable() -> Path:
    if not SEED_FILE.exists():
        raise FileNotFoundError(SEED_FILE)
    json.loads(SEED_FILE.read_text(encoding="utf-8"))
    return SEED_FILE
