"""Epic 2 — sample expansion, source health, company filter/peers."""

from __future__ import annotations

from backend.app.models import FinancialReport, GsoMacro
from backend.app.schemas import BenchmarkInput
from backend.app.services import company_service, pipeline_service
from backend.app.services.benchmark_service import run_benchmark
from crawlers.companies.listed_companies import (
    ALLOWED_TICKERS,
    load_seed_companies,
    run_company_crawl,
)


def test_allowed_tickers_match_seed_file():
    seeds = load_seed_companies()
    assert len(ALLOWED_TICKERS) >= 25
    assert len(seeds) == len(ALLOWED_TICKERS)


def test_list_companies_vsic_division_filter(db_session, monkeypatch):
    from tests.companies.test_listed_companies import _patch_crawl_network

    _patch_crawl_network(monkeypatch)
    run_company_crawl(db_session, tickers=["RAL", "REE", "DQC", "GEE", "TYA"])
    rows = company_service.list_companies(db_session, vsic="27")
    codes = {r.stock_code for r in rows}
    assert codes >= {"RAL", "REE", "DQC", "GEE", "TYA"}


def test_company_detail_includes_peers(db_session, monkeypatch):
    from tests.companies.test_listed_companies import _patch_crawl_network

    _patch_crawl_network(monkeypatch)
    run_company_crawl(db_session, tickers=["RAL", "REE", "DQC"])
    detail = company_service.get_company(db_session, "RAL")
    assert detail is not None
    assert detail.vsic_division == "27"
    peer_codes = {p.stock_code for p in detail.peers}
    assert "REE" in peer_codes and "DQC" in peer_codes
    assert "RAL" not in peer_codes


def test_source_health_honest_when_empty(db_session):
    health = pipeline_service.get_source_health(db_session)
    by_src = {h["source"]: h for h in health}
    assert by_src["gso"]["status"] == "unavailable"
    assert by_src["oecd"]["status"] == "unavailable"


def test_source_health_gso_ok_and_monitor_sample_size(db_session, monkeypatch):
    from datetime import date

    from tests.companies.test_listed_companies import _patch_crawl_network

    _patch_crawl_network(monkeypatch)
    run_company_crawl(db_session, tickers=["RAL", "HPG"])
    db_session.add(
        GsoMacro(
            vsic_code="C",
            indicator_code="IIP_C",
            indicator_name="IIP",
            period=date(2024, 1, 1),
            value=100.0,
            unit="index",
            source="GSO",
        )
    )
    db_session.commit()
    status = pipeline_service.get_monitor_status(db_session)
    assert status["sample_size"] >= 2
    gso = next(h for h in status["source_health"] if h["source"] == "gso")
    assert gso["status"] == "ok"


def test_benchmark_peer_count_division_27(db_session, monkeypatch):
    from tests.companies.test_listed_companies import _patch_crawl_network

    _patch_crawl_network(monkeypatch)
    run_company_crawl(db_session, tickers=["RAL", "REE", "DQC", "GEE", "TYA"])
    assert db_session.query(FinancialReport).count() >= 5
    result = run_benchmark(
        db_session,
        BenchmarkInput(
            vsic_code="2740",
            operating_revenue=5e12,
            profit_before_tax=4e11,
            employees=3000,
            total_assets=6e12,
            total_equity=3e12,
            current_assets=3e12,
            current_liabilities=2e12,
        ),
    )
    assert result.peer_count >= 3
    assert "insufficient_peers" not in (result.warnings or [])
    assert result.percentiles.get("roa") is not None
