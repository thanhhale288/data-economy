"""Seed VSIC mappings and sample companies into the database."""

import json
from datetime import date, datetime
from pathlib import Path

from backend.app.database import Base, SessionLocal, engine
from backend.app.models import (
    Company,
    DigitalMetric,
    DigitalPresence,
    FinancialReport,
    GsoMacro,
    MarketplaceListing,
    OecdIndicator,
    VsicCode,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_vsic_mappings(db) -> int:
    path = DATA_DIR / "mappings" / "vsic_isic_section_c.json"
    with open(path) as f:
        mappings = json.load(f)

    count = 0
    for m in mappings:
        existing = db.query(VsicCode).filter(VsicCode.vsic_code == m["vsic_code"]).first()
        if not existing:
            db.add(VsicCode(**m))
            count += 1
    db.commit()
    return count


def load_companies(db) -> int:
    path = DATA_DIR / "seeds" / "companies.json"
    with open(path) as f:
        companies = json.load(f)

    count = 0
    for c in companies:
        existing = db.query(Company).filter(Company.stock_code == c["stock_code"]).first()
        if existing:
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

        fin = c.get("financial", {})
        if fin:
            db.add(
                FinancialReport(
                    company_id=company.id,
                    period=date.fromisoformat(fin["period"]),
                    report_type="annual",
                    revenue=fin.get("revenue"),
                    profit_before_tax=fin.get("profit_before_tax"),
                    net_profit=fin.get("net_profit"),
                    total_assets=fin.get("total_assets"),
                    total_equity=fin.get("total_equity"),
                    current_assets=fin.get("current_assets"),
                    current_liabilities=fin.get("current_liabilities"),
                    operating_expenses=fin.get("operating_expenses"),
                    cost_of_goods=fin.get("cost_of_goods"),
                    rental_cost=fin.get("rental_cost"),
                    remuneration=fin.get("remuneration"),
                    employees=fin.get("employees"),
                    gross_margin=fin.get("gross_margin"),
                )
            )

        for dp in c.get("digital_presence", []):
            db.add(
                DigitalPresence(
                    company_id=company.id,
                    channel_type=dp["channel_type"],
                    url=dp["url"],
                    has_checkout=dp.get("has_checkout", False),
                    match_confidence=dp.get("match_confidence"),
                    crawled_at=datetime.utcnow(),
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
                    crawled_at=datetime.utcnow(),
                )
            )

        count += 1

    db.commit()
    return count


def seed_gso_sample(db) -> int:
    """Seed sample GSO IIP data for demo when live crawl unavailable."""
    existing = db.query(GsoMacro).count()
    if existing > 0:
        return 0

    import random

    base_date = date(2020, 1, 1)
    indicators = [
        ("C", "IIP_C", "Chỉ số SXCN - Chế biến chế tạo"),
        ("C", "SHIPMENT_C", "Chỉ số xuất hàng công nghiệp"),
        ("C", "INVENTORY_C", "Chỉ số tồn kho công nghiệp"),
    ]
    count = 0
    value = 100.0
    for month_offset in range(60):
        y = 2020 + month_offset // 12
        m = (month_offset % 12) + 1
        period = date(y, m, 1)
        value *= 1 + random.uniform(-0.02, 0.035)

        for vsic, code, name in indicators:
            noise = random.uniform(0.95, 1.05)
            db.add(
                GsoMacro(
                    vsic_code=vsic,
                    indicator_code=code,
                    indicator_name=name,
                    period=period,
                    value=round(value * noise, 2),
                    unit="index_2015=100",
                )
            )
            count += 1

    db.commit()
    return count


def seed_oecd_sample(db) -> int:
    existing = db.query(OecdIndicator).count()
    if existing > 0:
        return 0

    import random

    indicators = [
        ("MEI_IP", "Industrial Production Index"),
        ("MEI_BCI", "Business Confidence Index"),
        ("INDIGO", "Digital Trade Openness Index"),
    ]
    count = 0
    value = 100.0
    for month_offset in range(60):
        y = 2020 + month_offset // 12
        m = (month_offset % 12) + 1
        period = date(y, m, 1)
        value *= 1 + random.uniform(-0.015, 0.025)

        for code, name in indicators:
            db.add(
                OecdIndicator(
                    indicator_code=code,
                    indicator_name=name,
                    country="VNM",
                    isic_code="C",
                    period=period,
                    value=round(value * random.uniform(0.96, 1.04), 2),
                    unit="index",
                    frequency="monthly",
                )
            )
            count += 1

    db.commit()
    return count


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        vsic_count = load_vsic_mappings(db)
        company_count = load_companies(db)
        gso_count = seed_gso_sample(db)
        oecd_count = seed_oecd_sample(db)
        print(
            f"Seeded: {vsic_count} VSIC codes, {company_count} companies, "
            f"{gso_count} GSO records, {oecd_count} OECD records"
        )
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
