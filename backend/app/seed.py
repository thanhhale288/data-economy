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
from backend.app.services.website_verify import merge_website_verify_into_channels

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
        # Annual seed is demo/sourced seed — never pretend it is CafeF live.
        "source_url": "seed:companies.json",
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


def _upsert_digital_presence(db, company_id: int, digital_presence: list) -> None:
    """Upsert all seed digital_presence channels (website + marketplace).

    Re-seed used to refresh only the website channel, which left marketplace
    URLs missing after an earlier incomplete insert (e.g. DQC shopee).
    """
    for dp in digital_presence or []:
        channel = (dp.get("channel_type") or "").strip().lower()
        url = (dp.get("url") or "").strip()
        if not channel or not url:
            continue
        existing = (
            db.query(DigitalPresence)
            .filter(
                DigitalPresence.company_id == company_id,
                DigitalPresence.channel_type == channel,
            )
            .first()
        )
        if existing:
            existing.url = url
            existing.has_checkout = dp.get("has_checkout", False)
            existing.match_confidence = dp.get("match_confidence")
            existing.is_active = True
            continue
        db.add(
            DigitalPresence(
                company_id=company_id,
                channel_type=channel,
                url=url,
                has_checkout=dp.get("has_checkout", False),
                match_confidence=dp.get("match_confidence"),
                crawled_at=datetime.now(timezone.utc),
            )
        )


def _upsert_marketplace_listings(db, company_id: int, listings: list) -> None:
    """Upsert seed marketplace_listings by (platform, product_name).

    Task #34: re-seed previously skipped listings on update, so curated depth
    (e.g. DQC) reaches existing DB rows. Never invent revenue — recompute from
    price × units when both present.
    """
    from crawlers.marketplace.common import compute_revenue_est, normalize_listing_source

    for ml in listings or []:
        platform = (ml.get("platform") or "").strip()
        name = (ml.get("product_name") or "").strip()
        if not platform or not name:
            continue
        price = ml.get("price")
        units = ml.get("units_sold_est")
        revenue = compute_revenue_est(price, units)
        source = normalize_listing_source(ml.get("source") or "seed")
        existing = (
            db.query(MarketplaceListing)
            .filter(
                MarketplaceListing.company_id == company_id,
                MarketplaceListing.platform == platform,
                MarketplaceListing.product_name == name,
            )
            .first()
        )
        if existing:
            existing.price = price
            existing.units_sold_est = units
            existing.revenue_est = revenue
            existing.rating = ml.get("rating")
            existing.source = source
            if ml.get("product_url"):
                existing.product_url = ml["product_url"]
            existing.crawled_at = datetime.now(timezone.utc)
            continue
        db.add(
            MarketplaceListing(
                company_id=company_id,
                platform=platform,
                product_name=name,
                price=price,
                units_sold_est=units,
                revenue_est=revenue,
                rating=ml.get("rating"),
                product_url=ml.get("product_url"),
                source=source,
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
        channels = merge_website_verify_into_channels(c)
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
                if field == "has_ecommerce_site":
                    value = c.get(field, False)
                elif field == "digital_channels":
                    value = channels
                else:
                    value = c.get(field)
                setattr(existing, field, value)
            _upsert_financial(db, existing.id, c.get("financial", {}))
            _upsert_digital_presence(db, existing.id, c.get("digital_presence", []))
            _upsert_marketplace_listings(
                db, existing.id, c.get("marketplace_listings", [])
            )
            updated += 1
            continue

        company = Company(
            stock_code=c["stock_code"],
            name=c["name"],
            vsic_code=c["vsic_code"],
            exchange=c["exchange"],
            website_url=c.get("website_url"),
            has_ecommerce_site=c.get("has_ecommerce_site", False),
            digital_channels=channels,
            description=c.get("description"),
        )
        db.add(company)
        db.flush()

        _upsert_financial(db, company.id, c.get("financial", {}))
        _upsert_digital_presence(db, company.id, c.get("digital_presence", []))
        _upsert_marketplace_listings(
            db, company.id, c.get("marketplace_listings", [])
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


def run_seed(*, offline: bool = False):
    _ensure_schema_ready()
    db = SessionLocal()
    try:
        vsic_ins, vsic_upd = load_vsic_mappings(db)
        company_ins, company_upd = load_companies(db)
        gso_count = 0
        oecd_count = 0
        if offline:
            print("[seed] offline mode — skip live GSO/OECD crawl")
        else:
            gso_count = seed_gso_sample(db)
            oecd_count = seed_oecd_sample(db)
        print(
            f"Seeded: VSIC +{vsic_ins}/~{vsic_upd}, companies +{company_ins}/~{company_upd}, "
            f"{gso_count} GSO records, {oecd_count} OECD records"
        )
    finally:
        db.close()


if __name__ == "__main__":
    import os

    run_seed(offline=os.environ.get("SEED_OFFLINE", "").lower() in {"1", "true", "yes"})
