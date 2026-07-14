from datetime import date

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from backend.app.models import (
    Company,
    DigitalMetric,
    GsoMacro,
    ModelPrediction,
    ModelRegistry,
    OecdIndicator,
)
from backend.app.schemas import DashboardSummary


def get_dashboard_summary(db: Session) -> DashboardSummary:
    companies = db.query(Company).all()
    companies_with_ecom = sum(1 for c in companies if c.has_ecommerce_site)

    latest_iip = (
        db.query(GsoMacro)
        .filter(GsoMacro.indicator_code == "IIP_C", GsoMacro.vsic_code == "C")
        .order_by(desc(GsoMacro.period))
        .first()
    )

    prev_iip = None
    if latest_iip:
        prev_iip = (
            db.query(GsoMacro)
            .filter(
                GsoMacro.indicator_code == "IIP_C",
                GsoMacro.vsic_code == "C",
                GsoMacro.period < latest_iip.period,
            )
            .order_by(desc(GsoMacro.period))
            .first()
        )

    iip_growth = None
    if latest_iip and prev_iip and prev_iip.value:
        iip_growth = (latest_iip.value - prev_iip.value) / prev_iip.value * 100

    avg_adoption = db.query(func.avg(DigitalMetric.digital_adoption_score)).scalar()
    total_va = db.query(func.sum(DigitalMetric.digital_va_contribution)).scalar()

    active_models = (
        db.query(ModelRegistry).filter(ModelRegistry.is_active.is_(True)).all()
    )
    model_metrics = {
        m.model_name: m.metrics or {} for m in active_models
    }

    return DashboardSummary(
        iip_latest=latest_iip.value if latest_iip else None,
        iip_growth_pct=round(iip_growth, 2) if iip_growth is not None else None,
        total_companies=len(companies),
        companies_with_ecommerce=companies_with_ecom,
        avg_digital_adoption=round(avg_adoption, 2) if avg_adoption else None,
        total_digital_va=round(total_va, 2) if total_va else None,
        latest_period=latest_iip.period if latest_iip else None,
        model_metrics=model_metrics,
    )


def get_iip_timeseries(db: Session, vsic_code: str = "C") -> list[dict]:
    rows = (
        db.query(GsoMacro)
        .filter(GsoMacro.indicator_code == "IIP_C", GsoMacro.vsic_code == vsic_code)
        .order_by(GsoMacro.period)
        .all()
    )
    return [{"period": r.period.isoformat(), "value": r.value} for r in rows]


def get_industry_heatmap(db: Session) -> list[dict]:
    subquery = (
        db.query(
            DigitalMetric.company_id,
            func.max(DigitalMetric.digital_va_contribution).label("va"),
        )
        .group_by(DigitalMetric.company_id)
        .subquery()
    )

    results = (
        db.query(Company.vsic_code, func.sum(subquery.c.va).label("total_va"))
        .join(subquery, Company.id == subquery.c.company_id)
        .group_by(Company.vsic_code)
        .all()
    )
    return [{"vsic_code": r.vsic_code, "digital_va": r.total_va or 0} for r in results]


def get_oecd_vs_gso(db: Session) -> dict:
    gso = (
        db.query(GsoMacro)
        .filter(GsoMacro.indicator_code == "IIP_C", GsoMacro.vsic_code == "C")
        .order_by(GsoMacro.period)
        .limit(24)
        .all()
    )
    oecd = (
        db.query(OecdIndicator)
        .filter(OecdIndicator.indicator_code == "MEI_IP")
        .order_by(OecdIndicator.period)
        .limit(24)
        .all()
    )
    return {
        "gso": [{"period": r.period.isoformat(), "value": r.value} for r in gso],
        "oecd": [{"period": r.period.isoformat(), "value": r.value} for r in oecd],
    }
