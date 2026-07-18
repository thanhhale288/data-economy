"""Listed manufacturing company crawler.

Enriches the fixed 10-ticker sample: metadata, official website digital presence,
and structured BCTC via crawlers.financial. Ecommerce detection is delegated to
crawlers.companies.website_detector (Task 6).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.models import Company, DigitalPresence
from crawlers.companies.website_detector import detect_website
from crawlers.financial.bctc_crawler import fetch_bctc, upsert_financial_report

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SEED_FILE = DATA_DIR / "seeds" / "companies.json"

ALLOWED_TICKERS: tuple[str, ...] = (
    "RAL",
    "HPG",
    "VNM",
    "FPT",
    "GVR",
    "DGC",
    "MSN",
    "PNJ",
    "REE",
    "BMP",
)
ALLOWED_TICKER_SET = frozenset(ALLOWED_TICKERS)


def detect_ecommerce_site(url: str) -> tuple[bool, bool]:
    """Thin wrap of website_detector. Returns (has_ecommerce, has_checkout).

    On HTTP fail/block the tuple is (False, False); prefer crawl_company_website
    / DetectionResult.ok so callers can keep previous DB state.
    """
    result = detect_website(url)
    if not result.ok:
        return False, False
    return result.has_ecommerce, result.has_checkout


def crawl_company_website(company: Company) -> dict:
    """Detect website ecommerce flags. Includes ok so callers can keep prior state."""
    if not company.website_url:
        return {
            "ok": True,
            "has_ecommerce_site": False,
            "has_checkout": False,
            "detail": "no_url",
        }
    result = detect_website(company.website_url)
    return {
        "ok": result.ok,
        "has_ecommerce_site": result.has_ecommerce,
        "has_checkout": result.has_checkout,
        "detail": result.detail,
    }


def load_seed_companies() -> list[dict]:
    with open(SEED_FILE, encoding="utf-8") as f:
        companies = json.load(f)
    # Exactly the fixed sample — ignore any accidental extras in seed.
    by_code = {c["stock_code"]: c for c in companies if c.get("stock_code") in ALLOWED_TICKER_SET}
    return [by_code[code] for code in ALLOWED_TICKERS if code in by_code]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upsert_company_metadata(db: Session, seed: dict) -> Company:
    """Create or update company row from seed (+ published fields when present)."""
    code = seed["stock_code"]
    if code not in ALLOWED_TICKER_SET:
        raise ValueError(f"ticker not in fixed sample: {code}")

    company = db.query(Company).filter(Company.stock_code == code).first()
    fields = {
        "name": seed["name"],
        "vsic_code": seed["vsic_code"],
        "exchange": seed.get("exchange") or "HOSE",
        "website_url": seed.get("website_url"),
        "digital_channels": seed.get("digital_channels"),
        "description": seed.get("description"),
    }
    if company is None:
        company = Company(stock_code=code, has_ecommerce_site=False, **fields)
        db.add(company)
        db.flush()
    else:
        for key, value in fields.items():
            setattr(company, key, value)
    company.updated_at = _utcnow()
    db.commit()
    db.refresh(company)
    return company


def upsert_website_presence(
    db: Session,
    company: Company,
    *,
    url: str | None,
    has_checkout: bool,
) -> DigitalPresence | None:
    """Ensure a single active website channel for the company."""
    if not url:
        return None

    existing = (
        db.query(DigitalPresence)
        .filter_by(company_id=company.id, channel_type="website")
        .all()
    )
    if not existing:
        row = DigitalPresence(
            company_id=company.id,
            channel_type="website",
            url=url,
            is_active=True,
            has_checkout=has_checkout,
            match_confidence=1.0,
            crawled_at=_utcnow(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    primary = existing[0]
    primary.url = url
    primary.is_active = True
    primary.has_checkout = has_checkout
    primary.match_confidence = primary.match_confidence or 1.0
    primary.crawled_at = _utcnow()
    # Collapse accidental duplicates on re-run.
    for dup in existing[1:]:
        db.delete(dup)
    db.commit()
    db.refresh(primary)
    return primary


def enrich_company(db: Session, seed: dict) -> bool:
    """Enrich one seed company: metadata, website presence, BCTC upsert."""
    company = upsert_company_metadata(db, seed)

    seed_website = next(
        (
            dp
            for dp in seed.get("digital_presence", [])
            if dp.get("channel_type") == "website" and dp.get("url")
        ),
        None,
    )
    # Detect on the URL we will store (seed website channel may differ from
    # corporate website_url, e.g. FPT: fpt.com.vn vs fptshop.com.vn).
    detect_url = (seed_website or {}).get("url") or company.website_url
    if detect_url:
        result = detect_website(detect_url)
        website_info = {
            "ok": result.ok,
            "has_ecommerce_site": result.has_ecommerce,
            "has_checkout": result.has_checkout,
            "detail": result.detail,
        }
    else:
        website_info = {
            "ok": True,
            "has_ecommerce_site": False,
            "has_checkout": False,
            "detail": "no_url",
        }

    if website_info["ok"]:
        # Live detect succeeded — trust detector only (do not OR with seed).
        company.has_ecommerce_site = bool(website_info["has_ecommerce_site"])
        has_checkout = bool(website_info["has_checkout"])
    else:
        # HTTP fail/block — do not guess. Keep previous DB state; on first enrich
        # (no website presence yet) fall back to seed provenance.
        logger.warning(
            "Website detect fail %s (%s): %s — keeping previous ecommerce/checkout flags",
            company.stock_code,
            detect_url,
            website_info.get("detail"),
        )
        existing_presence = (
            db.query(DigitalPresence)
            .filter_by(company_id=company.id, channel_type="website")
            .first()
        )
        if existing_presence is None:
            company.has_ecommerce_site = seed.get(
                "has_ecommerce_site", company.has_ecommerce_site
            )
            has_checkout = bool((seed_website or {}).get("has_checkout", False))
        else:
            # Leave company.has_ecommerce_site unchanged.
            has_checkout = existing_presence.has_checkout

    company.updated_at = _utcnow()
    db.commit()

    website_url = company.website_url or seed.get("website_url")
    presence_url = (seed_website or {}).get("url") or website_url
    upsert_website_presence(
        db,
        company,
        url=presence_url,
        has_checkout=has_checkout,
    )

    bctc = fetch_bctc(company.stock_code, use_fallback=True)
    if bctc.report is not None:
        upsert_financial_report(db, company.id, bctc.report)
        logger.info(
            "BCTC %s status=%s source=%s",
            company.stock_code,
            bctc.status,
            bctc.source_url,
        )
    else:
        logger.warning(
            "BCTC missing for %s: %s — no invented values",
            company.stock_code,
            bctc.detail,
        )

    return True


def update_company_from_seed(db: Session, seed: dict) -> bool:
    """Backward-compatible alias used by older call sites."""
    if seed.get("stock_code") not in ALLOWED_TICKER_SET:
        return False
    return enrich_company(db, seed)


def run_company_crawl(db: Session) -> int:
    """Entry point for scheduler/pipeline — enrich exactly the 10 sample tickers."""
    seeds = load_seed_companies()
    count = 0
    for seed in seeds:
        if enrich_company(db, seed):
            count += 1
    return count
