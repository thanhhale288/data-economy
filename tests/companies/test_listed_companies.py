"""Company crawl enrich / digital presence / idempotency — no live website fetch."""

from __future__ import annotations

from datetime import date

from backend.app.models import Company, DigitalPresence, FinancialReport
from crawlers.companies.listed_companies import (
    ALLOWED_TICKERS,
    load_seed_companies,
    run_company_crawl,
)
from crawlers.companies.website_detector import DetectionResult
from crawlers.financial.bctc_crawler import FetchResult, SEED_SOURCE_URL


def _stub_fetch(stock_code: str, **_kwargs) -> FetchResult:
    seed = next(s for s in load_seed_companies() if s["stock_code"] == stock_code)
    fin = seed.get("financial") or {}
    if not fin:
        return FetchResult(status="empty", detail="no_fin", report=None)
    report = {
        "stock_code": stock_code,
        "period": date.fromisoformat(fin["period"]),
        "report_type": "annual",
        "revenue": fin.get("revenue"),
        "profit_before_tax": fin.get("profit_before_tax"),
        "net_profit": fin.get("net_profit"),
        "total_assets": fin.get("total_assets"),
        "total_equity": fin.get("total_equity"),
        "current_assets": fin.get("current_assets"),
        "current_liabilities": fin.get("current_liabilities"),
        "operating_expenses": fin.get("operating_expenses"),
        "cost_of_goods": fin.get("cost_of_goods"),
        "rental_cost": fin.get("rental_cost"),
        "remuneration": fin.get("remuneration"),
        "employees": fin.get("employees"),
        "gross_margin": fin.get("gross_margin"),
        "source_url": SEED_SOURCE_URL,
    }
    return FetchResult(
        status="fallback",
        detail="test_seed_fallback",
        report=report,
        source_url=SEED_SOURCE_URL,
    )


def _patch_crawl_network(monkeypatch) -> None:
    monkeypatch.setattr(
        "crawlers.companies.listed_companies.detect_website",
        lambda url: DetectionResult(
            ok=True,
            has_ecommerce=False,
            has_checkout=False,
            detail="stub",
        ),
    )
    monkeypatch.setattr(
        "crawlers.companies.listed_companies.fetch_bctc",
        _stub_fetch,
    )


def test_seed_contains_exactly_ten_allowed_tickers():
    seeds = load_seed_companies()
    codes = [s["stock_code"] for s in seeds]
    assert len(codes) == 10
    assert set(codes) == set(ALLOWED_TICKERS)
    assert "BMP" in codes  # Nhựa Bình Minh (HOSE BMP) — not Biwase/BWE


def test_run_company_crawl_enriches_metadata_and_website_presence(
    db_session, monkeypatch
):
    _patch_crawl_network(monkeypatch)

    count = run_company_crawl(db_session)
    assert count == 10

    companies = db_session.query(Company).all()
    assert len(companies) == 10
    assert {c.stock_code for c in companies} == set(ALLOWED_TICKERS)

    ral = db_session.query(Company).filter_by(stock_code="RAL").one()
    assert ral.name.startswith("Công ty Cổ phần Bóng đèn")
    assert ral.vsic_code == "2740"
    assert ral.website_url == "https://rangdong.com.vn"

    websites = (
        db_session.query(DigitalPresence)
        .filter_by(company_id=ral.id, channel_type="website")
        .all()
    )
    assert len(websites) == 1
    assert websites[0].url == "https://rangdong.com.vn"
    assert websites[0].is_active is True

    fins = db_session.query(FinancialReport).filter_by(company_id=ral.id).all()
    assert len(fins) == 1
    assert fins[0].revenue == 5200000000000
    assert fins[0].source_url is not None
    assert fins[0].source_url.startswith(("seed:", "fallback:", "http"))


def test_run_company_crawl_idempotent(db_session, monkeypatch):
    _patch_crawl_network(monkeypatch)

    assert run_company_crawl(db_session) == 10
    assert run_company_crawl(db_session) == 10

    assert db_session.query(Company).count() == 10
    assert (
        db_session.query(DigitalPresence).filter_by(channel_type="website").count()
        == 10
    )
    # One annual report per company from seed fallback.
    assert db_session.query(FinancialReport).count() == 10


def test_detect_fail_keeps_previous_ecommerce_and_checkout(db_session, monkeypatch):
    """HTTP fail must not overwrite prior flags with guessed false."""
    from crawlers.companies.listed_companies import enrich_company, load_seed_companies

    # First enrich: live OK with ecommerce True (not seed OR).
    monkeypatch.setattr(
        "crawlers.companies.listed_companies.detect_website",
        lambda url: DetectionResult(
            ok=True,
            has_ecommerce=True,
            has_checkout=True,
            detail="stub_ok",
        ),
    )
    monkeypatch.setattr(
        "crawlers.companies.listed_companies.fetch_bctc",
        _stub_fetch,
    )
    seed = next(s for s in load_seed_companies() if s["stock_code"] == "RAL")
    enrich_company(db_session, seed)

    ral = db_session.query(Company).filter_by(stock_code="RAL").one()
    assert ral.has_ecommerce_site is True
    presence = (
        db_session.query(DigitalPresence)
        .filter_by(company_id=ral.id, channel_type="website")
        .one()
    )
    assert presence.has_checkout is True

    monkeypatch.setattr(
        "crawlers.companies.listed_companies.detect_website",
        lambda url: DetectionResult(
            ok=False,
            has_ecommerce=False,
            has_checkout=False,
            detail="http_fail status=403",
        ),
    )
    enrich_company(db_session, seed)

    db_session.refresh(ral)
    db_session.refresh(presence)
    assert ral.has_ecommerce_site is True
    assert presence.has_checkout is True


def test_live_detect_overrides_seed_ecommerce_flag(db_session, monkeypatch):
    """When detect ok=True, use live flags only — do not OR with seed."""
    from crawlers.companies.listed_companies import enrich_company, load_seed_companies

    monkeypatch.setattr(
        "crawlers.companies.listed_companies.detect_website",
        lambda url: DetectionResult(
            ok=True,
            has_ecommerce=False,
            has_checkout=False,
            detail="stub_no_shop",
        ),
    )
    monkeypatch.setattr(
        "crawlers.companies.listed_companies.fetch_bctc",
        _stub_fetch,
    )
    seed = next(s for s in load_seed_companies() if s["stock_code"] == "RAL")
    assert seed.get("has_ecommerce_site") is True  # seed says yes

    enrich_company(db_session, seed)
    ral = db_session.query(Company).filter_by(stock_code="RAL").one()
    assert ral.has_ecommerce_site is False  # live wins
    presence = (
        db_session.query(DigitalPresence)
        .filter_by(company_id=ral.id, channel_type="website")
        .one()
    )
    assert presence.has_checkout is False


def test_bmp_is_binh_minh_plastics(db_session, monkeypatch):
    _patch_crawl_network(monkeypatch)

    run_company_crawl(db_session)
    bmp = db_session.query(Company).filter_by(stock_code="BMP").one()
    assert bmp.vsic_code == "2220"
    assert "nhựa" in bmp.name.lower() or "Nhựa" in bmp.name
    assert "water" not in (bmp.description or "").lower()