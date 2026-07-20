"""Dashboard ngành (Module 1) — aggregate GSO IIP, Digital VA, OECD peer, registry."""

from __future__ import annotations

from datetime import date

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.app.models import (
    Company,
    DigitalMetric,
    GsoMacro,
    ModelRegistry,
    OecdIndicator,
    VsicCode,
)
from backend.app.schemas import DashboardSummary

# Peer MEI IP is EA20 only (ADR-0001). Never invent VNM MEI.
_OECD_PEER_COUNTRY = "EA20"
_OECD_MEI_CODE = "MEI_IP"
_GSO_IIP_CODE = "IIP_C"


def get_dashboard_summary(db: Session) -> DashboardSummary:
    companies = db.query(Company).all()
    companies_with_ecom = sum(1 for c in companies if c.has_ecommerce_site)

    latest_iip = (
        db.query(GsoMacro)
        .filter(GsoMacro.indicator_code == _GSO_IIP_CODE, GsoMacro.vsic_code == "C")
        .order_by(desc(GsoMacro.period))
        .first()
    )

    prev_iip = None
    if latest_iip:
        prev_iip = (
            db.query(GsoMacro)
            .filter(
                GsoMacro.indicator_code == _GSO_IIP_CODE,
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
    model_metrics = {m.model_name: m.metrics or {} for m in active_models}
    preferred = preferred_forecast_model(db)

    return DashboardSummary(
        iip_latest=latest_iip.value if latest_iip else None,
        iip_growth_pct=round(iip_growth, 2) if iip_growth is not None else None,
        total_companies=len(companies),
        companies_with_ecommerce=companies_with_ecom,
        avg_digital_adoption=round(avg_adoption, 2) if avg_adoption else None,
        total_digital_va=round(total_va, 2) if total_va else None,
        latest_period=latest_iip.period if latest_iip else None,
        model_metrics=model_metrics,
        preferred_forecast_model=preferred,
    )


def get_iip_timeseries(db: Session, vsic_code: str = "C") -> list[dict]:
    rows = (
        db.query(GsoMacro)
        .filter(
            GsoMacro.indicator_code == _GSO_IIP_CODE,
            GsoMacro.vsic_code == vsic_code,
        )
        .order_by(GsoMacro.period)
        .all()
    )
    return [
        {
            "period": r.period.isoformat(),
            "value": r.value,
            "source": r.source,
        }
        for r in rows
    ]


def get_industry_heatmap(db: Session) -> list[dict]:
    """Digital VA by VSIC class (4-digit) with labels for heatmap UI.

    Uses latest digital_va_contribution per company (max by period via
    subquery on max value is a demo proxy when multiple periods exist).
    """
    subquery = (
        db.query(
            DigitalMetric.company_id,
            func.max(DigitalMetric.digital_va_contribution).label("va"),
        )
        .group_by(DigitalMetric.company_id)
        .subquery()
    )

    results = (
        db.query(
            Company.vsic_code,
            func.sum(subquery.c.va).label("total_va"),
            func.count(Company.id).label("company_count"),
        )
        .join(subquery, Company.id == subquery.c.company_id)
        .group_by(Company.vsic_code)
        .all()
    )

    codes = [r.vsic_code for r in results]
    name_map: dict[str, str] = {}
    if codes:
        for vsic in db.query(VsicCode).filter(VsicCode.vsic_code.in_(codes)).all():
            name_map[vsic.vsic_code] = vsic.name_vi

    rows = [
        {
            "vsic_code": r.vsic_code,
            "vsic_name": name_map.get(r.vsic_code),
            "digital_va": float(r.total_va or 0),
            "company_count": int(r.company_count or 0),
            "division": (r.vsic_code[:2] if r.vsic_code and len(r.vsic_code) >= 2 else r.vsic_code),
        }
        for r in results
    ]
    rows.sort(key=lambda x: x["digital_va"], reverse=True)

    max_va = max((r["digital_va"] for r in rows), default=0.0)
    for r in rows:
        r["intensity"] = round(r["digital_va"] / max_va, 4) if max_va > 0 else 0.0
    return rows


def get_oecd_vs_gso(db: Session) -> dict:
    """Compare GSO IIP (VN) with OECD MEI_IP peer (EA20).

    If peer series is absent, return empty oecd + explicit missing status.
    Never invent peer values. Align by calendar period (not list index).
    """
    gso_rows = (
        db.query(GsoMacro)
        .filter(GsoMacro.indicator_code == _GSO_IIP_CODE, GsoMacro.vsic_code == "C")
        .order_by(GsoMacro.period)
        .all()
    )
    oecd_rows = (
        db.query(OecdIndicator)
        .filter(
            OecdIndicator.indicator_code == _OECD_MEI_CODE,
            OecdIndicator.country == _OECD_PEER_COUNTRY,
        )
        .order_by(OecdIndicator.period)
        .all()
    )

    gso = [
        {
            "period": r.period.isoformat(),
            "value": r.value,
            "source": r.source,
            "country": "VNM",
        }
        for r in gso_rows
    ]
    oecd = [
        {
            "period": r.period.isoformat(),
            "value": r.value,
            "source": r.source,
            "country": r.country,
        }
        for r in oecd_rows
    ]

    if oecd:
        oecd_status = "available"
        oecd_note = (
            "OECD MEI Industrial Production for peer EA20 (Euro area), "
            "source OECD_PEER — not Vietnam MEI (unavailable; ADR-0001)."
        )
        oecd_country = _OECD_PEER_COUNTRY
        oecd_source = oecd_rows[0].source if oecd_rows else "OECD_PEER"
    else:
        oecd_status = "missing"
        oecd_note = (
            "OECD MEI_IP peer (EA20) chưa có trong DB — không hiển thị số bịa. "
            "Chạy crawl OECD với include_peers, hoặc chấp nhận series_missing."
        )
        oecd_country = None
        oecd_source = None

    gso_by_period = {_period_key(r.period): r.value for r in gso_rows}
    oecd_by_period = {_period_key(r.period): r.value for r in oecd_rows}
    all_periods = sorted(set(gso_by_period) | set(oecd_by_period))
    aligned = [
        {
            "period": p,
            "gso": gso_by_period.get(p),
            "oecd": oecd_by_period.get(p),
        }
        for p in all_periods
    ]

    return {
        "gso": gso,
        "oecd": oecd,
        "aligned": aligned,
        "oecd_status": oecd_status,
        "oecd_note": oecd_note,
        "oecd_country": oecd_country,
        "oecd_source": oecd_source,
        "oecd_indicator": _OECD_MEI_CODE,
    }


def preferred_forecast_model(db: Session) -> str | None:
    """Pick an active registry model for dashboard forecast (lowest MAPE if present)."""
    active = (
        db.query(ModelRegistry).filter(ModelRegistry.is_active.is_(True)).all()
    )
    if not active:
        return None

    def mape_key(m: ModelRegistry) -> float:
        metrics = m.metrics or {}
        mape = metrics.get("mape")
        if mape is None:
            return float("inf")
        try:
            return float(mape)
        except (TypeError, ValueError):
            return float("inf")

    ranked = sorted(active, key=mape_key)
    return ranked[0].model_name


def _period_key(period: date) -> str:
    return period.isoformat()[:7]  # YYYY-MM for monthly align
