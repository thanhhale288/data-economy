"""Pure, order-preserving macro feature helpers.

Callers must sort their frame chronologically before using these helpers.  The
rolling mean includes the current observation and prior observations available
inside its window (``min_periods=1``); it never uses future observations.
"""

import pandas as pd


def add_lag_features(df: pd.DataFrame, col: str, lags: list[int]) -> pd.DataFrame:
    """Add ``{col}_lag{lag}`` columns using pandas ``shift``."""
    for lag in lags:
        df[f"{col}_lag{lag}"] = df[col].shift(lag)
    return df


def add_rolling_features(
    df: pd.DataFrame, col: str, windows: list[int]
) -> pd.DataFrame:
    """Add trailing rolling means using available past and current values."""
    for window in windows:
        df[f"{col}_roll{window}m"] = df[col].rolling(
            window=window, min_periods=1
        ).mean()
    return df
