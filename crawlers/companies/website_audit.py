"""Batch website detector + marketplace URL audit for the seed allowlist (Task #33).

Runs ``detect_website`` per allowlist ticker, lists the marketplace channel URLs
that seed/DB claim, and reports three kinds of inconsistency:

* ``flag_vs_url_mismatch`` — ``digital_channels.<ch>=true`` without a
  ``digital_presence`` URL (or a URL with the flag off).
* ``db_mismatch`` — DB ``digital_presence`` drifted from seed (missing channel,
  different URL, ``has_ecommerce_site`` differs).
* detection fail — HTTP 403/timeout/block → ``website_ok=False`` and
  ``has_checkout=None`` (unknown). Never invent ``has_checkout=True``.

Honesty: checkout is only ever written to the DB from a *successful* live
detection. A blocked or failed fetch leaves prior DB checkout untouched.
"""

from __future__ import annotations

import csv
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.models import Company, DigitalPresence
from crawlers.companies.listed_companies import load_seed_companies
from crawlers.companies.website_detector import DetectionResult, detect_website

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_DIR = ROOT / ".scratch"
DEFAULT_REPORT_STEM = "epic3-task33-website-url-audit"

MARKETPLACE_CHANNELS: tuple[str, ...] = ("shopee", "tiktok", "lazada")
AUDITED_CHANNELS: tuple[str, ...] = ("website",) + MARKETPLACE_CHANNELS


@dataclass
class WebsiteQaRow:
    """One allowlist ticker outcome for the Task #33 audit table.

    ``None`` means *unknown* (fetch blocked/failed or detection skipped) — it is
    not the same as ``False``.
    """

    stock_code: str
    website_ok: bool | None
    has_checkout: bool | None
    shopee_url: str | None
    tiktok_url: str | None
    flag_vs_url_mismatch: str
    lazada_url: str | None = None
    has_ecommerce: bool | None = None
    detected_url: str | None = None
    detect_detail: str = ""
    db_mismatch: str = ""
    fixed: str = ""


