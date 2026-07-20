"""Task #18 — Benchmark Module 5 service tests (honest peer percentiles)."""

from __future__ import annotations

from datetime import date

from pytest import approx

from backend.app.models import Company, FinancialReport
from backend.app.schemas import BenchmarkInput
from backend.app.services import benchmark_service as svc


EXPENDITURE_KEYS = (
    "expenditure_related_ratio",
    "purchase_goods_share",
    "rental_cost_share",
    "remuneration_share",
)


def _ral_like_input(**overrides) -> BenchmarkInput:
    base = dict(
        vsic_code="2740",
        operating_revenue=5_200_000_000_000,
        profit_before_tax=420_000_000_000,
        employees=3200,
        total_assets=6_800_000_000_000,
        total_equity=3_200_000_000_000,
        current_assets=3_100_000_000_000,
        current_liabilities=2_100_000_000_000,
        operating_expenses=4_000_000_000_000,
        cost_of_goods=3_200_000_000_000,
        rental_cost=85_000_000_000,
        remuneration=680_000_000_000,
    )
    base.update(overrides)
    return BenchmarkInput(**base)


def test_compute_ratios_from_period_end_bctc():
    ratios = svc.compute_benchmark_ratios(_ral_like_input())
    assert ratios["roa"] == approx(420_000_000_000 / 6_800_000_000_000)
    assert ratios["roe"] == approx(420_000_000_000 / 3_200_000_000_000)
    assert ratios["current_ratio"] == approx(3_100_000_000_000 / 2_100_000_000_000)
    assert ratios["equity_ratio"] == approx(3_200_000_000_000 / 6_800_000_000_000)
    assert ratios["revenue_per_worker"] == approx(5_200_000_000_000 / 3200)
    # BITE expenditure block (operating_expenses present → non-null)
    assert ratios["expenditure_related_ratio"] == approx(4_000_000_000_000 / 5_200_000_000_000)
    assert ratios["purchase_goods_share"] == approx(3_200_000_000_000 / 4_000_000_000_000)
    assert ratios["rental_cost_share"] == approx(85_000_000_000 / 4_000_000_000_000)
    assert ratios["remuneration_share"] == approx(680_000_000_000 / 4_000_000_000_000)


def test_missing_expenditure_inputs_yield_null_shares():
    ratios = svc.compute_benchmark_ratios(
        _ral_like_input(
            operating_expenses=None,
            cost_of_goods=None,
            rental_cost=None,
            remuneration=None,
        )
    )
    for key in EXPENDITURE_KEYS:
        assert ratios[key] is None
    # Core ratios unchanged when only expenditure inputs missing
    assert ratios["roa"] == approx(420_000_000_000 / 6_800_000_000_000)
    assert ratios["roe"] == approx(420_000_000_000 / 3_200_000_000_000)
    assert ratios["current_ratio"] is not None
    assert ratios["equity_ratio"] is not None
    assert ratios["revenue_per_worker"] is not None
    assert ratios["profit_per_worker"] is not None


def test_partial_expenditure_inputs_null_only_affected_shares():
    """Shares need operating_expenses; expenditure_related needs expenses + revenue."""
    ratios = svc.compute_benchmark_ratios(
        _ral_like_input(
            operating_expenses=None,
            cost_of_goods=3_200_000_000_000,
            rental_cost=85_000_000_000,
            remuneration=680_000_000_000,
        )
    )
    for key in EXPENDITURE_KEYS:
        assert ratios[key] is None


def test_missing_balance_sheet_yields_null_core_ratios():
    ratios = svc.compute_benchmark_ratios(
        _ral_like_input(
            total_assets=None,
            total_equity=None,
            current_assets=None,
            current_liabilities=None,
        )
    )
    assert ratios["roa"] is None
    assert ratios["roe"] is None
    assert ratios["current_ratio"] is None
    assert ratios["equity_ratio"] is None
    assert ratios["revenue_per_worker"] is not None


def test_empty_peers_do_not_invent_percentile(db_session):
    result = svc.run_benchmark(db_session, _ral_like_input(vsic_code="3290"))
    assert result.peer_count == 0
    assert result.peer_scope == "vsic_division:32"
    assert "insufficient_peers" in result.warnings
    assert result.percentiles.get("roa") is None
    assert result.percentiles.get("roe") is None
    assert result.industry_averages.get("roa") is None
    assert result.comparison.get("roa") == "insufficient_peers"
    assert all(v is None for v in result.percentiles.values())
    for key in EXPENDITURE_KEYS:
        assert result.percentiles.get(key) is None
        assert result.industry_averages.get(key) is None
        assert result.comparison.get(key) == "insufficient_peers"
        # User ratios still computed; never fake a 50th percentile
        assert getattr(result, key) is not None


def test_peers_same_vsic_division_compute_percentile(peers_division_27):
    result = svc.run_benchmark(peers_division_27, _ral_like_input())
    assert result.peer_count == 2
    assert result.peer_scope == "vsic_division:27"
    assert "prototype_listed_sample" in result.warnings
    assert "small_peer_sample" in result.warnings
    assert result.percentiles["roa"] is not None
    assert 0 <= result.percentiles["roa"] <= 100
    assert result.industry_averages["roa"] is not None
    assert result.comparison["roa"] in {"above_average", "below_average", "average"}


