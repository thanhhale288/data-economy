"""Persistence / upsert tests for financial_reports."""

from __future__ import annotations

from datetime import date

from backend.app.models import FinancialReport
from crawlers.financial.bctc_crawler import upsert_financial_report


def test_upsert_financial_report_inserts_then_updates_same_key(
    db_session, sample_company
):
    report = {
        "period": date(2024, 12, 31),
        "report_type": "annual",
        "revenue": 100.0,
        "net_profit": 10.0,
        "employees": 100,
        "gross_margin": 0.2,
        "source_url": "seed:companies.json",
        "profit_before_tax": None,
        "total_assets": None,
        "total_equity": None,
        "current_assets": None,
        "current_liabilities": None,
        "operating_expenses": None,
        "cost_of_goods": None,
        "rental_cost": None,
        "remuneration": None,
    }

    created = upsert_financial_report(db_session, sample_company.id, report)
    assert created is True
    assert db_session.query(FinancialReport).count() == 1

    report["revenue"] = 200.0
    report["source_url"] = "fallback:data/raw/companies_bctc_fallback.json"
    created_again = upsert_financial_report(db_session, sample_company.id, report)
    assert created_again is False
    assert db_session.query(FinancialReport).count() == 1

    row = db_session.query(FinancialReport).one()
    assert row.revenue == 200.0
    assert row.source_url == "fallback:data/raw/companies_bctc_fallback.json"
    assert row.profit_before_tax is None