@dataclass
class FixSummary:
    """What ``apply_db_fixes`` changed for one ticker."""

    actions: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _clean_url(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def channel_urls(seed: dict) -> dict[str, str | None]:
    """First non-empty ``digital_presence`` URL per channel type."""
    urls: dict[str, str | None] = {}
    for dp in seed.get("digital_presence") or []:
        channel = str(dp.get("channel_type") or "").strip().lower()
        if not channel or urls.get(channel):
            continue
        urls[channel] = _clean_url(dp.get("url"))
    return urls


def detect_target_url(seed: dict) -> str | None:
    """URL the detector should hit.

    Mirrors ``enrich_company``: the stored website channel wins over the
    corporate ``website_url`` (FPT: fpt.com.vn vs fptshop.com.vn).
    """
    urls = channel_urls(seed)
    return urls.get("website") or _clean_url(seed.get("website_url"))


def seed_flag_mismatches(seed: dict) -> list[str]:
    """Flag/URL inconsistencies inside the seed row itself."""
    channels = seed.get("digital_channels") or {}
    urls = channel_urls(seed)
    problems: list[str] = []
    for channel in AUDITED_CHANNELS:
        flagged = bool(channels.get(channel))
        url = urls.get(channel)
        if flagged and not url:
            problems.append(f"{channel}_flag_without_url")
        elif url and not flagged:
            problems.append(f"{channel}_url_without_flag")
    if seed.get("has_ecommerce_site") and not any(
        urls.get(channel) for channel in AUDITED_CHANNELS
    ):
        problems.append("has_ecommerce_site_without_any_url")
    return problems


def db_mismatches(db: Session | None, seed: dict) -> list[str]:
    """How DB ``digital_presence`` / company flags drifted from seed."""
    if db is None:
        return []
    code = str(seed.get("stock_code") or "").strip().upper()
    company = db.query(Company).filter_by(stock_code=code).first()
    if company is None:
        return ["db_missing_company"]

    db_rows = {
        str(row.channel_type or "").strip().lower(): row
        for row in db.query(DigitalPresence).filter_by(company_id=company.id).all()
    }
    seed_urls = channel_urls(seed)
    problems: list[str] = []
    for channel in AUDITED_CHANNELS:
        seed_url = seed_urls.get(channel)
        db_row = db_rows.get(channel)
        if seed_url and db_row is None:
            problems.append(f"db_missing_{channel}_url")
        elif seed_url and _clean_url(db_row.url) != seed_url:
            problems.append(f"db_url_differs_{channel}")
    if bool(company.has_ecommerce_site) != bool(seed.get("has_ecommerce_site")):
        problems.append("db_has_ecommerce_site_differs")
    return problems


def audit_ticker(
    db: Session | None,
    seed: dict,
    *,
    detect: object = detect_website,
    detect_enabled: bool = True,
) -> WebsiteQaRow:
    """Audit one seed company (live detect optional)."""
    code = str(seed["stock_code"]).strip().upper()
    urls = channel_urls(seed)
    target = detect_target_url(seed)

    website_ok: bool | None = None
    has_checkout: bool | None = None
    has_ecommerce: bool | None = None
    detail = "detect_skipped"

    if detect_enabled:
        if not target:
            website_ok = False
            detail = "missing_url"
        else:
            result: DetectionResult = detect(target)  # type: ignore[operator]
            detail = result.detail
            if result.ok:
                website_ok = True
                has_checkout = bool(result.has_checkout)
                has_ecommerce = bool(result.has_ecommerce)
            else:
                # HTTP fail / block / timeout — leave checkout unknown.
                website_ok = False
                logger.warning(
                    "Website audit %s (%s): %s — checkout stays unknown",
                    code,
                    target,
                    detail,
                )

    return WebsiteQaRow(
        stock_code=code,
        website_ok=website_ok,
        has_checkout=has_checkout,
        shopee_url=urls.get("shopee"),
        tiktok_url=urls.get("tiktok"),
        flag_vs_url_mismatch=";".join(seed_flag_mismatches(seed)),
        lazada_url=urls.get("lazada"),
        has_ecommerce=has_ecommerce,
        detected_url=target,
        detect_detail=detail,
        db_mismatch=";".join(db_mismatches(db, seed)),
    )


def apply_db_fixes(db: Session, seed: dict, row: WebsiteQaRow) -> FixSummary:
    """Sync DB ``digital_presence`` to the seed URLs for one company.

    Adds/repairs marketplace + website channel URLs from seed provenance. Website
    ``has_checkout`` is only rewritten when this run detected it live
    (``website_ok is True``); an unknown detection is skipped, not guessed.
    """
    summary = FixSummary()
    code = str(seed.get("stock_code") or "").strip().upper()
    company = db.query(Company).filter_by(stock_code=code).first()
    if company is None:
        summary.skipped.append("no_company_run_seed_first")
        return summary

    db_rows = {
        str(dp.channel_type or "").strip().lower(): dp
        for dp in db.query(DigitalPresence).filter_by(company_id=company.id).all()
    }
    seed_dp_by_channel = {
        str(dp.get("channel_type") or "").strip().lower(): dp
        for dp in seed.get("digital_presence") or []
    }
    seed_urls = channel_urls(seed)

    for channel in AUDITED_CHANNELS:
        seed_url = seed_urls.get(channel)
        if not seed_url:
            continue
        seed_dp = seed_dp_by_channel.get(channel) or {}
        existing = db_rows.get(channel)
        if existing is None:
            db.add(
                DigitalPresence(
                    company_id=company.id,
                    channel_type=channel,
                    url=seed_url,
                    is_active=True,
                    has_checkout=bool(seed_dp.get("has_checkout", False)),
                    match_confidence=seed_dp.get("match_confidence"),
                    crawled_at=_utcnow(),
                )
            )
            summary.actions.append(f"added_{channel}_url")
        elif _clean_url(existing.url) != seed_url:
            existing.url = seed_url
            existing.crawled_at = _utcnow()
            summary.actions.append(f"updated_{channel}_url")

    db.flush()
    website_row = (
        db.query(DigitalPresence)
        .filter_by(company_id=company.id, channel_type="website")
        .first()
    )
    if website_row is not None:
        if row.website_ok is True and bool(website_row.has_checkout) != bool(
            row.has_checkout
        ):
            website_row.has_checkout = bool(row.has_checkout)
            website_row.crawled_at = _utcnow()
            summary.actions.append("updated_website_has_checkout_from_live")
        elif row.website_ok is not True:
            summary.skipped.append("website_checkout_unknown_kept_previous")

    if bool(company.has_ecommerce_site) != bool(seed.get("has_ecommerce_site")):
        # Seed is the curated provenance for the flag; live detect writes it via
        # enrich_company, not here.
        company.has_ecommerce_site = bool(seed.get("has_ecommerce_site"))
        summary.actions.append("updated_has_ecommerce_site_from_seed")

    if summary.actions:
        company.updated_at = _utcnow()
        db.commit()
    return summary


def audit_allowlist(
    db: Session | None,
    tickers: list[str] | None = None,
    *,
    detect: object = detect_website,
    detect_enabled: bool = True,
    fix_db: bool = False,
    sleep_s: float = 0.4,
) -> list[WebsiteQaRow]:
    """Audit the full allowlist (or a subset), optionally fixing DB drift."""
    seeds = load_seed_companies(tickers=tickers)
    rows: list[WebsiteQaRow] = []
    for i, seed in enumerate(seeds):
        row = audit_ticker(
            db, seed, detect=detect, detect_enabled=detect_enabled
        )
        if fix_db and db is not None:
            summary = apply_db_fixes(db, seed, row)
            row.fixed = ";".join(summary.actions)
            # Re-check so the report shows post-fix state.
            row.db_mismatch = ";".join(db_mismatches(db, seed))
        rows.append(row)
        logger.info(
            "Website audit %s website_ok=%s checkout=%s mismatch=%s db=%s fixed=%s",
            row.stock_code,
            row.website_ok,
            row.has_checkout,
            row.flag_vs_url_mismatch or "-",
            row.db_mismatch or "-",
            row.fixed or "-",
        )
        if detect_enabled and sleep_s > 0 and i < len(seeds) - 1:
            time.sleep(sleep_s)
    return rows


def summarize(rows: list[WebsiteQaRow]) -> dict[str, int]:
    """Counts used by the report header and the CLI summary line."""
    return {
        "tickers": len(rows),
        "website_ok": sum(1 for r in rows if r.website_ok is True),
        "website_fail": sum(1 for r in rows if r.website_ok is False),
        "website_unknown": sum(1 for r in rows if r.website_ok is None),
        "has_checkout": sum(1 for r in rows if r.has_checkout is True),
        "checkout_unknown": sum(1 for r in rows if r.has_checkout is None),
        "flag_url_mismatch": sum(1 for r in rows if r.flag_vs_url_mismatch),
        "db_mismatch": sum(1 for r in rows if r.db_mismatch),
        "marketplace_urls": sum(
            1
            for r in rows
            for url in (r.shopee_url, r.tiktok_url, r.lazada_url)
            if url
        ),
    }


def _cell(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "true" if value else "false"


REPORT_FIELDNAMES = [
    "stock_code",
    "website_ok",
    "has_checkout",
    "shopee_url",
    "tiktok_url",
    "flag_vs_url_mismatch",
    "lazada_url",
    "has_ecommerce",
    "detected_url",
    "detect_detail",
    "db_mismatch",
    "fixed",
]


def write_audit_report(
    rows: list[WebsiteQaRow],
    *,
    report_dir: Path | None = None,
    stem: str = DEFAULT_REPORT_STEM,
) -> tuple[Path, Path]:
    """Write Markdown + CSV audit report. Returns (md_path, csv_path)."""
    out_dir = report_dir or DEFAULT_REPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{stem}.md"
    csv_path = out_dir / f"{stem}.csv"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    counts = summarize(rows)

    lines = [
        "# Epic 3 Task #33 — website detector + marketplace URL audit",
        "",
        f"**Generated (UTC):** {now}",
        f"**Counts:** {', '.join(f'{k}={v}' for k, v in counts.items())}",
        "",
        "| stock_code | website_ok | has_checkout | shopee_url | tiktok_url | "
        "flag_vs_url_mismatch | db_mismatch | detect_detail |",
        "|------------|-----------|--------------|------------|------------|"
        "----------------------|-------------|---------------|",
    ]
    for row in rows:
        detail = (row.detect_detail or "").replace("|", "/")
        lines.append(
            f"| {row.stock_code} | {_cell(row.website_ok)} | {_cell(row.has_checkout)} | "
            f"{row.shopee_url or ''} | {row.tiktok_url or ''} | "
            f"{row.flag_vs_url_mismatch or '-'} | {row.db_mismatch or '-'} | {detail} |"
        )
    lines += [
        "",
        "`unknown` = HTTP block/timeout or detection skipped — **not** a false. "
        "Checkout is never inferred from a failed fetch.",
        "",
        "`flag_vs_url_mismatch` empty (`-`) = `digital_channels` agrees with "
        "`digital_presence` URLs. `db_mismatch` compares DB rows against seed; "
        "re-run with `--fix-db` to sync missing/stale URLs.",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=REPORT_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: asdict(row)[k] for k in REPORT_FIELDNAMES})

    return md_path, csv_path
