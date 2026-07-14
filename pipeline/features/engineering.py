"""Feature engineering for ML models."""

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models import GsoMacro, OecdIndicator
from pipeline.cleaning.cleaner import clean_timeseries, resample_quarterly_to_monthly

FEATURES_PATH = __file__.replace("engineering.py", "../../data/processed/features.parquet")


def load_macro_dataframe(db: Session) -> pd.DataFrame:
    gso = (
        db.query(GsoMacro)
        .filter(GsoMacro.indicator_code == "IIP_C", GsoMacro.vsic_code == "C")
        .order_by(GsoMacro.period)
        .all()
    )
    gso_df = pd.DataFrame(
        [{"period": r.period, "iip": r.value} for r in gso]
    )

    oecd_codes = ["MEI_IP", "MEI_BCI", "INDIGO"]
    oecd_dfs = []
    for code in oecd_codes:
        rows = (
            db.query(OecdIndicator)
            .filter(OecdIndicator.indicator_code == code)
            .order_by(OecdIndicator.period)
            .all()
        )
        if rows:
            oecd_dfs.append(
                pd.DataFrame(
                    [{"period": r.period, code.lower(): r.value} for r in rows]
                )
            )

    df = gso_df
    for oecd_df in oecd_dfs:
        df = df.merge(oecd_df, on="period", how="outer")

    df = df.sort_values("period").reset_index(drop=True)
    df = clean_timeseries(df.rename(columns={"iip": "value"}), "value")
    df = df.rename(columns={"value": "iip"})
    return df


def add_lag_features(df: pd.DataFrame, col: str, lags: list[int]) -> pd.DataFrame:
    for lag in lags:
        df[f"{col}_lag{lag}"] = df[col].shift(lag)
    return df


def add_rolling_features(df: pd.DataFrame, col: str, windows: list[int]) -> pd.DataFrame:
    for w in windows:
        df[f"{col}_roll{w}m"] = df[col].rolling(window=w, min_periods=1).mean()
    return df


def build_features(db: Session) -> pd.DataFrame:
    df = load_macro_dataframe(db)

    for col in ["mei_ip", "mei_bci", "indigo"]:
        if col in df.columns:
            df = add_lag_features(df, col, [1, 2, 3])
            df = add_rolling_features(df, col, [3, 6])

    df = add_lag_features(df, "iip", [1, 2, 3])
    df = add_rolling_features(df, "iip", [3, 6])
    df["iip_growth"] = df["iip"].pct_change()
    df = df.dropna()
    return df


def run_feature_engineering(db: Session) -> int:
    from pathlib import Path

    df = build_features(db)
    out_path = Path(__file__).resolve().parents[2] / "data" / "processed" / "features.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    return len(df)
