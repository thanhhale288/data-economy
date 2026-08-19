"""Task #94 — BCTC consistency check: extract vs historical DB financial_reports."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import Company, FinancialReport, VsicCode
from backend.app.services.bctc_consistency import (
    CONSISTENCY_FIELD_MAP,
    check_consistency,
)


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'consistency_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(
        VsicCode(vsic_code="2740", isic_code="2740", level=4, name_vi="Thiết bị chiếu sáng")
    )
    session.commit()
    yield session
    session.close()
    engine.dispose()


def _add_company(db, stock_code="RAL"):
    c = Company(stock_code=stock_code, name=stock_code, vsic_code="2740", exchange="HOSE")
    db.add(c)
    db.commit()
    return c


def _add_report(db, company, *, period=date(2024, 12, 31), **kwargs):
    defaults = dict(
        company_id=company.id,
        period=period,
        report_type="annual",
        revenue=5_200_000_000_000,
        profit_before_tax=420_000_000_000,
        total_assets=6_800_000_000_000,
        total_equity=3_200_000_000_000,
        employees=3200,
    )
    defaults.update(kwargs)
    r = FinancialReport(**defaults)
    db.add(r)
    db.commit()
    return r


# ── no DB record ────────────────────────────────────────────────────────────

def test_no_db_record_returns_has_db_record_false(db):
    report = check_consistency(db, "UNKNOWN", {"operating_revenue": 1e12})
    assert not report.has_db_record
    assert report.ticker == "UNKNOWN"
    assert all(f.severity == "warn" for f in report.flags)
    assert all(f.note == "no_db_record" for f in report.flags)


# ── matching values ──────────────────────────────────────────────────────────

def test_consistent_extract_all_ok(db):
    company = _add_company(db)
    _add_report(db, company)
    extract = {
        "operating_revenue": 5_200_000_000_000,
        "profit_before_tax": 420_000_000_000,
        "total_assets": 6_800_000_000_000,
        "total_equity": 3_200_000_000_000,
        "employees": 3200,
    }
    report = check_consistency(db, "RAL", extract)
    assert report.has_db_record
    ok_flags = [f for f in report.flags if f.severity == "ok"]
    assert len(ok_flags) == len(CONSISTENCY_FIELD_MAP)


# ── minor deviation under threshold ─────────────────────────────────────────

def test_small_deviation_below_threshold_is_ok(db):
    company = _add_company(db)
    _add_report(db, company)
    # 5% deviation — under 10% threshold
    extract = {"operating_revenue": 5_200_000_000_000 * 1.05}
    report = check_consistency(db, "RAL", extract)
    rev_flag = next(f for f in report.flags if f.extract_field == "operating_revenue")
    assert rev_flag.severity == "ok"
    assert rev_flag.rel_deviation is not None
    assert rev_flag.rel_deviation < 0.10


# ── large deviation triggers mismatch ───────────────────────────────────────

def test_large_deviation_triggers_mismatch(db):
    company = _add_company(db)
    _add_report(db, company)
    # 30% deviation → mismatch
    extract = {"operating_revenue": 5_200_000_000_000 * 1.30}
    report = check_consistency(db, "RAL", extract)
    rev_flag = next(f for f in report.flags if f.extract_field == "operating_revenue")
    assert rev_flag.severity == "mismatch"
    assert rev_flag.rel_deviation is not None
    assert rev_flag.rel_deviation >= 0.10
    assert "lệch" in report.summary


# ── null extract field ───────────────────────────────────────────────────────

def test_null_extract_field_is_warn_not_mismatch(db):
    company = _add_company(db)
    _add_report(db, company)
    extract = {"operating_revenue": None}
    report = check_consistency(db, "RAL", extract)
    rev_flag = next(f for f in report.flags if f.extract_field == "operating_revenue")
    assert rev_flag.severity == "warn"
    assert rev_flag.note == "extract_null"


# ── null DB field ────────────────────────────────────────────────────────────

def test_null_db_field_is_warn_not_mismatch(db):
    company = _add_company(db)
    _add_report(db, company, employees=None)
    extract = {"employees": 3500}
    report = check_consistency(db, "RAL", extract)
    emp_flag = next(f for f in report.flags if f.extract_field == "employees")
    assert emp_flag.severity == "warn"
    assert emp_flag.note == "db_null"


# ── both null ────────────────────────────────────────────────────────────────

def test_both_null_is_ok_not_mismatch(db):
    company = _add_company(db)
    _add_report(db, company, total_equity=None)
    extract = {"total_equity": None}
    report = check_consistency(db, "RAL", extract)
    eq_flag = next(f for f in report.flags if f.extract_field == "total_equity")
    assert eq_flag.severity == "ok"
    assert eq_flag.note == "both_null"


# ── ticker normalised to uppercase ──────────────────────────────────────────

def test_ticker_normalized_uppercase(db):
    company = _add_company(db, "REE")
    _add_report(db, company)
    report = check_consistency(db, "ree", {"operating_revenue": 5_200_000_000_000})
    assert report.ticker == "REE"
    assert report.has_db_record


# ── latest annual period is picked ──────────────────────────────────────────

def test_latest_annual_period_used(db):
    company = _add_company(db)
    _add_report(db, company, period=date(2022, 12, 31), revenue=3_000_000_000_000)
    _add_report(db, company, period=date(2024, 12, 31), revenue=5_200_000_000_000)
    extract = {"operating_revenue": 5_200_000_000_000}
    report = check_consistency(db, "RAL", extract)
    assert report.period == "2024-12-31"
    rev_flag = next(f for f in report.flags if f.extract_field == "operating_revenue")
    assert rev_flag.severity == "ok"


# ── consistency_field_map coverage ──────────────────────────────────────────

def test_all_mapped_fields_appear_in_flags(db):
    company = _add_company(db)
    _add_report(db, company)
    report = check_consistency(db, "RAL", {})
    flag_fields = {f.extract_field for f in report.flags}
    assert flag_fields == set(CONSISTENCY_FIELD_MAP.keys())
