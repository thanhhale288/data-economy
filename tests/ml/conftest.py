"""Shared fixtures for Task #12 ML unit tests (no network / no live DB)."""

from __future__ import annotations

import os

# Avoid OpenMP segfaults with XGBoost on some macOS / CI runners.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def monthly_periods_2020_2024() -> pd.DatetimeIndex:
    """Monthly month-starts from 2020-01 through 2024-12 (60 periods)."""
    return pd.date_range("2020-01-01", "2024-12-01", freq="MS")


@pytest.fixture()
def synthetic_iip_series(monthly_periods_2020_2024) -> pd.Series:
    """~60-month synthetic IIP with trend + mild seasonality (deterministic)."""
    n = len(monthly_periods_2020_2024)
    t = np.arange(n, dtype=float)
    values = 100.0 + 0.15 * t + 2.0 * np.sin(2 * np.pi * t / 12.0) + 0.3 * np.cos(
        2 * np.pi * t / 6.0
    )
    return pd.Series(values, index=monthly_periods_2020_2024, name="iip")


@pytest.fixture()
def synthetic_feature_frame(synthetic_iip_series) -> pd.DataFrame:
    """Small feature panel for XGBoost (period, iip, lags, indigo, etc.)."""
    iip = synthetic_iip_series.astype(float)
    periods = iip.index
    indigo = 90.0 + 0.1 * np.arange(len(iip)) + 0.5 * np.sin(np.arange(len(iip)) / 4.0)
    df = pd.DataFrame(
        {
            "period": periods,
            "iip": iip.values,
            "iip_lag1": iip.shift(1).values,
            "iip_lag2": iip.shift(2).values,
            "iip_lag3": iip.shift(3).values,
            "iip_roll3m": iip.rolling(3, min_periods=1).mean().values,
            "iip_roll6m": iip.rolling(6, min_periods=1).mean().values,
            "iip_growth": iip.pct_change().fillna(0.0).values,
            "indigo": indigo,
            "indigo_lag1": pd.Series(indigo).shift(1).values,
            "digital_adoption_score": 0.4 + 0.002 * np.arange(len(iip)),
            "online_revenue_ratio": 0.1 + 0.001 * np.arange(len(iip)),
            "digital_alignment": "broadcast_latest",
            "financial_alignment": "broadcast_latest",
        }
    )
    df["online_revenue_ratio_x_iip_growth"] = (
        df["online_revenue_ratio"] * df["iip_growth"]
    )
    return df
