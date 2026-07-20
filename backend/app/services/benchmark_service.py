"""SingStat BITE-style firm benchmark against seeded listed peers.

Peers = latest annual BCTC among companies sharing the same VSIC 2-digit
division. Percentiles are never invented: missing peer samples yield null
plus an explicit warning (not a fake 50th percentile).
"""

from __future__ import annotations

import statistics

from sqlalchemy.orm import Session, joinedload

from backend.app.models import Company, FinancialReport
from backend.app.schemas import BenchmarkInput, BenchmarkResult

METRIC_KEYS = (
    "roa",
    "roe",
    "current_ratio",
    "equity_ratio",
    "revenue_per_worker",
    "profit_per_worker",
    # SingStat BITE expenditure block (form "Of which" → ratios)
    "expenditure_related_ratio",  # operating_expenses / operating_revenue
    "purchase_goods_share",  # cost_of_goods / operating_expenses
    "rental_cost_share",  # rental_cost / operating_expenses
    "remuneration_share",  # remuneration / operating_expenses
)

# Prototype honesty: listed seed sample is tiny; surface this in API/UI.
PROTOTYPE_WARNING = "prototype_listed_sample"
INSUFFICIENT_PEERS_WARNING = "insufficient_peers"
SMALL_SAMPLE_WARNING = "small_peer_sample"
SMALL_SAMPLE_THRESHOLD = 3


