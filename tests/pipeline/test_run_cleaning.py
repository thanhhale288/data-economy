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


@pytest.fixture()
def cleaning_db_with_va(cleaning_db):
    """Extend cleaning_db with VA_C + VA_C_NOMINAL (no invent from IIP)."""
    db = cleaning_db
    for period, va_c, va_nom in (
        (date(2024, 1, 1), 500.0, 800.0),
        (date(2024, 2, 1), 500.0, 800.0),  # step-hold flat within quarter
    ):
        db.add(
            GsoMacro(
                indicator_code="VA_C",
                indicator_name="Manufacturing VA constant",
                vsic_code="C",
                period=period,
                value=va_c,
                unit="billion_vnd_constant_2010",
                source="GSO",
            )
        )
        db.add(
            GsoMacro(
                indicator_code="VA_C_NOMINAL",
                indicator_name="Manufacturing VA nominal",
                vsic_code="C",
                period=period,
                value=va_nom,
                unit="billion_vnd_current",
                source="GSO",
            )
        )
    db.commit()
    return db


def test_run_data_cleaning_includes_va_with_provenance(
    cleaning_db_with_va, processed_tmpdir
):
    import pandas as pd

    run_data_cleaning(cleaning_db_with_va)
    macro = pd.read_parquet(processed_tmpdir / run_cleaning_mod.CLEANED_MACRO_NAME)
    assert "va_c" in macro.columns
    assert "va_c_nominal" in macro.columns
    assert "va_c_source" in macro.columns
    assert "va_c_unit" in macro.columns
    assert "va_c_alignment" in macro.columns
    assert set(macro["va_c"].dropna()) == {500.0}
    assert set(macro["va_c_alignment"].dropna()) == {
        run_cleaning_mod.VA_ALIGNMENT
    }
    assert set(macro["va_c_source"].dropna()) == {"GSO"}
    assert set(macro["va_c_unit"].dropna()) == {"billion_vnd_constant_2010"}

    report = json.loads(
        (processed_tmpdir / run_cleaning_mod.CLEANING_REPORT_NAME).read_text(
            encoding="utf-8"
        )
    )
    assert "va_c" in report["macro"]
    assert report["macro"]["va_c"]["role"] == "auxiliary_feature"
    assert report["macro"]["va_c"]["alignment"] == run_cleaning_mod.VA_ALIGNMENT
    assert report["macro"]["va_c"]["outlier_method"] == "none"
    assert report["macro"]["va_c"]["long_gap_filled"] == 0
    assert "va_c" not in report["series_missing"]
    assert "va_c_nominal" not in report["series_missing"]


def test_run_data_cleaning_does_not_invent_va_when_absent(
    cleaning_db, processed_tmpdir
):
    import pandas as pd

    run_data_cleaning(cleaning_db)
    macro = pd.read_parquet(processed_tmpdir / run_cleaning_mod.CLEANED_MACRO_NAME)
    assert "va_c" not in macro.columns
    assert "iip" in macro.columns
    report = json.loads(
        (processed_tmpdir / run_cleaning_mod.CLEANING_REPORT_NAME).read_text(
            encoding="utf-8"
        )
    )
    assert "va_c" in report["series_missing"]
    assert "va_c_nominal" in report["series_missing"]
    assert "va_c" not in report["macro"]