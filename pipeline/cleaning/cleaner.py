"""Data cleaning utilities."""

import numpy as np
import pandas as pd


def fill_missing_short_gaps(series: pd.Series, max_gap: int = 2) -> pd.Series:
    return series.interpolate(method="linear", limit=max_gap)


def fill_missing_long_gaps(series: pd.Series) -> pd.Series:
    return series.interpolate(method="linear")


def detect_outliers_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return (series < lower) | (series > upper)


def clean_timeseries(df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
    df = df.sort_values("period").copy()
    df[value_col] = fill_missing_short_gaps(df[value_col])
    df[value_col] = fill_missing_long_gaps(df[value_col])

    outliers = detect_outliers_iqr(df[value_col])
    median_val = df[value_col].median()
    df.loc[outliers, value_col] = median_val
    return df


def resample_quarterly_to_monthly(df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
    df = df.set_index("period")
    monthly = df[value_col].resample("MS").interpolate(method="linear")
    return monthly.reset_index().rename(columns={value_col: "value"})
