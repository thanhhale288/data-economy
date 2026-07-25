"""Epic 3 Task #32 — CafeF enrich: mock OK persist + network fail → fallback."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import httpx

from backend.app.models import FinancialReport
from crawlers.financial.batch_enrich import (
    classify_fetch_status,
    enrich_ticker,
    write_enrich_report,
)
from crawlers.financial.bctc_crawler import fetch_bctc
from tests.financial.conftest import FIXTURES


def test_fetch_bctc_cafef_ok_mocked(monkeypatch):
    html = (FIXTURES / "cafef_bmp_bctc.html").read_text(encoding="utf-8")

    def ok(self, url, **_kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(200, request=request, text=html)

    monkeypatch.setattr(httpx.Client, "get", ok)

    result = fetch_bctc("BMP")
    assert result.status == "ok"
    assert result.detail == "cafef_ok"
    assert result.report is not None
    assert "cafef" in (result.source_url or "").lower()
    assert result.report["employees"] is None
    assert result.report["revenue"] is not None
    assert classify_fetch_status(result) == "cafef_ok"


def test_fetch_bctc_cafef_network_fail_uses_fallback(monkeypatch):
    def boom(self, url, **_kwargs):
        raise httpx.ConnectError("blocked", request=MagicMock())

    monkeypatch.setattr(httpx.Client, "get", boom)

    result = fetch_bctc("RAL", use_fallback=True)
    assert result.status == "fallback"
    assert "cafef_error" in result.detail
    assert result.report is not None
    assert result.report["source_url"] in (
        "seed:companies.json",
        "fallback:data/raw/companies_bctc_fallback.json",
    )
    assert classify_fetch_status(result) == "fallback"


def test_enrich_ticker_cafef_ok_persists_source_url_and_null_employees(
    monkeypatch, db_session, sample_company
):
    """CafeF OK → DB row with CafeF source_url; employees stay null (no seed fill)."""
    sample_company.stock_code = "BMP"
    db_session.commit()

    html = (FIXTURES / "cafef_bmp_bctc.html").read_text(encoding="utf-8")

    def ok(self, url, **_kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(200, request=request, text=html)

    monkeypatch.setattr(httpx.Client, "get", ok)

    # Seed annual already in DB with employees — must not merge into CafeF quarterly.
    db_session.add(
        FinancialReport(
            company_id=sample_company.id,
            period=date(2024, 12, 31),
            report_type="annual",
            revenue=1.0,
            employees=9999,
            source_url="seed:companies.json",
        )
    )
    db_session.commit()

    row = enrich_ticker(db_session, "BMP", persist=True)
    assert row.status == "cafef_ok"
    assert row.persisted is True
    assert row.employees is None
    assert "cafef" in (row.source_url or "").lower()

    quarterly = (
        db_session.query(FinancialReport)
        .filter_by(company_id=sample_company.id, report_type="quarterly")
        .one()
    )
    assert quarterly.source_url and "cafef" in quarterly.source_url.lower()
    assert quarterly.employees is None
    assert quarterly.revenue is not None

    annual = (
        db_session.query(FinancialReport)
        .filter_by(company_id=sample_company.id, report_type="annual")
        .one()
    )
    assert annual.employees == 9999
    assert annual.source_url == "seed:companies.json"


def test_enrich_ticker_cafef_fail_fallback_no_invent(monkeypatch, db_session, sample_company):
    def boom(self, url, **_kwargs):
        raise httpx.ConnectTimeout("timed out", request=MagicMock())

    monkeypatch.setattr(httpx.Client, "get", boom)

    row = enrich_ticker(db_session, "RAL", persist=True)
    assert row.status == "fallback"
    assert row.persisted is True
    assert "cafef_error" in row.detail
    assert row.source_url is not None
    assert not str(row.source_url).lower().startswith("http")

    saved = db_session.query(FinancialReport).filter_by(company_id=sample_company.id).one()
    assert saved.source_url in (
        "seed:companies.json",
        "fallback:data/raw/companies_bctc_fallback.json",
    )


def test_write_enrich_report_md_csv(tmp_path):
    from crawlers.financial.batch_enrich import EnrichRow

    rows = [
        EnrichRow(
            ticker="BMP",
            status="cafef_ok",
            detail="cafef_ok",
            period="2025-12-31",
            report_type="quarterly",
            source_url="https://s.cafef.vn/BMP/bao-cao-tai-chinh.chn",
            persisted=True,
            revenue=1.0,
            employees=None,
        ),
        EnrichRow(
            ticker="ZZZ",
            status="error",
            detail="no_fallback:cafef_error",
            period=None,
            report_type=None,
            source_url=None,
            persisted=False,
        ),
    ]
    md_path, csv_path = write_enrich_report(
        rows, report_dir=tmp_path, stem="task32-test"
    )
    assert md_path.exists() and csv_path.exists()
    text = md_path.read_text(encoding="utf-8")
    assert "BMP" in text and "cafef_ok" in text
    assert "ZZZ" in text and "error" in text
