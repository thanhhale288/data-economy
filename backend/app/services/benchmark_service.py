import statistics
from typing import Any

from sqlalchemy.orm import Session, joinedload

from backend.app.models import Company, FinancialReport
from backend.app.schemas import BenchmarkInput, BenchmarkResult


def _safe_div(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _percentile(value: float, population: list[float]) -> float:
    if not population:
        return 50.0
    below = sum(1 for p in population if p <= value)
    return round(below / len(population) * 100, 1)


def compute_benchmark_ratios(data: BenchmarkInput) -> dict[str, float | None]:
    return {
        "roa": _safe_div(data.profit_before_tax, data.total_assets),
        "roe": _safe_div(data.profit_before_tax, data.total_equity),
        "current_ratio": _safe_div(data.current_assets, data.current_liabilities),
        "equity_ratio": _safe_div(data.total_equity, data.total_assets),
        "revenue_per_worker": _safe_div(data.operating_revenue, data.employees),
        "profit_per_worker": _safe_div(data.profit_before_tax, data.employees),
    }


def get_industry_financials(db: Session, vsic_code: str) -> list[FinancialReport]:
    prefix = vsic_code[:2] if len(vsic_code) >= 2 else vsic_code
    companies = (
        db.query(Company)
        .filter(Company.vsic_code.startswith(prefix))
        .options(joinedload(Company.financial_reports))
        .all()
    )
    reports: list[FinancialReport] = []
    for c in companies:
        if c.financial_reports:
            latest = max(c.financial_reports, key=lambda r: r.period)
            reports.append(latest)
    return reports


def compute_industry_averages(reports: list[FinancialReport]) -> dict[str, float]:
    ratios: dict[str, list[float]] = {
        "roa": [],
        "roe": [],
        "current_ratio": [],
        "equity_ratio": [],
        "revenue_per_worker": [],
        "profit_per_worker": [],
    }
    for r in reports:
        inp = BenchmarkInput(
            vsic_code="C",
            operating_revenue=r.revenue or 0,
            profit_before_tax=r.profit_before_tax or 0,
            employees=r.employees or 1,
            total_assets=r.total_assets,
            total_equity=r.total_equity,
            current_assets=r.current_assets,
            current_liabilities=r.current_liabilities,
        )
        computed = compute_benchmark_ratios(inp)
        for k, v in computed.items():
            if v is not None:
                ratios[k].append(v)

    return {k: round(statistics.mean(v), 4) if v else 0 for k, v in ratios.items()}


def compare_to_industry(
    user_ratios: dict[str, float | None],
    industry_avgs: dict[str, float],
    industry_populations: dict[str, list[float]],
) -> BenchmarkResult:
    percentiles: dict[str, float] = {}
    comparison: dict[str, str] = {}

    for metric, value in user_ratios.items():
        if value is None:
            continue
        pop = industry_populations.get(metric, [])
        pct = _percentile(value, pop) if pop else 50.0
        percentiles[metric] = pct

        avg = industry_avgs.get(metric, 0)
        if avg == 0:
            comparison[metric] = "neutral"
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
        percentiles=percentiles,
        industry_averages=industry_avgs,
        comparison=comparison,
    )


def run_benchmark(db: Session, data: BenchmarkInput) -> BenchmarkResult:
    user_ratios = compute_benchmark_ratios(data)
    reports = get_industry_financials(db, data.vsic_code)
    industry_avgs = compute_industry_averages(reports)

    populations: dict[str, list[float]] = {
        "roa": [],
        "roe": [],
        "current_ratio": [],
        "equity_ratio": [],
        "revenue_per_worker": [],
        "profit_per_worker": [],
    }
    for r in reports:
        inp = BenchmarkInput(
            vsic_code=data.vsic_code,
            operating_revenue=r.revenue or 0,
            profit_before_tax=r.profit_before_tax or 0,
            employees=r.employees or 1,
            total_assets=r.total_assets,
            total_equity=r.total_equity,
            current_assets=r.current_assets,
            current_liabilities=r.current_liabilities,
        )
        computed = compute_benchmark_ratios(inp)
        for k, v in computed.items():
            if v is not None:
                populations[k].append(v)

    return compare_to_industry(user_ratios, industry_avgs, populations)
