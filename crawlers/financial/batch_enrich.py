"""Batch CafeF/BCTC enrich for the seeded listed-company allowlist (Task #32).

Runs ``fetch_bctc`` per ticker, persists only when a report is returned, and
writes a provenance table. Missing CafeF fields stay null — never backfilled
from seed demo numbers into a CafeF row.
"""

from __future__ import annotations

import csv
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models import Company
from crawlers.financial.bctc_crawler import (
    SEED_FILE,
    FetchResult,
    fetch_bctc,
    upsert_financial_report,
)

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_DIR = ROOT / ".scratch"
DEFAULT_REPORT_STEM = "epic3-task32-cafef-bctc-report"


@dataclass
class EnrichRow:
    """One allowlist ticker outcome for the Task #32 report table."""

    ticker: str
    status: str  # cafef_ok | fallback | error
    detail: str
    period: str | None
    report_type: str | None
    source_url: str | None
    persisted: bool
    revenue: float | None = None
    employees: int | None = None


def load_allowlist_tickers() -> list[str]:
    """Stock codes from ``data/seeds/companies.json`` (order preserved)."""
    raw = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    companies = raw["companies"] if isinstance(raw, dict) else raw
    codes: list[str] = []
    seen: set[str] = set()
    for row in companies:
        code = str(row.get("stock_code") or "").strip().upper()
        if not code or code in seen:
            continue
        seen.add(code)
        codes.append(code)
    return codes


def classify_fetch_status(result: FetchResult) -> str:
    """Map FetchResult → report status ``cafef_ok|fallback|error``."""
    if result.status == "ok":
        return "cafef_ok"
    if result.status == "fallback":
        return "fallback"
    return "error"


def _period_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return str(value)[:10]


def enrich_ticker(
    db: Session | None,
    stock_code: str,
    *,
    persist: bool = True,
    use_fallback: bool = True,
) -> EnrichRow:
    """Fetch one ticker; upsert when a report exists (CafeF or labeled fallback)."""
    code = stock_code.strip().upper()
    result = fetch_bctc(code, use_fallback=use_fallback)
    status = classify_fetch_status(result)
    report = result.report
    period = _period_str(report.get("period")) if report else None
    report_type = report.get("report_type") if report else None
    source_url = result.source_url or (report.get("source_url") if report else None)
    revenue = report.get("revenue") if report else None
    employees = report.get("employees") if report else None
    persisted = False

    if persist and report is not None and db is not None:
        company = db.query(Company).filter_by(stock_code=code).first()
        if company is None:
            logger.warning("Skip persist %s — company not in DB (run seed first)", code)
        else:
            # Persist CafeF as-is (nulls stay null). Fallback rows keep their
            # labeled source_url — never merge seed fields into a CafeF report.
            upsert_financial_report(db, company.id, report)
            persisted = True

    return EnrichRow(
        ticker=code,
        status=status,
        detail=result.detail,
        period=period,
        report_type=report_type,
        source_url=source_url,
        persisted=persisted,
        revenue=revenue if isinstance(revenue, (int, float)) else None,
        employees=employees if isinstance(employees, int) else None,
    )


def enrich_allowlist(
    db: Session | None,
    tickers: list[str] | None = None,
    *,
    persist: bool = True,
    use_fallback: bool = True,
    sleep_s: float = 0.4,
) -> list[EnrichRow]:
    """Smoke/enrich full allowlist (or a subset). Sleep between HTTP calls."""
    codes = tickers or load_allowlist_tickers()
    rows: list[EnrichRow] = []
    for i, code in enumerate(codes):
        row = enrich_ticker(
            db, code, persist=persist, use_fallback=use_fallback
        )
        rows.append(row)
        logger.info(
            "BCTC enrich %s status=%s detail=%s persisted=%s",
            row.ticker,
            row.status,
            row.detail,
            row.persisted,
        )
        if sleep_s > 0 and i < len(codes) - 1:
            time.sleep(sleep_s)
    return rows


def write_enrich_report(
    rows: list[EnrichRow],
    *,
    report_dir: Path | None = None,
    stem: str = DEFAULT_REPORT_STEM,
) -> tuple[Path, Path]:
    """Write Markdown + CSV report. Returns (md_path, csv_path)."""
    out_dir = report_dir or DEFAULT_REPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{stem}.md"
    csv_path = out_dir / f"{stem}.csv"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1

    lines = [
        "# Epic 3 Task #32 — CafeF BCTC enrich report",
        "",
        f"**Generated (UTC):** {now}",
        f"**Tickers:** {len(rows)}",
        f"**Counts:** {', '.join(f'{k}={v}' for k, v in sorted(counts.items()))}",
        "",
        "| ticker | status | detail | period | report_type | source_url | persisted |",
        "|--------|--------|--------|--------|-------------|------------|-----------|",
    ]
    for row in rows:
        detail = (row.detail or "").replace("|", "/")
        src = (row.source_url or "").replace("|", "/")
        lines.append(
            f"| {row.ticker} | {row.status} | {detail} | {row.period or ''} | "
            f"{row.report_type or ''} | {src} | {row.persisted} |"
        )
    lines.append("")
    lines.append(
        "Status legend: `cafef_ok` = CafeF parse OK; `fallback` = labeled seed/fallback; "
        "`error` = no report. Missing fields (e.g. employees) stay null — not filled from seed."
    )
    lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    fieldnames = [
        "ticker",
        "status",
        "detail",
        "period",
        "report_type",
        "source_url",
        "persisted",
        "revenue",
        "employees",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    return md_path, csv_path
