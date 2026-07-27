"""SingStat BITE-style firm benchmark against seeded listed peers.

Peers = latest annual BCTC among companies sharing the same VSIC 2-digit
division. Percentiles are never invented: missing peer samples yield null
plus an explicit warning (not a fake 50th percentile).
"""

from __future__ import annotations

import statistics

from sqlalchemy.orm import Session, joinedload

from backend.app.models import Company, DigitalMetric, FinancialReport
from backend.app.schemas import BenchmarkInput, BenchmarkResult, DigitalBenchmark

METRIC_KEYS = (
    "roa",
    "roe",
    "current_ratio",
    "equity_ratio",
    "revenue_per_worker",
    "profit_per_worker",
    "profit_margin",
    "asset_turnover",
    "debt_to_equity",
    # SingStat BITE expenditure block (form "Of which" → ratios)
    "expenditure_related_ratio",  # operating_expenses / operating_revenue
    "purchase_goods_share",  # cost_of_goods / operating_expenses
    "rental_cost_share",  # rental_cost / operating_expenses
    "remuneration_share",  # remuneration / operating_expenses
)

# Metrics where a higher value usually means more risk / weaker position.
HIGHER_IS_WORSE = frozenset({"debt_to_equity"})

# Prototype honesty: listed seed sample is tiny; surface this in API/UI.
PROTOTYPE_WARNING = "prototype_listed_sample"
INSUFFICIENT_PEERS_WARNING = "insufficient_peers"
SMALL_SAMPLE_WARNING = "small_peer_sample"
SMALL_SAMPLE_THRESHOLD = 3
# P25/P50/P75 only when enough peer points — never invent a band on tiny n.
QUARTILE_MIN_PEERS = 4


def _safe_div(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _debt_to_equity(total_assets: float | None, total_equity: float | None) -> float | None:
    """(Assets − Equity) / Equity ≈ total liabilities / equity. Null if incomplete."""
    if total_assets is None or total_equity is None or total_equity == 0:
        return None
    return (total_assets - total_equity) / total_equity


def _percentile(value: float, population: list[float]) -> float | None:
    """Empirical percentile = share of peers with ratio ≤ value.

    Returns None when there is no peer sample — never invents a midpoint.
    """
    if not population:
        return None
    below = sum(1 for p in population if p <= value)
    return round(below / len(population) * 100, 1)


def _peer_quartiles(population: list[float]) -> dict[str, float] | None:
    """P25 / median / P75 of peer values. None when n < QUARTILE_MIN_PEERS."""
    if len(population) < QUARTILE_MIN_PEERS:
        return None
    ordered = sorted(population)
    q1, _q2, q3 = statistics.quantiles(ordered, n=4, method="inclusive")
    return {
        "p25": round(q1, 6),
        "p50": round(statistics.median(ordered), 6),
        "p75": round(q3, 6),
    }


def compute_benchmark_ratios(data: BenchmarkInput) -> dict[str, float | None]:
    return {
        "roa": _safe_div(data.profit_before_tax, data.total_assets),
        "roe": _safe_div(data.profit_before_tax, data.total_equity),
        "current_ratio": _safe_div(data.current_assets, data.current_liabilities),
        "equity_ratio": _safe_div(data.total_equity, data.total_assets),
        "revenue_per_worker": _safe_div(data.operating_revenue, float(data.employees)),
        "profit_per_worker": _safe_div(data.profit_before_tax, float(data.employees)),
        "profit_margin": _safe_div(data.profit_before_tax, data.operating_revenue),
        "asset_turnover": _safe_div(data.operating_revenue, data.total_assets),
        "debt_to_equity": _debt_to_equity(data.total_assets, data.total_equity),
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
        "profit_margin": _safe_div(report.profit_before_tax, report.revenue),
        "asset_turnover": _safe_div(report.revenue, report.total_assets),
        "debt_to_equity": _debt_to_equity(report.total_assets, report.total_equity),
        "expenditure_related_ratio": _safe_div(report.operating_expenses, report.revenue),
        "purchase_goods_share": _safe_div(report.cost_of_goods, report.operating_expenses),
        "rental_cost_share": _safe_div(report.rental_cost, report.operating_expenses),
        "remuneration_share": _safe_div(report.remuneration, report.operating_expenses),
    }


def vsic_division_prefix(vsic_code: str) -> str:
    return vsic_code[:2] if len(vsic_code) >= 2 else vsic_code


def _latest_annual_report(reports: list[FinancialReport]) -> FinancialReport | None:
    """Prefer latest annual BCTC; CafeF quarterlies often lack employees/opex."""
    annual = [r for r in reports if (r.report_type or "annual") == "annual"]
    pool = annual or reports
    if not pool:
        return None
    return max(pool, key=lambda r: r.period)


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
        latest = _latest_annual_report(company.financial_reports or [])
        if latest is not None:
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


def compute_industry_quartiles(
    populations: dict[str, list[float]],
) -> dict[str, dict[str, float] | None]:
    return {key: _peer_quartiles(values) for key, values in populations.items()}


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
    industry_quartiles = compute_industry_quartiles(industry_populations)

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
        profit_margin=user_ratios.get("profit_margin"),
        asset_turnover=user_ratios.get("asset_turnover"),
        debt_to_equity=user_ratios.get("debt_to_equity"),
        expenditure_related_ratio=user_ratios.get("expenditure_related_ratio"),
        purchase_goods_share=user_ratios.get("purchase_goods_share"),
        rental_cost_share=user_ratios.get("rental_cost_share"),
        remuneration_share=user_ratios.get("remuneration_share"),
        percentiles=percentiles,
        industry_averages=industry_avgs,
        industry_quartiles=industry_quartiles,
        comparison=comparison,
        peer_count=peer_count,
        peer_scope=peer_scope,
        warnings=_build_warnings(peer_count, industry_populations),
    )