def test_peers_with_cost_fields_yield_expenditure_industry_averages(peers_division_27):
    result = svc.run_benchmark(peers_division_27, _ral_like_input())
    # RAL: 4e12/5.2e12 ; REE: 6e12/8e12
    ral_exp = 4_000_000_000_000 / 5_200_000_000_000
    ree_exp = 6_000_000_000_000 / 8_000_000_000_000
    assert result.industry_averages["expenditure_related_ratio"] == approx(
        round((ral_exp + ree_exp) / 2, 4)
    )
    ral_cog = 3_200_000_000_000 / 4_000_000_000_000
    ree_cog = 4_500_000_000_000 / 6_000_000_000_000
    assert result.industry_averages["purchase_goods_share"] == approx(
        round((ral_cog + ree_cog) / 2, 4)
    )
    ral_rent = 85_000_000_000 / 4_000_000_000_000
    ree_rent = 120_000_000_000 / 6_000_000_000_000
    assert result.industry_averages["rental_cost_share"] == approx(
        round((ral_rent + ree_rent) / 2, 4)
    )
    ral_rem = 680_000_000_000 / 4_000_000_000_000
    ree_rem = 900_000_000_000 / 6_000_000_000_000
    assert result.industry_averages["remuneration_share"] == approx(
        round((ral_rem + ree_rem) / 2, 4)
    )
    for key in EXPENDITURE_KEYS:
        assert result.percentiles[key] is not None
        assert 0 <= result.percentiles[key] <= 100
        assert result.comparison[key] in {"above_average", "below_average", "average"}


def test_prefill_maps_expenditure_cost_fields(peers_division_27):
    payload = svc.load_input_from_company(peers_division_27, "RAL")
    assert payload is not None
    assert payload.operating_expenses == 4_000_000_000_000
    assert payload.cost_of_goods == 3_200_000_000_000
    assert payload.rental_cost == 85_000_000_000
    assert payload.remuneration == 680_000_000_000


def test_null_employees_excluded_from_worker_peer_population(peers_division_27, db_session):
    company = Company(stock_code="LIT", name="Lighting Co", vsic_code="2740", exchange="HOSE")
    db_session.add(company)
    db_session.flush()
    db_session.add(
        FinancialReport(
            company_id=company.id,
            period=date(2025, 12, 31),
            revenue=1_000_000_000_000,
            profit_before_tax=100_000_000_000,
            total_assets=2_000_000_000_000,
            total_equity=1_000_000_000_000,
            current_assets=800_000_000_000,
            current_liabilities=400_000_000_000,
            employees=None,
        )
    )
    db_session.commit()

    reports = svc.get_industry_financials(db_session, "2740")
    assert len(reports) == 3
    populations = svc.build_peer_populations(reports)
    assert len(populations["roa"]) == 3
    assert len(populations["revenue_per_worker"]) == 2


def test_prefill_requires_complete_bctc(peers_division_27):
    payload = svc.load_input_from_company(peers_division_27, "RAL")
    assert payload is not None
    assert payload.stock_code == "RAL"
    assert payload.vsic_code == "2740"
    assert payload.employees == 3200
    assert svc.load_input_from_company(peers_division_27, "NOPE") is None


def test_prefill_skips_incomplete_newer_quarterly(peers_division_27, db_session):
    """CafeF quarterlies can outrank annual by period but lack employees."""
    company = db_session.query(Company).filter(Company.stock_code == "RAL").one()
    db_session.add(
        FinancialReport(
            company_id=company.id,
            period=date(2026, 3, 31),
            report_type="quarterly",
            revenue=1_800_000_000_000,
            profit_before_tax=130_000_000_000,
            employees=None,
            cost_of_goods=1_300_000_000_000,
        )
    )
    db_session.commit()

    payload = svc.load_input_from_company(db_session, "RAL")
    assert payload is not None
    assert payload.employees == 3200
    assert payload.operating_revenue == 5_200_000_000_000

    reports = svc.get_industry_financials(db_session, "2740")
    ral_peer = next(r for r in reports if r.company_id == company.id)
    assert ral_peer.period == date(2025, 12, 31)
    assert ral_peer.report_type == "annual"


def test_singleton_peer_warns_small_sample(singleton_peer):
    result = svc.run_benchmark(
        singleton_peer,
        _ral_like_input(
            vsic_code="2410",
            operating_revenue=100_000_000_000_000,
            profit_before_tax=10_000_000_000_000,
            employees=30000,
            total_assets=180_000_000_000_000,
            total_equity=90_000_000_000_000,
            current_assets=70_000_000_000_000,
            current_liabilities=35_000_000_000_000,
        ),
    )
    assert result.peer_count == 1
    assert "small_peer_sample" in result.warnings
    assert result.percentiles["roa"] is not None
