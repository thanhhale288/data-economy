"""Orchestrate Task #10 data cleaning and write processed artifacts.

Primary clean path for the DAG: loads GSO/OECD macro + marketplace listings from
DB, cleans via ``cleaner`` / ``marketplace_clean`` / ``validate_vsic``, and writes
parquet + JSON under ``data/processed/`` without overwriting raw DB rows.

Task #46 also carries manufacturing VA (``VA_C`` / optional ``VA_C_NOMINAL``) from
``gso_macro`` into the cleaned wide frame as auxiliary columns. VA is already
quarterly→monthly step-held at ingest — cleaning does not re-interpolate or invent
dynamics. Forecast target remains GSO ``IIP_C`` (column ``iip``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models import GsoMacro, MarketplaceListing, OecdIndicator
from crawlers.oecd.sdmx_client import PEER_MEI_IP_COUNTRY
from pipeline.cleaning.cleaner import CleanProvenance, clean_timeseries
from pipeline.cleaning.marketplace_clean import clean_marketplace_listings
from pipeline.cleaning.vsic_validation import validate_vsic

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
CLEANED_MACRO_NAME = "cleaned_macro.parquet"
CLEANED_MARKETPLACE_NAME = "cleaned_marketplace.parquet"
CLEANING_REPORT_NAME = "cleaning_report.json"

MACRO_SERIES = ("iip", "indigo", "mei_ip")
# Auxiliary GSO VA columns (not forecast targets). Keys = parquet col, values = DB code.
VA_INDICATOR_MAP = {
    "va_c": "VA_C",
    "va_c_nominal": "VA_C_NOMINAL",
}
VA_MACRO_SERIES = tuple(VA_INDICATOR_MAP.keys())
VA_ALIGNMENT = "step_hold_at_ingest"


def _processed_dir() -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    return PROCESSED_DIR


def _provenance_dict(prov: CleanProvenance | Any) -> dict[str, Any]:
    if hasattr(prov, "to_dict"):
        return prov.to_dict()
    return dict(prov)


def _load_va_frame(
    db: Session, *, parquet_col: str, indicator_code: str
) -> pd.DataFrame | None:
    """Load one VA series with source/unit/alignment; None if absent (no invent)."""
    rows = (
        db.query(GsoMacro)
        .filter(
            GsoMacro.indicator_code == indicator_code,
            GsoMacro.vsic_code == "C",
        )
        .order_by(GsoMacro.period)
        .all()
    )
    if not rows:
        return None
    return pd.DataFrame(
        [
            {
                "period": r.period,
                parquet_col: r.value,
                f"{parquet_col}_source": r.source,
                f"{parquet_col}_unit": r.unit,
                f"{parquet_col}_alignment": VA_ALIGNMENT,
            }
            for r in rows
        ]
    )


def _load_raw_macro(db: Session) -> tuple[pd.DataFrame, list[str]]:
    """Load IIP_C / VA_C(+nominal) / INDIGO@VNM / MEI_IP@EA20 for cleaning."""
    series_missing: list[str] = []

    gso = (
        db.query(GsoMacro)
        .filter(GsoMacro.indicator_code == "IIP_C", GsoMacro.vsic_code == "C")
        .order_by(GsoMacro.period)
        .all()
    )
    gso_df = pd.DataFrame([{"period": r.period, "iip": r.value} for r in gso])
    if gso_df.empty:
        series_missing.append("iip")

    frames: list[pd.DataFrame] = [gso_df] if not gso_df.empty else []

    for parquet_col, indicator_code in VA_INDICATOR_MAP.items():
        va_df = _load_va_frame(db, parquet_col=parquet_col, indicator_code=indicator_code)
        if va_df is None:
            series_missing.append(parquet_col)
        else:
            frames.append(va_df)

    indigo = (
        db.query(OecdIndicator)
        .filter(
            OecdIndicator.indicator_code == "INDIGO",
            OecdIndicator.country == "VNM",
        )
        .order_by(OecdIndicator.period)
        .all()
    )
    if indigo:
        frames.append(
            pd.DataFrame([{"period": r.period, "indigo": r.value} for r in indigo])
        )
    else:
        series_missing.append("indigo")

    mei_peer = (
        db.query(OecdIndicator)
        .filter(
            OecdIndicator.indicator_code == "MEI_IP",
            OecdIndicator.country == PEER_MEI_IP_COUNTRY,
        )
        .order_by(OecdIndicator.period)
        .all()
    )
    if mei_peer:
        frames.append(
            pd.DataFrame(
                [{"period": r.period, "mei_ip": r.value} for r in mei_peer]
            )
        )
    else:
        series_missing.append("mei_ip")

    if not frames:
        return pd.DataFrame(columns=["period"]), series_missing

    df = frames[0]
    for other in frames[1:]:
        df = df.merge(other, on="period", how="outer")
    df = df.sort_values("period").reset_index(drop=True)
    return df, series_missing


def _clean_va_series(
    raw: pd.DataFrame, col: str
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Pass-through VA levels: no linear gap fill / outlier rewrite (honest step-hold)."""
    series_df = raw[["period", col]].rename(columns={col: "value"})
    cleaned_df, prov = clean_timeseries(
        series_df,
        "value",
        max_gap=0,
        fill_long_gaps=False,
        outlier_method="none",
        return_provenance=True,
    )
    report = _provenance_dict(prov)
    sources = (
        sorted(raw[f"{col}_source"].dropna().astype(str).unique())
        if f"{col}_source" in raw.columns
        else []
    )
    units = (
        sorted(raw[f"{col}_unit"].dropna().astype(str).unique())
        if f"{col}_unit" in raw.columns
        else []
    )
    notes = list(report.get("notes") or [])
    notes.append(
        "VA levels from gso_macro; quarterly→monthly step-hold already applied at ingest"
    )
    notes.append("no linear gap fill / outlier rewrite (avoid inventing dynamics)")
    notes.append("auxiliary feature only — forecast target remains iip / IIP_C")
    if sources:
        notes.append("source=" + ",".join(sources))
    if units:
        notes.append("unit=" + ",".join(units))
    report["notes"] = notes
    report["alignment"] = VA_ALIGNMENT
    report["indicator_code"] = VA_INDICATOR_MAP[col]
    report["role"] = "auxiliary_feature"
    return cleaned_df.rename(columns={"value": col})[["period", col]], report


