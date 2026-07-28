"""Dashboard ngành (Module 1) — aggregate GSO IIP, VA_C, Digital VA, OECD peer, registry."""

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
# National manufacturing VA from NSO SDMX (Task #38). Never invent / never = Σ Digital VA.
_GSO_VA_C = "VA_C"
_GSO_VA_C_NOMINAL = "VA_C_NOMINAL"
_GSO_VA_CODES = frozenset({_GSO_VA_C, _GSO_VA_C_NOMINAL})


def _latest_gso(
    db: Session, indicator_code: str, vsic_code: str = "C"
) -> GsoMacro | None:
    return (
        db.query(GsoMacro)
        .filter(
            GsoMacro.indicator_code == indicator_code,
            GsoMacro.vsic_code == vsic_code,
        )
        .order_by(desc(GsoMacro.period))
        .first()
    )


def _mom_growth(db: Session, latest: GsoMacro | None) -> float | None:
    if not latest:
        return None
    prev = (
        db.query(GsoMacro)
        .filter(
            GsoMacro.indicator_code == latest.indicator_code,
            GsoMacro.vsic_code == latest.vsic_code,
            GsoMacro.period < latest.period,
        )
        .order_by(desc(GsoMacro.period))
        .first()
    )
    if not prev or not prev.value:
        return None
    return (latest.value - prev.value) / prev.value * 100


def _yoy_growth(db: Session, latest: GsoMacro | None) -> float | None:
    """Same calendar month one year earlier — exact period match, no interpolation."""
    if not latest:
        return None
    try:
        yoy_period = latest.period.replace(year=latest.period.year - 1)
    except ValueError:  # Feb 29 → fall back to Feb 28
        yoy_period = latest.period.replace(year=latest.period.year - 1, day=28)
    year_ago = (
        db.query(GsoMacro)
        .filter(
            GsoMacro.indicator_code == latest.indicator_code,
            GsoMacro.vsic_code == latest.vsic_code,
            GsoMacro.period == yoy_period,
        )
        .first()
    )
    if not year_ago or not year_ago.value:
        return None
    return (latest.value - year_ago.value) / year_ago.value * 100


def get_dashboard_summary(db: Session) -> DashboardSummary:
    companies = db.query(Company).all()
    companies_with_ecom = sum(1 for c in companies if c.has_ecommerce_site)

    latest_iip = _latest_gso(db, _GSO_IIP_CODE)
    iip_growth = _mom_growth(db, latest_iip)
    iip_yoy = _yoy_growth(db, latest_iip)

    latest_va = _latest_gso(db, _GSO_VA_C)
    va_growth = _mom_growth(db, latest_va)
    va_yoy = _yoy_growth(db, latest_va)
    latest_va_nominal = _latest_gso(db, _GSO_VA_C_NOMINAL)

    avg_adoption = db.query(func.avg(DigitalMetric.digital_adoption_score)).scalar()
    total_va = db.query(func.sum(DigitalMetric.digital_va_contribution)).scalar()
    companies_with_metrics = (
        db.query(func.count(func.distinct(DigitalMetric.company_id))).scalar() or 0
    )

    active_models = (
        db.query(ModelRegistry).filter(ModelRegistry.is_active.is_(True)).all()
    )
    model_metrics = {m.model_name: m.metrics or {} for m in active_models}
    preferred = preferred_forecast_model(db)

    return DashboardSummary(
        iip_latest=latest_iip.value if latest_iip else None,
        iip_growth_pct=round(iip_growth, 2) if iip_growth is not None else None,
        iip_yoy_pct=round(iip_yoy, 2) if iip_yoy is not None else None,
        total_companies=len(companies),
        companies_with_ecommerce=companies_with_ecom,
        companies_with_metrics=int(companies_with_metrics),
        avg_digital_adoption=round(avg_adoption, 2) if avg_adoption else None,
        total_digital_va=round(total_va, 2) if total_va else None,
        latest_period=latest_iip.period if latest_iip else None,
        model_metrics=model_metrics,
        preferred_forecast_model=preferred,
        va_c_latest=latest_va.value if latest_va else None,
        va_c_growth_pct=round(va_growth, 2) if va_growth is not None else None,
        va_c_yoy_pct=round(va_yoy, 2) if va_yoy is not None else None,
        va_c_period=latest_va.period if latest_va else None,
        va_c_unit=latest_va.unit if latest_va else None,
        va_c_source=latest_va.source if latest_va else None,
        va_c_nominal_latest=latest_va_nominal.value if latest_va_nominal else None,
        va_c_nominal_period=latest_va_nominal.period if latest_va_nominal else None,
        va_c_nominal_unit=latest_va_nominal.unit if latest_va_nominal else None,
        va_c_nominal_source=latest_va_nominal.source if latest_va_nominal else None,
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


def get_va_timeseries(
    db: Session,
    indicator_code: str = _GSO_VA_C,
    vsic_code: str = "C",
) -> list[dict]:
    """National manufacturing VA timeseries from gso_macro.

    Only ``VA_C`` / ``VA_C_NOMINAL``. Empty list when absent — never invent,
    never fill from IIP or firm-level Digital VA.
    """
    code = (indicator_code or _GSO_VA_C).strip().upper()
    if code not in _GSO_VA_CODES:
        return []
    rows = (
        db.query(GsoMacro)
        .filter(
            GsoMacro.indicator_code == code,
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
            "unit": r.unit,
            "indicator_code": r.indicator_code,
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
        .filter(subquery.c.va > 0)
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
            "OECD không có dữ liệu sản xuất công nghiệp của Việt Nam, "
            "nên biểu đồ dùng chỉ số khu vực Euro (EA20) làm đối sánh với IIP của GSO."
        )
        oecd_country = _OECD_PEER_COUNTRY
        oecd_source = oecd_rows[0].source if oecd_rows else "OECD_PEER"
    else:
        oecd_status = "missing"
        oecd_note = (
            "Chưa có dữ liệu OECD khu vực Euro (EA20) trong hệ thống — "
            "không hiển thị số ước lượng. Chạy crawl OECD (kèm peer) để bổ sung."
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