DIGITAL_METRIC_KEYS = ("digital_adoption_score", "online_revenue_ratio")


def _latest_digital_metric(company: Company) -> DigitalMetric | None:
    metrics = company.digital_metrics or []
    if not metrics:
        return None
    return max(metrics, key=lambda m: m.period)


def _digital_values(company: Company) -> dict[str, float | None]:
    """Adoption + online revenue share for one company (null stays null).

    ``online_revenue_ratio`` falls back to online estimate ÷ BCTC revenue when
    the stored ratio is missing — both sides are real stored values.
    """
    metric = _latest_digital_metric(company)
    if metric is None:
        return {key: None for key in DIGITAL_METRIC_KEYS}

    ratio = metric.online_revenue_ratio
    if ratio is None:
        report = _latest_annual_report(company.financial_reports or [])
        ratio = _safe_div(metric.online_revenue_est, report.revenue if report else None)
    return {
        "digital_adoption_score": metric.digital_adoption_score,
        "online_revenue_ratio": ratio,
    }


def build_digital_benchmark(db: Session, data: BenchmarkInput) -> DigitalBenchmark:
    """Compare a listed firm's digital footprint to same-division peers."""
    if not data.stock_code:
        return DigitalBenchmark(status="no_stock_code")

    prefix = vsic_division_prefix(data.vsic_code)
    companies = (
        db.query(Company)
        .filter(Company.vsic_code.startswith(prefix))
        .options(
            joinedload(Company.digital_metrics),
            joinedload(Company.financial_reports),
        )
        .all()
    )

    target = next(
        (c for c in companies if c.stock_code.upper() == data.stock_code.upper()),
        None,
    )
    if target is None:
        return DigitalBenchmark(status="no_company", stock_code=data.stock_code.upper())

    firm_values = _digital_values(target)
    if all(v is None for v in firm_values.values()):
        return DigitalBenchmark(status="no_metrics", stock_code=target.stock_code)

    populations: dict[str, list[float]] = {key: [] for key in DIGITAL_METRIC_KEYS}
    peer_ids = set()
    for company in companies:
        if company.id == target.id:
            continue
        values = _digital_values(company)
        has_any = False
        for key, value in values.items():
            if value is not None:
                populations[key].append(value)
                has_any = True
        if has_any:
            peer_ids.add(company.id)

    averages = compute_industry_averages(populations)
    quartiles = compute_industry_quartiles(populations)
    percentiles: dict[str, float | None] = {}
    comparison: dict[str, str] = {}
    for key, value in firm_values.items():
        if value is None:
            continue
        pct = _percentile(value, populations[key])
        percentiles[key] = pct
        avg = averages.get(key)
        if pct is None or avg is None:
            comparison[key] = "insufficient_peers"
        elif value > avg * 1.1:
            comparison[key] = "above_average"
        elif value < avg * 0.9:
            comparison[key] = "below_average"
        else:
            comparison[key] = "average"

    latest = _latest_digital_metric(target)
    return DigitalBenchmark(
        status="ok",
        stock_code=target.stock_code,
        period=latest.period if latest else None,
        metrics=firm_values,
        percentiles=percentiles,
        industry_averages=averages,
        industry_quartiles=quartiles,
        comparison=comparison,
        peer_count=len(peer_ids),
    )


def run_benchmark(db: Session, data: BenchmarkInput) -> BenchmarkResult:
    user_ratios = compute_benchmark_ratios(data)
    prefix = vsic_division_prefix(data.vsic_code)
    reports = get_industry_financials(db, data.vsic_code)
    populations = build_peer_populations(reports)
    industry_avgs = compute_industry_averages(populations)
    result = compare_to_industry(
        user_ratios,
        industry_avgs,
        populations,
        peer_count=len(reports),
        peer_scope=f"vsic_division:{prefix}",
    )
    result.digital = build_digital_benchmark(db, data)
    return result


def load_input_from_company(db: Session, stock_code: str) -> BenchmarkInput | None:
    """Optional helper: prefill form from a listed company's latest annual BCTC.

    Skips incomplete CafeF quarterlies (often missing employees) so a newer
    partial row does not 404 over a complete seeded annual.
    """
    company = (
        db.query(Company)
        .filter(Company.stock_code == stock_code.upper())
        .options(joinedload(Company.financial_reports))
        .first()
    )
    if company is None or not company.financial_reports:
        return None

    def _is_complete(report: FinancialReport) -> bool:
        return (
            report.revenue is not None
            and report.profit_before_tax is not None
            and report.employees is not None
        )

    annual = [
        r
        for r in company.financial_reports
        if (r.report_type or "annual") == "annual" and _is_complete(r)
    ]
    complete = annual or [r for r in company.financial_reports if _is_complete(r)]
    if not complete:
        return None
    latest = max(complete, key=lambda r: r.period)
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
