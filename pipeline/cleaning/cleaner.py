"""Data cleaning utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd


@dataclass
class CleanProvenance:
    """Metadata describing what a cleaning pass changed."""

    value_col: str
    short_gap_filled: int
    long_gap_filled: int
    outliers_detected: int
    outliers_handled: int
    outlier_method: str  # "iqr" | "zscore" | "none"
    outlier_action: str  # "median" | "winsorize" | "null" | "none"
    max_gap: int
    zscore_threshold: float | None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fill_missing_short_gaps(series: pd.Series, max_gap: int = 2) -> pd.Series:
    """Linear-interpolate contiguous NaN runs of length <= max_gap only.

    Longer runs are left as NaN so a separate long-gap pass can fill them
    (and provenance can attribute fills to the correct method).
    """
    s = series.astype(float)
    if max_gap <= 0 or not s.isna().any():
        return s.copy()

    na = s.isna()
    # Contiguous True/False runs share an id; size is the run length.
    run_id = na.ne(na.shift(fill_value=False)).cumsum()
    run_len = na.groupby(run_id).transform("size")
    short_na = na & (run_len <= max_gap)

    interpolated = s.interpolate(method="linear")
    out = s.copy()
    out.loc[short_na] = interpolated.loc[short_na]
    return out


def fill_missing_long_gaps(series: pd.Series) -> pd.Series:
    """Linear-interpolate remaining NaNs without a gap-length limit."""
    return series.interpolate(method="linear")


def detect_outliers_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
    """Boolean mask of IQR outliers (True = outlier). NaNs are never flagged."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    if pd.isna(iqr) or iqr == 0:
        return pd.Series(False, index=series.index)
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return (series < lower) | (series > upper)


def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Boolean mask of |Z| > threshold outliers. NaNs are never flagged."""
    mean = series.mean()
    std = series.std(ddof=0)
    if pd.isna(std) or std == 0 or pd.isna(mean):
        return pd.Series(False, index=series.index)
    z = (series - mean) / std
    return z.abs() > threshold


def _iqr_fences(series: pd.Series, factor: float) -> tuple[float, float] | None:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    if pd.isna(iqr) or iqr == 0:
        return None
    return float(q1 - factor * iqr), float(q3 + factor * iqr)


def _zscore_fences(series: pd.Series, threshold: float) -> tuple[float, float] | None:
    mean = series.mean()
    std = series.std(ddof=0)
    if pd.isna(std) or std == 0 or pd.isna(mean):
        return None
    return float(mean - threshold * std), float(mean + threshold * std)


def clean_timeseries(
    df: pd.DataFrame,
    value_col: str = "value",
    *,
    max_gap: int = 2,
    fill_long_gaps: bool = True,
    outlier_method: Literal["iqr", "zscore", "none"] = "iqr",
    outlier_action: Literal["median", "winsorize", "null"] = "median",
    iqr_factor: float = 1.5,
    zscore_threshold: float = 3.0,
    return_provenance: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, CleanProvenance]:
    """Clean a timeseries column with gap fill then outlier handling.

    Short-gap fill (limited linear) runs first; long-gap fill (unlimited linear)
    is optional and counted separately so provenance can distinguish methods.
    """
    out = df.copy()
    notes: list[str] = []

    if "period" in out.columns:
        out = out.sort_values("period")

    series = out[value_col].astype(float)
    was_na = series.isna()

    filled_short = fill_missing_short_gaps(series, max_gap=max_gap)
    short_gap_filled = int((was_na & filled_short.notna()).sum())

    if fill_long_gaps:
        remaining_na = filled_short.isna()
        filled_long = fill_missing_long_gaps(filled_short)
        long_gap_filled = int((remaining_na & filled_long.notna()).sum())
        cleaned = filled_long
    else:
        long_gap_filled = 0
        cleaned = filled_short
        if cleaned.isna().any():
            notes.append("long gaps left unfilled (fill_long_gaps=False)")

    outliers_detected = 0
    outliers_handled = 0
    effective_action = "none" if outlier_method == "none" else outlier_action
    z_thresh: float | None = zscore_threshold if outlier_method == "zscore" else None

    if outlier_method == "none":
        notes.append("outlier detection skipped")
    else:
        if outlier_method == "iqr":
            outlier_mask = detect_outliers_iqr(cleaned, factor=iqr_factor)
            fences = _iqr_fences(cleaned, iqr_factor)
        else:
            outlier_mask = detect_outliers_zscore(cleaned, threshold=zscore_threshold)
            fences = _zscore_fences(cleaned, zscore_threshold)

        # Only flag finite values; keep NaN positions as non-outliers
        outlier_mask = outlier_mask.fillna(False)
        outliers_detected = int(outlier_mask.sum())

        if outliers_detected == 0:
            pass
        elif outlier_action == "median":
            median_val = cleaned.median()
            cleaned = cleaned.copy()
            cleaned.loc[outlier_mask] = median_val
            outliers_handled = outliers_detected
        elif outlier_action == "winsorize":
            cleaned = cleaned.copy()
            if fences is None:
                notes.append("winsorize skipped: could not compute fences")
            else:
                lower, upper = fences
                cleaned.loc[outlier_mask] = cleaned.loc[outlier_mask].clip(lower, upper)
                outliers_handled = outliers_detected
        elif outlier_action == "null":
            cleaned = cleaned.copy()
            cleaned.loc[outlier_mask] = np.nan
            outliers_handled = outliers_detected

    out[value_col] = cleaned

    provenance = CleanProvenance(
        value_col=value_col,
        short_gap_filled=short_gap_filled,
        long_gap_filled=long_gap_filled,
        outliers_detected=outliers_detected,
        outliers_handled=outliers_handled,
        outlier_method=outlier_method,
        outlier_action=effective_action,
        max_gap=max_gap,
        zscore_threshold=z_thresh,
        notes=notes,
    )

    if return_provenance:
        return out, provenance
    return out


def resample_quarterly_to_monthly(df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
    df = df.set_index("period")
    monthly = df[value_col].resample("MS").interpolate(method="linear")
    return monthly.reset_index().rename(columns={value_col: "value"})