def _safe_div(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _percentile(value: float, population: list[float]) -> float | None:
    """Empirical percentile = share of peers with ratio ≤ value.

    Returns None when there is no peer sample — never invents a midpoint.
    """
    if not population:
        return None
    below = sum(1 for p in population if p <= value)
    return round(below / len(population) * 100, 1)


def compute_benchmark_ratios(data: BenchmarkInput) -> dict[str, float | None]:
    return {
        "roa": _safe_div(data.profit_before_tax, data.total_assets),
        "roe": _safe_div(data.profit_before_tax, data.total_equity),
        "current_ratio": _safe_div(data.current_assets, data.current_liabilities),
        "equity_ratio": _safe_div(data.total_equity, data.total_assets),
        "revenue_per_worker": _safe_div(data.operating_revenue, float(data.employees)),
        "profit_per_worker": _safe_div(data.profit_before_tax, float(data.employees)),
        "expenditure_related_ratio": _safe_div(data.operating_expenses, data.operating_revenue),
        "purchase_goods_share": _safe_div(data.cost_of_goods, data.operating_expenses),
        "rental_cost_share": _safe_div(data.rental_cost, data.operating_expenses),
        "remuneration_share": _safe_div(data.remuneration, data.operating_expenses),
    }


def _ratios_from_report(report: FinancialReport) -> dict[str, float | None]:
    """Peer ratios from BCTC fields only — null fields stay null (no invent)."""
    return {
        "roa": _safe_div(report.profit_before_tax, report.total_assets),
        "roe": _safe_div(report.profit_before_tax, report.total_equity),
        "current_ratio": _safe_div(report.current_assets, report.current_liabilities),
        "equity_ratio": _safe_div(report.total_equity, report.total_assets),
        "revenue_per_worker": _safe_div(report.revenue, report.employees),
        "profit_per_worker": _safe_div(report.profit_before_tax, report.employees),
        "expenditure_related_ratio": _safe_div(report.operating_expenses, report.revenue),
        "purchase_goods_share": _safe_div(report.cost_of_goods, report.operating_expenses),
        "rental_cost_share": _safe_div(report.rental_cost, report.operating_expenses),
        "remuneration_share": _safe_div(report.remuneration, report.operating_expenses),
    }


def vsic_division_prefix(vsic_code: str) -> str:
    return vsic_code[:2] if len(vsic_code) >= 2 else vsic_code


def get_industry_financials(db: Session, vsic_code: str) -> list[FinancialReport]:
    prefix = vsic_division_prefix(vsic_code)
    companies = (
        db.query(Company)
        .filter(Company.vsic_code.startswith(prefix))
        .options(joinedload(Company.financial_reports))
        .all()
    )
    reports: list[FinancialReport] = []
    for company in companies:
        if company.financial_reports:
            latest = max(company.financial_reports, key=lambda r: r.period)
            reports.append(latest)
    return reports


def _empty_populations() -> dict[str, list[float]]:
    return {key: [] for key in METRIC_KEYS}


def build_peer_populations(reports: list[FinancialReport]) -> dict[str, list[float]]:
    populations = _empty_populations()
    for report in reports:
        computed = _ratios_from_report(report)
        for key, value in computed.items():
            if value is not None:
                populations[key].append(value)
    return populations


def compute_industry_averages(populations: dict[str, list[float]]) -> dict[str, float | None]:
    return {
        key: round(statistics.mean(values), 4) if values else None
        for key, values in populations.items()
    }


def _build_warnings(peer_count: int, populations: dict[str, list[float]]) -> list[str]:
    warnings: list[str] = []
    if peer_count == 0 or all(not pop for pop in populations.values()):
        warnings.append(INSUFFICIENT_PEERS_WARNING)
        return warnings

    warnings.append(PROTOTYPE_WARNING)
    if peer_count < SMALL_SAMPLE_THRESHOLD:
        warnings.append(SMALL_SAMPLE_WARNING)
    return warnings


def compare_to_industry(
    user_ratios: dict[str, float | None],
    industry_avgs: dict[str, float | None],
    industry_populations: dict[str, list[float]],
    *,
    peer_count: int,
    peer_scope: str,
) -> BenchmarkResult:
    percentiles: dict[str, float | None] = {}
    comparison: dict[str, str] = {}

    for metric, value in user_ratios.items():
        if value is None:
            continue
        pop = industry_populations.get(metric, [])
        pct = _percentile(value, pop)
        percentiles[metric] = pct

        avg = industry_avgs.get(metric)
        if pct is None or avg is None:
            comparison[metric] = "insufficient_peers"
        elif value > avg * 1.1:
            comparison[metric] = "above_average"
        elif value < avg * 0.9:
            comparison[metric] = "below_average"
        else:
            comparison[metric] = "average"

    return BenchmarkResult(
        roa=user_ratios.get("roa"),
        roe=user_ratios.get("roe"),
        current_ratio=user_ratios.get("current_ratio"),
        equity_ratio=user_ratios.get("equity_ratio"),
        revenue_per_worker=user_ratios.get("revenue_per_worker"),
        profit_per_worker=user_ratios.get("profit_per_worker"),
        expenditure_related_ratio=user_ratios.get("expenditure_related_ratio"),
        purchase_goods_share=user_ratios.get("purchase_goods_share"),
        rental_cost_share=user_ratios.get("rental_cost_share"),
        remuneration_share=user_ratios.get("remuneration_share"),
        percentiles=percentiles,
        industry_averages=industry_avgs,
        comparison=comparison,
        peer_count=peer_count,
        peer_scope=peer_scope,
        warnings=_build_warnings(peer_count, industry_populations),
    )


def run_benchmark(db: Session, data: BenchmarkInput) -> BenchmarkResult:
    user_ratios = compute_benchmark_ratios(data)
    prefix = vsic_division_prefix(data.vsic_code)
    reports = get_industry_financials(db, data.vsic_code)
    populations = build_peer_populations(reports)
    industry_avgs = compute_industry_averages(populations)
    return compare_to_industry(
        user_ratios,
        industry_avgs,
        populations,
        peer_count=len(reports),
        peer_scope=f"vsic_division:{prefix}",
    )


def load_input_from_company(db: Session, stock_code: str) -> BenchmarkInput | None:
    """Optional helper: prefill form from a seeded listed company's latest BCTC."""
    company = (
        db.query(Company)
        .filter(Company.stock_code == stock_code.upper())
        .options(joinedload(Company.financial_reports))
        .first()
    )
    if company is None or not company.financial_reports:
        return None
    latest = max(company.financial_reports, key=lambda r: r.period)
    if latest.revenue is None or latest.profit_before_tax is None or latest.employees is None:
        return None
    return BenchmarkInput(
        stock_code=company.stock_code,
        vsic_code=company.vsic_code,
        operating_revenue=latest.revenue,
        profit_before_tax=latest.profit_before_tax,
        employees=latest.employees,
        operating_expenses=latest.operating_expenses,
        cost_of_goods=latest.cost_of_goods,
        rental_cost=latest.rental_cost,
        remuneration=latest.remuneration,
        total_assets=latest.total_assets,
        total_equity=latest.total_equity,
        current_assets=latest.current_assets,
        current_liabilities=latest.current_liabilities,
    )
