"""Digital economy metrics computation for manufacturing companies."""

from datetime import date

from sqlalchemy.orm import Session, joinedload

from backend.app.models import Company, DigitalMetric, DigitalPresence, MarketplaceListing


def _channel_weights() -> dict[str, float]:
    return {"website": 0.35, "shopee": 0.30, "tiktok": 0.20, "lazada": 0.15}


def compute_adoption_score(company: Company) -> float:
    weights = _channel_weights()
    channels = {dp.channel_type for dp in company.digital_presence if dp.is_active}
    score = sum(weights.get(ch, 0) for ch in channels)
    if company.has_ecommerce_site:
        score = min(1.0, score + 0.1)
    return round(min(score, 1.0), 3)


def compute_channel_diversity(company: Company) -> float:
    active = [dp.channel_type for dp in company.digital_presence if dp.is_active]
    return round(len(set(active)) / 4.0, 3)


def estimate_online_revenue(company: Company) -> float:
    marketplace_total = sum(
        (ml.revenue_est or 0) for ml in company.marketplace_listings
    )
    if marketplace_total > 0:
        return marketplace_total

    fin = company.financial_reports
    if not fin:
        return 0.0
    latest = max(fin, key=lambda r: r.period)
    revenue = latest.revenue or 0
    adoption = compute_adoption_score(company)
    return revenue * adoption * 0.15


def compute_digital_va(
    online_revenue: float,
    gross_margin: float | None,
    adoption_score: float,
) -> float:
    margin = gross_margin or 0.25
    cost_savings = online_revenue * 0.05 * adoption_score
    digital_investment = online_revenue * 0.02
    return online_revenue * margin + cost_savings - digital_investment


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
