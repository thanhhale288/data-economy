"""Seed VSIC mappings and sample companies into the database.

Schema must come from Alembic (`alembic upgrade head`) — not create_all.
"""

import json
from datetime import date, datetime, timezone
from pathlib import Path

from backend.app.database import SessionLocal, engine
from backend.app.models import (
    Company,
    DigitalPresence,
    FinancialReport,
    MarketplaceListing,
    VsicCode,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _ensure_schema_ready() -> None:
    """Fail fast if migrations have not been applied."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    required = {"vsic_codes", "companies", "alembic_version"}
    missing = required - tables
    if missing:
        raise SystemExit(
            "Database schema incomplete (missing: "
            + ", ".join(sorted(missing))
            + "). Run: alembic upgrade head"
        )


def load_vsic_mappings(db) -> tuple[int, int]:
    path = DATA_DIR / "mappings" / "vsic_isic_section_c.json"
    with open(path) as f:
        mappings = json.load(f)

    inserted = 0
    updated = 0
    for m in mappings:
        existing = db.query(VsicCode).filter(VsicCode.vsic_code == m["vsic_code"]).first()
        if not existing:
            db.add(VsicCode(**m))
            inserted += 1
            continue
        changed = False
        for field in ("isic_code", "level", "name_vi", "name_en", "parent_code"):
            if getattr(existing, field) != m.get(field):
                setattr(existing, field, m.get(field))
                changed = True
        if changed:
            updated += 1
    db.commit()
    return inserted, updated


def _migrate_legacy_bwe_to_bmp(db) -> bool:
    """Rename stale seed ticker BWE → BMP in place (keep company_id / FKs).

    Older Phase 2 DBs used BWE for the plastics sample slot; the fixed seed list
    is BMP (Nhựa Bình Minh). Returns True when a rename happened.
    """
    bmp = db.query(Company).filter(Company.stock_code == "BMP").first()
    bwe = db.query(Company).filter(Company.stock_code == "BWE").first()
    if bmp is not None or bwe is None:
        return False
    bwe.stock_code = "BMP"
    db.flush()
    return True


def _upsert_financial(db, company_id: int, fin: dict) -> None:
    if not fin:
        return
    period = date.fromisoformat(fin["period"])
    # Seed annual is authoritative; drop other annual rows (e.g. stale BWE-era)
    # but keep CafeF quarterly reports.
    for row in (
        db.query(FinancialReport)
        .filter(
            FinancialReport.company_id == company_id,
            FinancialReport.report_type == "annual",
            FinancialReport.period != period,
        )
        .all()
    ):
        db.delete(row)

    existing = (
        db.query(FinancialReport)
        .filter(
            FinancialReport.company_id == company_id,
            FinancialReport.period == period,
            FinancialReport.report_type == "annual",
        )
        .first()
    )
    fields = {
        "revenue": fin.get("revenue"),
        "profit_before_tax": fin.get("profit_before_tax"),
        "net_profit": fin.get("net_profit"),
        "total_assets": fin.get("total_assets"),
        "total_equity": fin.get("total_equity"),
        "current_assets": fin.get("current_assets"),
        "current_liabilities": fin.get("current_liabilities"),
        "operating_expenses": fin.get("operating_expenses"),
        "cost_of_goods": fin.get("cost_of_goods"),
        "rental_cost": fin.get("rental_cost"),
        "remuneration": fin.get("remuneration"),
        "employees": fin.get("employees"),
        "gross_margin": fin.get("gross_margin"),
    }
    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        return
    db.add(
        FinancialReport(
            company_id=company_id,
            period=period,
            report_type="annual",
            **fields,
        )
    )


def _upsert_website_presence(db, company_id: int, digital_presence: list) -> None:
    for dp in digital_presence or []:
        if dp.get("channel_type") != "website":
            continue
        existing = (
            db.query(DigitalPresence)
            .filter(
                DigitalPresence.company_id == company_id,
                DigitalPresence.channel_type == "website",
            )
            .first()
        )
        if existing:
            existing.url = dp["url"]
            existing.has_checkout = dp.get("has_checkout", False)
            existing.match_confidence = dp.get("match_confidence")
            continue
        db.add(
            DigitalPresence(
                company_id=company_id,
                channel_type="website",
                url=dp["url"],
                has_checkout=dp.get("has_checkout", False),
                match_confidence=dp.get("match_confidence"),
                crawled_at=datetime.now(timezone.utc),
            )
        )


def load_companies(db) -> tuple[int, int]:
    path = DATA_DIR / "seeds" / "companies.json"
    with open(path) as f:
        companies = json.load(f)

    if _migrate_legacy_bwe_to_bmp(db):
        print("Migrated legacy stock_code BWE → BMP (kept company_id / related rows)")

    inserted = 0
    updated = 0
    for c in companies:
        existing = db.query(Company).filter(Company.stock_code == c["stock_code"]).first()
        if existing:
            for field in (
                "name",
                "vsic_code",
                "exchange",
                "website_url",
                "has_ecommerce_site",
                "digital_channels",
                "description",
            ):
                setattr(
                    existing,
                    field,
                    c.get(field) if field != "has_ecommerce_site" else c.get(field, False),
                )
            _upsert_financial(db, existing.id, c.get("financial", {}))
            _upsert_website_presence(db, existing.id, c.get("digital_presence", []))
            updated += 1
            continue

        company = Company(
            stock_code=c["stock_code"],
            name=c["name"],
            vsic_code=c["vsic_code"],
            exchange=c["exchange"],
            website_url=c.get("website_url"),
            has_ecommerce_site=c.get("has_ecommerce_site", False),
            digital_channels=c.get("digital_channels"),
            description=c.get("description"),
        )
        db.add(company)
        db.flush()

        _upsert_financial(db, company.id, c.get("financial", {}))

        for dp in c.get("digital_presence", []):
            db.add(
                DigitalPresence(
                    company_id=company.id,
                    channel_type=dp["channel_type"],
                    url=dp["url"],
                    has_checkout=dp.get("has_checkout", False),
                    match_confidence=dp.get("match_confidence"),
                    crawled_at=datetime.now(timezone.utc),
                )
            )

        for ml in c.get("marketplace_listings", []):
            db.add(
                MarketplaceListing(
                    company_id=company.id,
                    platform=ml["platform"],
                    product_name=ml["product_name"],
                    price=ml.get("price"),
                    units_sold_est=ml.get("units_sold_est"),
                    revenue_est=ml.get("revenue_est"),
                    rating=ml.get("rating"),
                    crawled_at=datetime.now(timezone.utc),
                )
            )

        inserted += 1

    db.commit()
    return inserted, updated


def seed_gso_sample(db) -> int:
    """Load GSO macro via crawler (NSO SDMX IIP + PX-Web shipment/inventory)."""
    from crawlers.gso.iip_crawler import fetch_gso_macro, save_gso_records

    result = fetch_gso_macro()
    print(f"GSO crawl status={result.status}: {result.detail[:240]}")
    if not result.records:
        return 0
    return save_gso_records(db, result.records)


def seed_oecd_sample(db) -> int:
    """Load OECD indicators via SDMX client (VNM + peer EA20 MEI_IP). No random data."""
    from crawlers.oecd.sdmx_client import fetch_oecd_indicators, save_oecd_records

    result = fetch_oecd_indicators(country="VNM", include_peers=True)
    print(f"OECD crawl: {result.detail_summary}")
    if not result.records:
        return 0
    return save_oecd_records(db, result.records)


def run_seed():
    _ensure_schema_ready()
    db = SessionLocal()
    try:
        vsic_ins, vsic_upd = load_vsic_mappings(db)
        company_ins, company_upd = load_companies(db)
        gso_count = seed_gso_sample(db)
        oecd_count = seed_oecd_sample(db)
        print(
            f"Seeded: VSIC +{vsic_ins}/~{vsic_upd}, companies +{company_ins}/~{company_upd}, "
            f"{gso_count} GSO records, {oecd_count} OECD records"
        )
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
