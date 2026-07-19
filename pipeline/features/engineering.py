"""Feature engineering for ML models.

Vietnam-first: GSO IIP_C is the target. OECD joins:
- INDIGO @ VNM (annual→monthly step-hold already applied at ingest)
- MEI_IP @ EA20 peer (source=OECD_PEER) as mei_ip — never treat as Vietnam data
- MEI_BCI omitted when unavailable for VNM (no fabrication)

Cleaning ownership: Task #10 ``data_cleaning`` owns the primary clean and writes
``data/processed/cleaned_macro.parquet``. ``load_macro_dataframe`` prefers that
artifact when present; the DB + ``clean_timeseries`` path is a fallback for
ad-hoc runs that skip the cleaning job (avoids silent double-clean when the
artifact exists).

Task #11 joins digital + financial aggregates (mean across seed firms) onto the
monthly macro calendar. Sparse firm snapshots use documented broadcast /
step-hold alignment — they are not invented monthly observations.
``dropna`` only applies to required IIP lag columns so digital/financial NaNs
are preserved for later models.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models import GsoMacro, OecdIndicator
from crawlers.oecd.sdmx_client import PEER_MEI_IP_COUNTRY
from pipeline.cleaning.cleaner import clean_timeseries
from pipeline.features.digital_features import (
    DIGITAL_FEATURE_COLUMNS,
    digital_features_for_calendar,
)
from pipeline.features.financial_features import (
    FINANCIAL_FEATURE_COLUMNS,
    financial_features_for_calendar,
)
from pipeline.features.macro_helpers import add_lag_features, add_rolling_features
from pipeline.features.validation import (
    CROSS_FEATURE_COLUMNS,
    validate_feature_frame,
)

_PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
_CLEANED_MACRO_PATH = _PROCESSED_DIR / "cleaned_macro.parquet"
_FEATURES_PATH = _PROCESSED_DIR / "features.parquet"
_MANIFEST_PATH = _PROCESSED_DIR / "features_manifest.json"

_IIP_DROPNA_SUBSET = ("iip", "iip_lag1", "iip_lag2", "iip_lag3")
_CROSS_COL = CROSS_FEATURE_COLUMNS[0]


def _usable_cleaned_macro(path: Path) -> pd.DataFrame | None:
    """Return cleaned macro artifact only if it has rows and an ``iip`` column."""
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path)
    except Exception:
        return None
    if df.empty or "iip" not in df.columns:
        return None
    return df


def _normalize_period(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce ``period`` to month-start timestamps for joins."""
    if df.empty or "period" not in df.columns:
        return df
    out = df.copy()
    out["period"] = (
        pd.to_datetime(out["period"], errors="coerce")
        .dt.to_period("M")
        .dt.to_timestamp()
    )
    return out.dropna(subset=["period"]).sort_values("period").reset_index(drop=True)


def load_macro_dataframe(db: Session) -> pd.DataFrame:
    # Prefer Task #10 cleaned artifact; fallback cleans from DB for ad-hoc use.
    # Ignore empty/partial artifacts so a failed clean smoke cannot poison features.
    cleaned = _usable_cleaned_macro(_CLEANED_MACRO_PATH)
    if cleaned is not None:
        df = _normalize_period(cleaned)
        # Never carry fabricated BCI from a stale artifact.
        if "mei_bci" in df.columns:
            df = df.drop(columns=["mei_bci"])
        return df

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

    df = _normalize_period(df)
    if not df.empty and "iip" in df.columns:
        df = clean_timeseries(df.rename(columns={"iip": "value"}), "value")
        df = df.rename(columns={"value": "iip"})
    return df


def _left_join_features(macro: pd.DataFrame, extra: pd.DataFrame) -> pd.DataFrame:
    if extra.empty:
        return macro
    extra = _normalize_period(extra)
    return macro.merge(extra, on="period", how="left")


def _add_cross_features(df: pd.DataFrame) -> pd.DataFrame:
    if "online_revenue_ratio" in df.columns and "iip_growth" in df.columns:
        df[_CROSS_COL] = df["online_revenue_ratio"] * df["iip_growth"]
    return df


def _dropna_required_iip_lags(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows missing IIP target lags only; keep sparse digital/financial NaNs."""
    subset = [col for col in _IIP_DROPNA_SUBSET if col in df.columns]
    if not subset:
        return df
    return df.dropna(subset=subset).reset_index(drop=True)


def build_features(db: Session, *, validate: bool = True) -> pd.DataFrame:
    """Build monthly feature frame: macro lags/rolls + digital + financial + cross."""
    df = load_macro_dataframe(db)

    for col in ["mei_ip", "indigo"]:
        if col in df.columns:
            df = add_lag_features(df, col, [1, 2, 3])
            df = add_rolling_features(df, col, [3, 6])

    if "iip" in df.columns:
        df = add_lag_features(df, "iip", [1, 2, 3])
        df = add_rolling_features(df, "iip", [3, 6])
        df["iip_growth"] = df["iip"].pct_change()

    calendar = df["period"] if "period" in df.columns else []
    df = _left_join_features(df, digital_features_for_calendar(db, calendar))
    df = _left_join_features(df, financial_features_for_calendar(db, calendar))
    df = _add_cross_features(df)

    # Validate lag identity on the full monthly frame before trimming warm-up rows.
    if validate and not df.empty:
        validate_feature_frame(df)
    return _dropna_required_iip_lags(df)


def _manifest_for(df: pd.DataFrame) -> dict[str, Any]:
    columns = list(df.columns)
    digital_present = all(col in df.columns for col in DIGITAL_FEATURE_COLUMNS)
    financial_present = all(col in df.columns for col in FINANCIAL_FEATURE_COLUMNS)
    notes: list[str] = [
        "dropna only on IIP lag subset; digital/financial NaNs preserved",
        "MEI_BCI never fabricated; mei_ip is OECD peer EA20 when present",
        f"mei_ip_peer_country={PEER_MEI_IP_COUNTRY}",
    ]
    if "digital_alignment" in df.columns:
        notes.append(
            "digital_alignment="
            + ",".join(sorted(df["digital_alignment"].dropna().astype(str).unique()))
        )
    elif not digital_present:
        notes.append("digital features absent (no digital_metrics rows)")
    if "financial_alignment" in df.columns:
        notes.append(
            "financial_alignment="
            + ",".join(
                sorted(df["financial_alignment"].dropna().astype(str).unique())
            )
        )
    elif not financial_present:
        notes.append("financial features absent (no financial_reports rows)")

    return {
        "columns": columns,
        "row_count": int(len(df)),
        "sources": {
            "macro": "cleaned_macro.parquet preferred; else DB GSO IIP_C + INDIGO@VNM + MEI_IP@EA20",
            "digital": "digital_metrics mean across firms; broadcast_latest or period_aggregate",
            "financial": "financial_reports ratios mean; step-hold or broadcast_latest",
            "cross": _CROSS_COL if _CROSS_COL in columns else None,
        },
        "feature_groups": {
            "macro_present": [c for c in ("iip", "indigo", "mei_ip") if c in columns],
            "digital_present": digital_present,
            "financial_present": financial_present,
            "cross_present": _CROSS_COL in columns,
        },
        "mei_ip_peer_country": PEER_MEI_IP_COUNTRY,
        "dropna_subset": [c for c in _IIP_DROPNA_SUBSET if c in columns],
        "notes": notes,
    }


def run_feature_engineering(db: Session) -> int:
    df = build_features(db)
    _PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_FEATURES_PATH, index=False)
    _MANIFEST_PATH.write_text(
        json.dumps(_manifest_for(df), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return len(df)
