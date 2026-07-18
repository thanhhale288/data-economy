"""Structured BCTC (financial report) crawler for the 10 listed sample companies.

Prefer live JSON/HTML when available; otherwise use sourced seed/fallback.
Never invent numeric fields — missing stays null with explicit provenance.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from backend.app.models import FinancialReport

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SEED_FILE = DATA_DIR / "seeds" / "companies.json"
FALLBACK_FILE = DATA_DIR / "raw" / "companies_bctc_fallback.json"
RAW_COMPANIES_DIR = DATA_DIR / "raw" / "companies"

SEED_SOURCE_URL = "seed:companies.json"
FALLBACK_SOURCE_PREFIX = "fallback:"
FALLBACK_SOURCE_URL = f"{FALLBACK_SOURCE_PREFIX}data/raw/companies_bctc_fallback.json"

HTTP_TIMEOUT = 20.0

FINANCIAL_FIELDS = (
    "revenue",
    "profit_before_tax",
    "net_profit",
    "total_assets",
    "total_equity",
    "current_assets",
    "current_liabilities",
    "operating_expenses",
    "cost_of_goods",
    "rental_cost",
    "remuneration",
    "employees",
    "gross_margin",
)

# Live CafeF pages are tried first via crawlers.financial.cafef.
# Empty templates keep the old "inject URLs in tests" path available.
DEFAULT_LIVE_URL_TEMPLATES: tuple[str, ...] = ()
USE_CAFEF_LIVE_DEFAULT = True


@dataclass
class FetchResult:
    """Outcome of a BCTC fetch for one ticker."""

    status: str  # ok | fallback | empty | error
    detail: str
    report: dict[str, Any] | None = None
    source_url: str | None = None

    @property
    def used_fallback(self) -> bool:
        return self.status == "fallback"


def _parse_number(raw: Any) -> float | int | None:
    """Parse a numeric cell; return None for blank/missing — never invent."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return raw
    text = str(raw).strip()
    if not text or text.lower() in {"null", "none", "n/a", "-", "—"}:
        return None
    cleaned = text.replace(",", "").replace(" ", "").replace("%", "")
    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return None


def _coerce_employees(value: float | int | None) -> int | None:
    if value is None:
        return None
    return int(value)


def _empty_fields() -> dict[str, Any]:
    return {name: None for name in FINANCIAL_FIELDS}


def parse_bctc_json(payload: dict[str, Any]) -> dict[str, Any]:
    """Parse a structured JSON BCTC document into a report dict."""
    fields = payload.get("fields") or {}
    period_raw = payload.get("period")
    if not period_raw:
        raise ValueError("BCTC JSON missing period")

    report = _empty_fields()
    report["stock_code"] = payload.get("stock_code")
    report["period"] = date.fromisoformat(str(period_raw)[:10])
    report["report_type"] = payload.get("report_type") or "annual"
    report["source_url"] = payload.get("source_url")

    for name in FINANCIAL_FIELDS:
        if name not in fields:
            report[name] = None
            continue
        parsed = _parse_number(fields.get(name))
        if name == "employees":
            report[name] = _coerce_employees(parsed)
        else:
            report[name] = parsed
    return report


