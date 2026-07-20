"""Financial-ratio features derived from persisted company reports.

CafeF financial reports are normally quarterly snapshots.  This module keeps
their values discrete: a quarterly report is held over its calendar quarter
and an annual report over its calendar year; financial values are never
linearly interpolated.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models import FinancialReport

FINANCIAL_FEATURE_COLUMNS = ("roa", "roe", "current_ratio")

_REPORT_COLUMNS = (
    "company_id",
    "period",
    "report_type",
    "revenue",
    "net_profit",
    "total_assets",
    "total_equity",
    "current_assets",
    "current_liabilities",
)
_OUTPUT_COLUMNS = ("period", *FINANCIAL_FEATURE_COLUMNS, "financial_alignment")


def _empty_output() -> pd.DataFrame:
    """Return the standard empty, join-ready financial feature frame."""
    return pd.DataFrame(
        {
            "period": pd.Series(dtype="datetime64[ns]"),
            **{column: pd.Series(dtype="float64") for column in FINANCIAL_FEATURE_COLUMNS},
            "financial_alignment": pd.Series(dtype="object"),
        }
    )


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide only where both operands exist and the denominator is non-zero."""
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    valid = numerator.notna() & denominator.notna() & denominator.ne(0)
    return numerator.div(denominator).where(valid)


def _alignment_for_report_types(report_types: pd.Series) -> str:
    """Classify an aggregated period by its source-report cadence."""
    types = report_types.fillna("").astype(str).str.strip().str.lower()
    return "step_hold_annual" if not types.empty and types.eq("annual").all() else "step_hold_quarter"


def compute_firm_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Add roa, roe, current_ratio to firm-level rows; preserve report identity."""
    result = df.copy()
    for column in ("net_profit", "total_assets", "total_equity", "current_assets", "current_liabilities"):
        if column not in result:
            result[column] = np.nan

    result["roa"] = _safe_ratio(result["net_profit"], result["total_assets"])
    result["roe"] = _safe_ratio(result["net_profit"], result["total_equity"])
    result["current_ratio"] = _safe_ratio(
        result["current_assets"], result["current_liabilities"]
    )
    return result


def load_financial_reports_frame(db: Session) -> pd.DataFrame:
    """Load the financial_reports table into a DataFrame."""
    reports = db.query(FinancialReport).order_by(FinancialReport.period).all()
    return pd.DataFrame(
        [
            {column: getattr(report, column) for column in _REPORT_COLUMNS}
            for report in reports
        ],
        columns=_REPORT_COLUMNS,
    )


def aggregate_financial_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute firm ratios, then average each ratio across firms by period."""
    if df.empty:
        return _empty_output()

    ratios = compute_firm_ratios(df)
    ratios["period"] = pd.to_datetime(ratios["period"], errors="coerce")
    ratios = ratios.dropna(subset=["period"])
    if ratios.empty:
        return _empty_output()

    grouped = ratios.groupby("period", sort=True, dropna=False)
    aggregate = grouped[list(FINANCIAL_FEATURE_COLUMNS)].mean().reset_index()
    alignment = grouped["report_type"].agg(_alignment_for_report_types).reset_index(
        name="financial_alignment"
    )
    return aggregate.merge(alignment, on="period", how="left")[
        list(_OUTPUT_COLUMNS)
    ]


def _calendar_frame(calendar: pd.Series | pd.DatetimeIndex | list) -> pd.DataFrame:
    """Normalize supplied calendar entries to one row per calendar month."""
    periods = pd.to_datetime(pd.Series(calendar), errors="coerce").dropna()
    if periods.empty:
        return _empty_output()[["period"]]
    return (
        pd.DataFrame({"period": periods.dt.to_period("M").dt.to_timestamp()})
        .drop_duplicates()
        .sort_values("period")
        .reset_index(drop=True)
    )


def _expand_step_hold(aggregate: pd.DataFrame) -> pd.DataFrame:
    """Expand each aggregate period across its quarter or year."""
    expanded: list[pd.DataFrame] = []
    for row in aggregate.itertuples(index=False):
        period = pd.Timestamp(row.period)
        annual = row.financial_alignment == "step_hold_annual"
        start = pd.Timestamp(year=period.year, month=1, day=1) if annual else period.to_period("Q").start_time
        months = 12 if annual else 3
        frame = pd.DataFrame({"period": pd.date_range(start, periods=months, freq="MS")})
        for column in FINANCIAL_FEATURE_COLUMNS:
            frame[column] = getattr(row, column)
        frame["financial_alignment"] = row.financial_alignment
        expanded.append(frame)
    return pd.concat(expanded, ignore_index=True) if expanded else _empty_output()


def financial_features_for_calendar(
    db: Session,
    calendar: pd.Series | pd.DatetimeIndex | list,
) -> pd.DataFrame:
    """Return monthly financial features aligned to a requested calendar.

    Multiple report periods are step-held over their source cadence.  A lone
    aggregated report is instead broadcast to every requested calendar month,
    which makes the sparse seed data usable without fabricating an observed
    reporting cadence.
    """
    calendar_frame = _calendar_frame(calendar)
    if calendar_frame.empty:
        return _empty_output()

    aggregate = aggregate_financial_features(load_financial_reports_frame(db))
    if aggregate.empty:
        return _empty_output()

    if len(aggregate) == 1:
        result = calendar_frame.copy()
        for column in FINANCIAL_FEATURE_COLUMNS:
            result[column] = aggregate.iloc[0][column]
        result["financial_alignment"] = "broadcast_latest"
        return result[list(_OUTPUT_COLUMNS)]

    expanded = _expand_step_hold(aggregate)
    result = calendar_frame.merge(expanded, on="period", how="left")
    return result[list(_OUTPUT_COLUMNS)]
