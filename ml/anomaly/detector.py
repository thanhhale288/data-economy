"""Isolation Forest anomaly detector for univariate macro series (IIP / VA).

Honesty contract:
- Empty / too-short series → available=false, empty points, explicit warning.
- Never invent anomaly flags when there is nothing to score.
- Deterministic via fixed ``random_state`` (same input → same scores/flags).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

DEFAULT_CONTAMINATION = 0.05
DEFAULT_RANDOM_STATE = 42
# Need enough rows after lag/roll feature NaNs drop for a stable fit.
MIN_POINTS = 12
# Sklearn decision_function: scores < 0 are outliers by default.
DECISION_THRESHOLD = 0.0


def _empty_result(
    *,
    warnings: list[str],
    contamination: float,
    n_input: int = 0,
) -> dict[str, Any]:
    return {
        "available": False,
        "method": "isolation_forest",
        "contamination": contamination,
        "threshold": None,
        "n_input": n_input,
        "n_scored": 0,
        "n_anomalies": 0,
        "points": [],
        "warnings": list(warnings),
    }


def build_feature_matrix(series: pd.Series) -> tuple[pd.DataFrame, pd.Index]:
    """Lag / roll / growth features for IsolationForest. Drops incomplete rows."""
    s = pd.to_numeric(series, errors="coerce").astype(float)
    s = s.dropna()
    if s.empty:
        return pd.DataFrame(), pd.Index([])

    frame = pd.DataFrame({"value": s.values}, index=s.index)
    frame["lag1"] = frame["value"].shift(1)
    frame["lag2"] = frame["value"].shift(2)
    frame["lag3"] = frame["value"].shift(3)
    frame["roll3_mean"] = frame["value"].rolling(3, min_periods=3).mean()
    frame["roll3_std"] = frame["value"].rolling(3, min_periods=3).std()
    frame["pct_change"] = frame["value"].pct_change()
    # Replace inf from zero-division in pct_change; leave as NaN then drop.
    frame = frame.replace([np.inf, -np.inf], np.nan)
    clean = frame.dropna()
    return clean, clean.index


def detect_series_anomalies(
    series: pd.Series | None,
    *,
    contamination: float = DEFAULT_CONTAMINATION,
    random_state: int = DEFAULT_RANDOM_STATE,
    min_points: int = MIN_POINTS,
) -> dict[str, Any]:
    """Score a univariate series; never invent alerts on missing/short data.

    Returns a dict with ``available``, ``threshold``, ``points``
    (period / value / score / is_anomaly), and ``warnings``.
    """
    cont = float(contamination)
    if cont <= 0.0 or cont >= 0.5:
        cont = DEFAULT_CONTAMINATION

    if series is None:
        return _empty_result(warnings=["missing_series"], contamination=cont)

    s = pd.to_numeric(pd.Series(series), errors="coerce").dropna()
    n_input = int(len(s))
    if n_input == 0:
        return _empty_result(
            warnings=["empty_series"],
            contamination=cont,
            n_input=0,
        )
    if n_input < min_points:
        return _empty_result(
            warnings=[f"insufficient_points:{n_input}<{min_points}"],
            contamination=cont,
            n_input=n_input,
        )

    features, scored_index = build_feature_matrix(s)
    if features.empty or len(features) < min_points:
        return _empty_result(
            warnings=[
                f"insufficient_feature_rows:{len(features)}<{min_points}",
            ],
            contamination=cont,
            n_input=n_input,
        )

    model = IsolationForest(
        contamination=cont,
        random_state=random_state,
        n_estimators=100,
        n_jobs=1,
    )
    x = features.to_numpy(dtype=float)
    model.fit(x)
    scores = model.decision_function(x)
    preds = model.predict(x)  # -1 anomaly, 1 inlier

    points: list[dict[str, Any]] = []
    n_anomalies = 0
    values = s.reindex(scored_index)
    for period, value, score, pred in zip(
        scored_index, values.to_numpy(), scores, preds, strict=True
    ):
        is_anomaly = bool(pred == -1)
        if is_anomaly:
            n_anomalies += 1
        if hasattr(period, "isoformat"):
            period_str = period.isoformat()
        else:
            period_str = str(period)
        # Normalize datetime64 / Timestamp to date-like ISO (date only when possible).
        if "T" in period_str:
            period_str = period_str.split("T", 1)[0]
        points.append(
            {
                "period": period_str,
                "value": float(value),
                "score": float(score),
                "is_anomaly": is_anomaly,
            }
        )

    return {
        "available": True,
        "method": "isolation_forest",
        "contamination": cont,
        "threshold": DECISION_THRESHOLD,
        "n_input": n_input,
        "n_scored": len(points),
        "n_anomalies": n_anomalies,
        "points": points,
        "warnings": [],
    }
