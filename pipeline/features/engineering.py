"""Feature engineering for ML models.

Vietnam-first: GSO IIP_C is the target. OECD joins:
- INDIGO @ VNM (annual→monthly step-hold already applied at ingest)
- MEI_IP @ EA20 peer (source=OECD_PEER) as mei_ip — never treat as Vietnam data
- MEI_BCI omitted when unavailable for VNM (no fabrication)
"""

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models import GsoMacro, OecdIndicator
from pipeline.cleaning.cleaner import clean_timeseries

from crawlers.oecd.sdmx_client import PEER_MEI_IP_COUNTRY


def load_macro_dataframe(db: Session) -> pd.DataFrame:
    gso = (
        db.query(GsoMacro)
        .filter(GsoMacro.indicator_code == "IIP_C", GsoMacro.vsic_code == "C")
        .order_by(GsoMacro.period)
        .all()
    )
    gso_df = pd.DataFrame([{"period": r.period, "iip": r.value} for r in gso])

    oecd_dfs = []

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
        oecd_dfs.append(
            pd.DataFrame([{"period": r.period, "indigo": r.value} for r in indigo])
        )

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
        oecd_dfs.append(
            pd.DataFrame(
                [{"period": r.period, "mei_ip": r.value} for r in mei_peer]
            )
        )

    df = gso_df
    for oecd_df in oecd_dfs:
        df = df.merge(oecd_df, on="period", how="outer")

    df = df.sort_values("period").reset_index(drop=True)
    if not df.empty and "iip" in df.columns:
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

    for col in ["mei_ip", "indigo"]:
        if col in df.columns:
            df = add_lag_features(df, col, [1, 2, 3])
            df = add_rolling_features(df, col, [3, 6])

    if "iip" in df.columns:
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