def _clean_macro_series(
    raw: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    """Clean each present numeric column independently; join on period."""
    if raw.empty or "period" not in raw.columns:
        return pd.DataFrame(columns=["period"]), {}

    cleaned = pd.DataFrame({"period": raw["period"]})
    macro_report: dict[str, dict[str, Any]] = {}

    for col in MACRO_SERIES:
        if col not in raw.columns:
            continue
        series_df = raw[["period", col]].rename(columns={col: "value"})
        cleaned_df, prov = clean_timeseries(series_df, "value", return_provenance=True)
        # Align by period — clean_timeseries sorts, so never assign by position.
        cleaned = cleaned.merge(
            cleaned_df.rename(columns={"value": col})[["period", col]],
            on="period",
            how="left",
        )
        macro_report[col] = _provenance_dict(prov)

    for col in VA_MACRO_SERIES:
        if col not in raw.columns:
            continue
        va_cleaned, va_report = _clean_va_series(raw, col)
        meta_cols = [
            m
            for m in (f"{col}_source", f"{col}_unit", f"{col}_alignment")
            if m in raw.columns
        ]
        va_frame = va_cleaned
        if meta_cols:
            va_frame = va_cleaned.merge(
                raw[["period", *meta_cols]].drop_duplicates(subset=["period"]),
                on="period",
                how="left",
            )
        cleaned = cleaned.merge(va_frame, on="period", how="left")
        macro_report[col] = va_report

    cleaned = cleaned.sort_values("period").reset_index(drop=True)
    return cleaned, macro_report


def _listings_to_dataframe(db: Session) -> pd.DataFrame:
    rows = db.query(MarketplaceListing).order_by(MarketplaceListing.id).all()
    if not rows:
        return pd.DataFrame(
            columns=[
                "id",
                "company_id",
                "platform",
                "product_name",
                "price",
                "units_sold_est",
                "revenue_est",
                "rating",
                "product_url",
                "crawled_at",
            ]
        )
    return pd.DataFrame(
        [
            {
                "id": r.id,
                "company_id": r.company_id,
                "platform": r.platform,
                "product_name": r.product_name,
                "price": r.price,
                "units_sold_est": r.units_sold_est,
                "revenue_est": r.revenue_est,
                "rating": r.rating,
                "product_url": r.product_url,
                "crawled_at": r.crawled_at,
            }
            for r in rows
        ]
    )


def _detail_summary(
    *,
    macro_report: dict[str, dict[str, Any]],
    vsic: dict[str, Any],
    marketplace: dict[str, Any],
    series_missing: list[str],
    records: int,
) -> str:
    nan_filled = sum(
        int(p.get("short_gap_filled", 0)) + int(p.get("long_gap_filled", 0))
        for p in macro_report.values()
    )
    outliers = sum(int(p.get("outliers_handled", 0)) for p in macro_report.values())
    mp_flagged = sum(int(v) for v in marketplace.get("outliers_flagged", {}).values())
    vsic_fails = int(vsic.get("companies_fail", 0)) + int(vsic.get("gso_fail", 0))
    missing = ",".join(series_missing) if series_missing else "none"
    return (
        f"records={records}; nan_filled={nan_filled}; outliers={outliers}; "
        f"mp_outliers_flagged={mp_flagged}; vsic_fails={vsic_fails}; "
        f"series_missing={missing}"
    )


def run_data_cleaning(db: Session) -> tuple[int, str]:
    """Returns (records_touched_or_written, detail_summary_for_pipeline_jobs)."""
    out_dir = _processed_dir()

    raw_macro, series_missing = _load_raw_macro(db)
    cleaned_macro, macro_report = _clean_macro_series(raw_macro)

    vsic_report = validate_vsic(db)
    vsic_dict = vsic_report.to_dict()

    listings_df = _listings_to_dataframe(db)
    # MarketplaceListing has no shop_name — entity resolution skips; flag outliers only.
    cleaned_listings, mp_prov = clean_marketplace_listings(
        listings_df,
        outlier_method="iqr",
        outlier_action="flag",
    )
    mp_dict = mp_prov.to_dict()

    macro_path = out_dir / CLEANED_MACRO_NAME
    marketplace_path = out_dir / CLEANED_MARKETPLACE_NAME
    report_path = out_dir / CLEANING_REPORT_NAME

    cleaned_macro.to_parquet(macro_path, index=False)
    cleaned_listings.to_parquet(marketplace_path, index=False)

    report = {
        "macro": macro_report,
        "vsic": vsic_dict,
        "marketplace": mp_dict,
        "artifacts": [CLEANED_MACRO_NAME, CLEANED_MARKETPLACE_NAME],
        "series_missing": series_missing,
    }
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    records = len(cleaned_macro) + len(cleaned_listings)
    detail = _detail_summary(
        macro_report=macro_report,
        vsic=vsic_dict,
        marketplace=mp_dict,
        series_missing=series_missing,
        records=records,
    )
    return records, detail
