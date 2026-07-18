"""Digital economy metrics computation for manufacturing companies.

Online revenue prefers Σ(price × units_sold) / revenue_est from marketplace
listings (shopee / tiktok / lazada). Seed rows with platform=website are
excluded from the sum (see MODULE NOTES). Digital VA formula matches CONTEXT.md
and must not be changed without an ADR.
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session, joinedload

from backend.app.models import Company, DigitalMetric, MarketplaceListing

logger = logging.getLogger(__name__)

# Marketplace platforms counted toward online_revenue_est.
# platform=website seed rows (e.g. RAL downlight) are NOT included — website
# sales are reflected via digital_presence / has_ecommerce_site adoption, not
# as marketplace GMV. See wave2-task7-report §6 decision for Task 9.
MARKETPLACE_PLATFORMS = frozenset({"shopee", "tiktok", "lazada"})

# ---------------------------------------------------------------------------
# Industry-ratio interpolation (CONTEXT: allowed when listings missing)
# ---------------------------------------------------------------------------
# REJECTED: prior silent fallback `revenue × adoption × 0.15` had no GSO /
# VECOM / OECD source — that invents online revenue.
# Until a sourced manufacturing e-commerce share is wired (proposed: GSO M3 /
# VECOM industry ratio under data/mappings/), missing listings → 0.0 + log.
# Callers may pass an explicit ratio via estimate_online_revenue(..., industry_ratio=).
SOURCED_INDUSTRY_ECOMMERCE_RATIO: float | None = None

# Digital VA component proxies (structure fixed; do not change without ADR)
_DEFAULT_GROSS_MARGIN = 0.25
_COST_SAVINGS_RATE = 0.05  # Cost_savings = Online_revenue × this rate
_DIGITAL_INVESTMENT_RATE = 0.02  # Digital_investment = Online_revenue × this rate


def _channel_weights() -> dict[str, float]:
    return {"website": 0.35, "shopee": 0.30, "tiktok": 0.20, "lazada": 0.15}


def compute_adoption_score(company: Company) -> float:
    """Weighted digital adoption from active, threshold-verified channels.

    Marketplace channels count only when ``match_confidence`` is missing
    (legacy) or ≥ 0.65 (CONTEXT shop-matcher threshold). Website uses
    ``is_active`` only (corporate URL, not fuzzy shop match).
    """
    weights = _channel_weights()
    channels: set[str] = set()
    for dp in company.digital_presence:
        if not dp.is_active:
            continue
        if dp.channel_type in MARKETPLACE_PLATFORMS:
            conf = dp.match_confidence
            if conf is not None and conf < 0.65:
                continue
        channels.add(dp.channel_type)
    score = sum(weights.get(ch, 0) for ch in channels)
    if company.has_ecommerce_site:
        score = min(1.0, score + 0.1)
    return round(min(score, 1.0), 3)


def compute_channel_diversity(company: Company) -> float:
    """Share of the four tracked channels that are active and verified."""
    active: set[str] = set()
    for dp in company.digital_presence:
        if not dp.is_active:
            continue
        if dp.channel_type in MARKETPLACE_PLATFORMS:
            conf = dp.match_confidence
            if conf is not None and conf < 0.65:
                continue
        active.add(dp.channel_type)
    return round(len(active) / 4.0, 3)


def listing_contribution(listing: MarketplaceListing) -> float | None:
    """Revenue from one listing: price×units when both present, else revenue_est."""
    if listing.price is not None and listing.units_sold_est is not None:
        return float(listing.price) * int(listing.units_sold_est)
    if listing.revenue_est is not None:
        return float(listing.revenue_est)
    return None


def marketplace_listings_for_revenue(
    company: Company,
) -> list[MarketplaceListing]:
    """Listings on shopee/tiktok/lazada only (excludes platform=website)."""
    return [
        ml
        for ml in company.marketplace_listings
        if (ml.platform or "").lower() in MARKETPLACE_PLATFORMS
    ]


def estimate_online_revenue(
    company: Company,
    *,
    industry_ratio: float | None = None,
) -> float:
    """Estimate firm online revenue from marketplace listings.

    Priority:
    1. Σ listing contributions on marketplace platforms (price×units or revenue_est)
    2. If no usable listings: industry_ratio × latest BCTC revenue when ratio is
       explicitly provided (sourced), else SOURCED_INDUSTRY_ECOMMERCE_RATIO if set
    3. Otherwise 0.0 with log — never invent a silent ratio
    """
    total = 0.0
    usable = 0
    for ml in marketplace_listings_for_revenue(company):
        contrib = listing_contribution(ml)
        if contrib is not None:
            total += contrib
            usable += 1

    if usable > 0:
        return total

    ratio = industry_ratio if industry_ratio is not None else SOURCED_INDUSTRY_ECOMMERCE_RATIO
    fin = company.financial_reports
    if ratio is not None and fin:
        latest = max(fin, key=lambda r: r.period)
        revenue = latest.revenue
        if revenue is not None and revenue > 0:
            interpolated = float(revenue) * float(ratio)
            logger.info(
                "online_revenue for %s: no marketplace listings; "
                "industry-ratio interpolation ratio=%s → %.2f "
                "(caller/module must document ratio source)",
                getattr(company, "stock_code", company.id),
                ratio,
                interpolated,
            )
            return interpolated

    logger.info(
        "online_revenue for %s: no marketplace listing revenue and no sourced "
        "industry_ratio — returning 0.0 (not inventing)",
        getattr(company, "stock_code", company.id),
    )
    return 0.0


def compute_digital_va(
    online_revenue: float,
    gross_margin: float | None,
    adoption_score: float,
) -> float:
    """Digital VA per CONTEXT.md — do not change structure/constants without ADR.

    Digital_VA = (Online_revenue × Gross_margin)
               + (Cost_savings × Adoption_score)
               - Digital_investment

    where Cost_savings = Online_revenue × 0.05,
          Digital_investment = Online_revenue × 0.02,
          Gross_margin defaults to 0.25 when BCTC margin is missing.
    """
    margin = gross_margin if gross_margin is not None else _DEFAULT_GROSS_MARGIN
    cost_savings = online_revenue * _COST_SAVINGS_RATE
    digital_investment = online_revenue * _DIGITAL_INVESTMENT_RATE
    return (
        online_revenue * margin
        + cost_savings * adoption_score
        - digital_investment
    )


def compute_industry_share(
    digital_va: float, vsic_code: str, all_metrics: list[tuple[str, float]]
) -> float:
    prefix = vsic_code[:2] if len(vsic_code) >= 2 else vsic_code
    industry_total = sum(va for code, va in all_metrics if code.startswith(prefix))
    if industry_total == 0:
        return 0.0
    return round(digital_va / industry_total * 100, 2)


def compute_company_metrics(db: Session, company: Company, period: date) -> DigitalMetric:
    adoption = compute_adoption_score(company)
    diversity = compute_channel_diversity(company)
    online_rev = estimate_online_revenue(company)

    gross_margin = None
    if company.financial_reports:
        latest = max(company.financial_reports, key=lambda r: r.period)
        gross_margin = latest.gross_margin

    digital_va = compute_digital_va(online_rev, gross_margin, adoption)

    total_revenue = 0.0
    if company.financial_reports:
        latest = max(company.financial_reports, key=lambda r: r.period)
        total_revenue = latest.revenue or 0
    online_ratio = online_rev / total_revenue if total_revenue > 0 else 0

    return DigitalMetric(
        company_id=company.id,
        period=period,
        online_revenue_est=round(online_rev, 2),
        digital_va_contribution=round(digital_va, 2),
        industry_share_pct=0.0,
        digital_adoption_score=adoption,
        channel_diversity=diversity,
        online_revenue_ratio=round(online_ratio, 4),
    )


def compute_all_digital_metrics(db: Session) -> int:
    companies = (
        db.query(Company)
        .options(
            joinedload(Company.digital_presence),
            joinedload(Company.marketplace_listings),
            joinedload(Company.financial_reports),
        )
        .all()
    )

    period = date(2024, 12, 31)
    all_va: list[tuple[str, float]] = []
    metrics: list[DigitalMetric] = []

    for company in companies:
        metric = compute_company_metrics(db, company, period)
        all_va.append((company.vsic_code, metric.digital_va_contribution or 0))
        metrics.append(metric)

    count = 0
    for metric in metrics:
        company = next(c for c in companies if c.id == metric.company_id)
        metric.industry_share_pct = compute_industry_share(
            metric.digital_va_contribution or 0,
            company.vsic_code,
            all_va,
        )

        existing = (
            db.query(DigitalMetric)
            .filter(
                DigitalMetric.company_id == metric.company_id,
                DigitalMetric.period == metric.period,
            )
            .first()
        )
        if existing:
            for attr in [
                "online_revenue_est",
                "digital_va_contribution",
                "industry_share_pct",
                "digital_adoption_score",
                "channel_diversity",
                "online_revenue_ratio",
            ]:
                setattr(existing, attr, getattr(metric, attr))
        else:
            db.add(metric)
            count += 1

    db.commit()
    return count
