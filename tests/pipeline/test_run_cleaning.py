"""Light integration tests for run_data_cleaning (skips if module not merged)."""

from __future__ import annotations

import importlib
import json
from datetime import date

import pytest

run_cleaning_mod = pytest.importorskip(
    "pipeline.cleaning.run_cleaning",
    reason="pipeline.cleaning.run_cleaning not merged yet",
)

run_data_cleaning = getattr(run_cleaning_mod, "run_data_cleaning", None)
if run_data_cleaning is None:
    pytest.skip(
        "run_data_cleaning not exported from pipeline.cleaning.run_cleaning",
        allow_module_level=True,
    )

from backend.app.models import GsoMacro, MarketplaceListing  # noqa: E402

# Keys written to data/processed/cleaning_report.json by run_data_cleaning.
EXPECTED_REPORT_KEYS = ("macro", "vsic", "marketplace", "artifacts", "series_missing")


@pytest.fixture()
def cleaning_db(seeded_cleaning_db):
    """Seed IIP_C macro + one listing so the cleaner has rows to process."""
    from backend.app.models import Company

    db = seeded_cleaning_db
    db.add(
        GsoMacro(
            indicator_code="IIP_C",
            indicator_name="IIP Section C",
            vsic_code="C",
            period=date(2024, 1, 1),
            value=100.0,
            unit="index",
            source="GSO",
        )
    )
    db.add(
        GsoMacro(
            indicator_code="IIP_C",
            indicator_name="IIP Section C",
            vsic_code="C",
            period=date(2024, 2, 1),
            value=102.0,
            unit="index",
            source="GSO",
        )
    )
    ral = db.query(Company).filter_by(stock_code="RAL").one()
    db.add(
        MarketplaceListing(
            company_id=ral.id,
            platform="shopee",
            product_name="LED test",
            price=45_000.0,
            units_sold_est=100,
            revenue_est=4_500_000.0,
        )
    )
    db.commit()
    return db


@pytest.fixture()
def processed_tmpdir(tmp_path, monkeypatch):
    """Redirect cleaning artifacts to a temp dir (no network, no shared data/)."""
    out = tmp_path / "processed"
    out.mkdir()
    monkeypatch.setattr(run_cleaning_mod, "PROCESSED_DIR", out)
    return out


def test_run_data_cleaning_returns_int_and_str(cleaning_db, processed_tmpdir):
    result = run_data_cleaning(cleaning_db)
    assert isinstance(result, tuple) and len(result) == 2
    count, detail = result
    assert isinstance(count, int)
    assert isinstance(detail, str)
    assert count >= 1
    assert "records=" in detail


def test_run_data_cleaning_writes_report_keys(cleaning_db, processed_tmpdir):
    run_data_cleaning(cleaning_db)
    report_path = processed_tmpdir / run_cleaning_mod.CLEANING_REPORT_NAME
    assert report_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for key in EXPECTED_REPORT_KEYS:
        assert key in report, f"missing report key {key!r}; got {list(report)}"
    assert "vsic" in report and "companies_checked" in report["vsic"]
    assert "marketplace" in report and "outliers_flagged" in report["marketplace"]
    assert (processed_tmpdir / run_cleaning_mod.CLEANED_MACRO_NAME).is_file()
    assert (processed_tmpdir / run_cleaning_mod.CLEANED_MARKETPLACE_NAME).is_file()


def test_run_cleaning_module_imports_without_network():
    mod = importlib.import_module("pipeline.cleaning.run_cleaning")
    assert hasattr(mod, "run_data_cleaning")