def parse_bctc_html(
    html: str,
    *,
    stock_code: str | None = None,
    source_url: str | None = None,
) -> dict[str, Any]:
    """Parse an HTML table with data-field attributes into a report dict."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="bctc") or soup.find("table")
    if table is None:
        raise ValueError("BCTC HTML has no table")

    period_raw = table.get("data-period")
    report_type = table.get("data-report-type") or "annual"
    if not period_raw:
        raise ValueError("BCTC HTML table missing data-period")

    report = _empty_fields()
    report["stock_code"] = stock_code
    report["period"] = date.fromisoformat(str(period_raw)[:10])
    report["report_type"] = report_type
    report["source_url"] = source_url

    for cell in table.select("[data-field]"):
        field = cell.get("data-field")
        if field not in FINANCIAL_FIELDS:
            continue
        parsed = _parse_number(cell.get_text())
        if field == "employees":
            report[field] = _coerce_employees(parsed)
        else:
            report[field] = float(parsed) if parsed is not None else None
    return report


def _report_from_seed_financial(
    stock_code: str, fin: dict[str, Any], source_url: str
) -> dict[str, Any]:
    report = _empty_fields()
    report["stock_code"] = stock_code
    report["period"] = date.fromisoformat(str(fin["period"])[:10])
    report["report_type"] = fin.get("report_type") or "annual"
    report["source_url"] = source_url
    for name in FINANCIAL_FIELDS:
        if name not in fin:
            report[name] = None
            continue
        parsed = _parse_number(fin.get(name))
        if name == "employees":
            report[name] = _coerce_employees(parsed)
        else:
            report[name] = parsed
    return report


def load_seed_financial(stock_code: str) -> dict[str, Any] | None:
    """Load BCTC fields for a ticker from data/seeds/companies.json."""
    if not SEED_FILE.exists():
        return None
    with SEED_FILE.open(encoding="utf-8") as fh:
        companies = json.load(fh)
    for company in companies:
        if company.get("stock_code") != stock_code:
            continue
        fin = company.get("financial")
        if not fin or "period" not in fin:
            return None
        return _report_from_seed_financial(stock_code, fin, SEED_SOURCE_URL)
    return None


def load_fallback_financial(stock_code: str) -> dict[str, Any] | None:
    """Load sourced fallback under data/raw/ (file or companies/ dir)."""
    # Per-ticker file: data/raw/companies/{ticker}_bctc_fallback.json
    per_ticker = RAW_COMPANIES_DIR / f"{stock_code.lower()}_bctc_fallback.json"
    if per_ticker.exists():
        with per_ticker.open(encoding="utf-8") as fh:
            payload = json.load(fh)
        report = parse_bctc_json(payload)
        report["source_url"] = (
            payload.get("source_url")
            or f"{FALLBACK_SOURCE_PREFIX}data/raw/companies/{per_ticker.name}"
        )
        return report

    if FALLBACK_FILE.exists():
        with FALLBACK_FILE.open(encoding="utf-8") as fh:
            payload = json.load(fh)
        entries = payload if isinstance(payload, list) else payload.get("companies", [])
        for entry in entries:
            if entry.get("stock_code") != stock_code:
                continue
            if "fields" in entry:
                report = parse_bctc_json(entry)
            else:
                report = _report_from_seed_financial(
                    stock_code, entry.get("financial") or entry, FALLBACK_SOURCE_URL
                )
            report["source_url"] = entry.get("source_url") or FALLBACK_SOURCE_URL
            return report

    # Final sourced fallback: seed file itself.
    return load_seed_financial(stock_code)


def _detect_payload_kind(text: str, content_type: str) -> str:
    ct = (content_type or "").lower()
    stripped = text.lstrip()
    if "json" in ct or stripped.startswith("{") or stripped.startswith("["):
        return "json"
    if "html" in ct or stripped.lower().startswith("<!doctype") or "<html" in stripped[:200].lower():
        return "html"
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"
    return "unknown"


def _parse_live_body(
    text: str, *, stock_code: str, source_url: str, content_type: str
) -> dict[str, Any]:
    kind = _detect_payload_kind(text, content_type)
    if kind == "json":
        payload = json.loads(text)
        if isinstance(payload, list):
            raise ValueError("live JSON array not supported for single-ticker BCTC")
        if "fields" not in payload and "period" in payload:
            # Flat shape — wrap into structured form.
            fields = {name: payload.get(name) for name in FINANCIAL_FIELDS}
            payload = {
                "stock_code": payload.get("stock_code") or stock_code,
                "period": payload["period"],
                "report_type": payload.get("report_type") or "annual",
                "fields": fields,
                "source_url": source_url,
            }
        report = parse_bctc_json(payload)
        report["stock_code"] = report.get("stock_code") or stock_code
        report["source_url"] = source_url
        return report
    if kind == "html":
        report = parse_bctc_html(text, stock_code=stock_code, source_url=source_url)
        return report
    raise ValueError(f"unsupported live content type: {content_type!r}")


def fetch_bctc(
    stock_code: str,
    *,
    live_urls: tuple[str, ...] | None = None,
    use_fallback: bool = True,
    use_cafef: bool | None = None,
) -> FetchResult:
    """Fetch structured BCTC for one ticker; fall back to sourced seed data.

    Order: explicit ``live_urls`` → CafeF HTML adapter (default on) → seed/fallback.
    """
    from crawlers.financial.cafef import cafef_bctc_url, fetch_cafef_bctc, parse_cafef_bctc_html

    errors: list[str] = []
    code = stock_code.strip().upper()
    try_cafef = USE_CAFEF_LIVE_DEFAULT if use_cafef is None else use_cafef

    # 1) Explicit live URLs (JSON / labeled HTML fixtures)
    urls = list(live_urls) if live_urls is not None else list(DEFAULT_LIVE_URL_TEMPLATES)
    for url in urls:
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
                response = client.get(
                    url, headers={"User-Agent": "Mozilla/5.0 (compatible; MfgDataEconomy/1.0)"}
                )
            if response.status_code != 200:
                errors.append(f"http_error:{response.status_code}@{url}")
                continue
            # CafeF pages can also be passed explicitly
            if "cafef.vn" in url.lower():
                report = parse_cafef_bctc_html(
                    response.text, stock_code=code, source_url=str(response.url)
                )
            else:
                report = _parse_live_body(
                    response.text,
                    stock_code=code,
                    source_url=url,
                    content_type=response.headers.get("content-type", ""),
                )
            return FetchResult(
                status="ok",
                detail="live_ok",
                report=report,
                source_url=report.get("source_url") or url,
            )
        except httpx.TimeoutException as exc:
            errors.append(f"network_timeout:{exc}")
            logger.warning("BCTC fetch timeout for %s: %s", code, url)
        except httpx.HTTPError as exc:
            errors.append(f"network_error:{type(exc).__name__}")
            logger.warning("BCTC fetch network error for %s: %s", code, exc)
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            errors.append(f"parse_error:{exc}")
            logger.warning("BCTC parse error for %s: %s", code, exc)

    # 2) CafeF adapter (default live path for listed VN tickers)
    if try_cafef and live_urls is None:
        try:
            report = fetch_cafef_bctc(code, timeout=HTTP_TIMEOUT)
            return FetchResult(
                status="ok",
                detail="cafef_ok",
                report=report,
                source_url=report.get("source_url") or cafef_bctc_url(code),
            )
        except Exception as exc:  # network + parse — fall through to seed
            errors.append(f"cafef_error:{type(exc).__name__}:{exc}")
            logger.warning("CafeF BCTC failed for %s: %s", code, exc)

    if use_fallback:
        report = load_fallback_financial(code)
        if report is not None:
            detail = "fallback_after:" + (";".join(errors) if errors else "no_live_urls")
            return FetchResult(
                status="fallback",
                detail=detail,
                report=report,
                source_url=report.get("source_url"),
            )
        return FetchResult(
            status="empty",
            detail="no_fallback:" + (";".join(errors) if errors else "no_data"),
            report=None,
            source_url=None,
        )

    return FetchResult(
        status="error",
        detail=";".join(errors) if errors else "no_live_urls",
        report=None,
        source_url=None,
    )


def upsert_financial_report(
    db: Session, company_id: int, report: dict[str, Any]
) -> bool:
    """Insert or update by (company_id, period, report_type). Returns True if inserted."""
    period = report["period"]
    report_type = report.get("report_type") or "annual"
    existing = (
        db.query(FinancialReport)
        .filter_by(company_id=company_id, period=period, report_type=report_type)
        .first()
    )
    values = {name: report.get(name) for name in FINANCIAL_FIELDS}
    values["source_url"] = report.get("source_url")

    if existing is None:
        db.add(
            FinancialReport(
                company_id=company_id,
                period=period,
                report_type=report_type,
                **values,
            )
        )
        db.commit()
        return True

    for key, value in values.items():
        setattr(existing, key, value)
    db.commit()
    return False
