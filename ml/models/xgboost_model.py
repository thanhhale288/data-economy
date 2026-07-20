"""XGBoost IIP forecaster with time-based evaluation and recursive multi-step forecast.

Feature selection
-----------------
``select_feature_columns`` keeps numeric columns only, excluding:
- ``period`` (time index)
- target (default ``iip``)
- string provenance: ``digital_alignment``, ``financial_alignment``

Training drops rows with NaN **target** only. Feature NaNs are kept so
``XGBRegressor`` can use native missing-value handling — important when sparse
digital/financial columns are null before late periods (a strict complete-case
dropna on all feature_cols would erase the 2023 train window).
No random split — chronological fixed / walk-forward via ``ml.evaluation.walk_forward``.

Forecast mode: ``recursive_one_step``
-------------------------------------
Multi-step horizons are produced by repeatedly predicting one month ahead and
feeding the prediction back into IIP-derived features:

- Updated from predictions when feasible: ``iip_lag1/2/3``, ``iip_roll3m/6m``,
  ``iip_growth``, and ``online_revenue_ratio_x_iip_growth`` (using held
  ``online_revenue_ratio``).
- Held at last known history value: indigo levels/lags/rolls, digital metrics,
  financial ratios, and any other exogenous numeric columns (including ``mei_ip``
  lags/rolls when present). Those series are not jointly forecasted here.

Limitations: held exogenous features do not evolve over the horizon; recursive
lag/roll updates assume monthly steps and use a simple mean for rolling windows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

from ml.evaluation.metrics import compute_all_metrics
from ml.evaluation.walk_forward import (
    TimeSplit,
    evaluate_walk_forward,
    iter_time_splits,
    parse_period_bound,
)

MODELS_DIR = Path(__file__).resolve().parents[2] / "data" / "models"

_EXCLUDE_ALWAYS = frozenset({"period", "digital_alignment", "financial_alignment"})
_ARTIFACT_MODEL = "xgboost_model.joblib"
_ARTIFACT_FEATURES = "xgboost_features.joblib"
_ARTIFACT_IMPORTANCE = "xgboost_importance.json"
_FORECAST_MODE = "recursive_one_step"


class InsufficientDataError(ValueError):
    """Raised when train/forecast cannot proceed with the given data/artifact."""


def select_feature_columns(df: pd.DataFrame, *, target_col: str = "iip") -> list[str]:
    """Return numeric feature column names suitable for XGBoost training."""
    exclude = _EXCLUDE_ALWAYS | {target_col}
    cols: list[str] = []
    for col in df.columns:
        if col in exclude:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        cols.append(col)
    return cols


def _resolve_artifact_dir(artifact_dir: Path | str | None) -> Path:
    path = MODELS_DIR if artifact_dir is None else Path(artifact_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _prepare_frame(
    df: pd.DataFrame,
    *,
    target_col: str,
    feature_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    if target_col not in df.columns:
        raise InsufficientDataError(f"Missing target column {target_col!r}")
    if "period" not in df.columns:
        raise InsufficientDataError("Missing period column")

    cols = feature_cols if feature_cols is not None else select_feature_columns(df, target_col=target_col)
    if not cols:
        raise InsufficientDataError("No numeric feature columns available")

    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise InsufficientDataError(f"Missing feature columns: {missing}")

    work = df.loc[:, ["period", target_col, *cols]].copy()
    work["period"] = pd.to_datetime(work["period"])
    work = work.sort_values("period").reset_index(drop=True)
    # Target must be observed; feature NaNs intentionally retained for XGBoost.
    work = work.dropna(subset=[target_col]).reset_index(drop=True)
    return work, cols


def _map_importance_scores(
    raw: dict[str, float],
    feature_cols: list[str],
) -> dict[str, float]:
    mapped: dict[str, float] = {c: 0.0 for c in feature_cols}
    for key, value in raw.items():
        if key in mapped:
            mapped[key] = float(value)
            continue
        if key.startswith("f") and key[1:].isdigit():
            idx = int(key[1:])
            if 0 <= idx < len(feature_cols):
                mapped[feature_cols[idx]] = float(value)
    return mapped


def extract_feature_importance(
    model: xgb.XGBRegressor,
    feature_cols: list[str],
) -> dict[str, Any]:
    booster = model.get_booster()
    gain = _map_importance_scores(booster.get_score(importance_type="gain"), feature_cols)
    weight = _map_importance_scores(booster.get_score(importance_type="weight"), feature_cols)
    return {"gain": gain, "weight": weight, "feature_cols": list(feature_cols)}


def save_xgboost_artifacts(
    artifact: dict[str, Any],
    *,
    artifact_dir: Path | str | None = None,
) -> dict[str, str]:
    """Write ``xgboost_model.joblib``, ``xgboost_features.joblib``, ``xgboost_importance.json``."""
    out_dir = _resolve_artifact_dir(artifact_dir)
    model_path = out_dir / _ARTIFACT_MODEL
    features_path = out_dir / _ARTIFACT_FEATURES
    importance_path = out_dir / _ARTIFACT_IMPORTANCE

    feature_cols = list(artifact["feature_cols"])
    importance = artifact.get("importance") or {"gain": {}, "weight": {}, "feature_cols": feature_cols}
    if "feature_cols" not in importance:
        importance = {**importance, "feature_cols": feature_cols}

    joblib.dump(artifact, model_path)
    joblib.dump(feature_cols, features_path)
    importance_path.write_text(
        json.dumps(importance, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {
        "artifact_path": str(model_path),
        "features_path": str(features_path),
        "importance_path": str(importance_path),
    }


def load_xgboost_artifact(path: Path | str | dict[str, Any]) -> dict[str, Any]:
    """Load a wrapped XGBoost artifact dict from path or pass through an in-memory dict."""
    if isinstance(path, dict):
        artifact = path
    else:
        artifact = joblib.load(Path(path))
    if not isinstance(artifact, dict) or "model" not in artifact:
        raise InsufficientDataError(
            "XGBoost artifact must be a dict with at least 'model' and 'feature_cols'"
        )
    if "feature_cols" not in artifact:
        raise InsufficientDataError("XGBoost artifact missing 'feature_cols'")
    return artifact


def _fit_regressor(
    X: pd.DataFrame,
    y: pd.Series | np.ndarray,
    *,
    n_estimators: int,
    max_depth: int,
    learning_rate: float,
) -> xgb.XGBRegressor:
    model = xgb.XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        random_state=42,
        objective="reg:squarederror",
        n_jobs=1,  # avoid OpenMP segfaults on some macOS / CI runners
    )
    model.fit(X, y)
    return model


def _insufficient_result(
    *,
    feature_cols: list[str],
    artifact_dir: Path,
    n_train: int = 0,
    n_test: int = 0,
) -> dict[str, Any]:
    return {
        "mae": None,
        "rmse": None,
        "mape": None,
        "status": "insufficient_data",
        "artifact_path": str(artifact_dir / _ARTIFACT_MODEL),
        "features_path": str(artifact_dir / _ARTIFACT_FEATURES),
        "importance_path": str(artifact_dir / _ARTIFACT_IMPORTANCE),
        "feature_cols": feature_cols,
        "importance": {"gain": {}, "weight": {}, "feature_cols": feature_cols},
        "n_train": n_train,
        "n_test": n_test,
        "predictions": [],
        "actuals": [],
        "test_periods": [],
    }


def train_xgboost_model(
    df: pd.DataFrame,
    *,
    target_col: str = "iip",
    train_end: str | None = "2023-12",
    test_start: str | None = "2024-01",
    min_train_size: int = 24,
    artifact_dir: Path | str | None = None,
    n_estimators: int = 100,
    max_depth: int = 4,
    learning_rate: float = 0.1,
) -> dict[str, Any]:
    """Train XGBRegressor with fixed chronological split (default train≤2023-12, test≥2024-01).

    Rows with NaN target are dropped before splitting; feature NaNs are retained
    for XGBoost missing-value handling (see module docstring).
    On insufficient data returns ``status="insufficient_data"`` with metrics None
    (never fabricated zeros). Raises ``InsufficientDataError`` for malformed input.
    """
    out_dir = _resolve_artifact_dir(artifact_dir)
    work, feature_cols = _prepare_frame(df, target_col=target_col)

    periods = work["period"]
    y = work[target_col]
    X = work[feature_cols]

    splits = list(
        iter_time_splits(
            periods,
            train_end=train_end,
            test_start=test_start,
            min_train_size=min_train_size,
            mode="fixed",
        )
    )
    if not splits:
        return _insufficient_result(feature_cols=feature_cols, artifact_dir=out_dir)

    split = splits[0]
    n_train = int(len(split.train_indices))
    n_test = int(len(split.test_indices))
    if n_train < min_train_size or n_test < 1:
        return _insufficient_result(
            feature_cols=feature_cols,
            artifact_dir=out_dir,
            n_train=n_train,
            n_test=n_test,
        )

    def predict_fn(s: TimeSplit) -> np.ndarray:
        model = _fit_regressor(
            X.iloc[s.train_indices],
            y.iloc[s.train_indices],
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
        )
        return np.asarray(model.predict(X.iloc[s.test_indices]), dtype=float)

    wf = evaluate_walk_forward(
        periods,
        y.values,
        predict_fn,
        train_end=train_end,
        test_start=test_start,
        min_train_size=min_train_size,
        mode="fixed",
    )
    if wf.get("status") != "ok":
        return _insufficient_result(
            feature_cols=feature_cols,
            artifact_dir=out_dir,
            n_train=n_train,
            n_test=n_test,
        )

    # Final model on the train fold; one-step preds on test (precomputed features).
    model = _fit_regressor(
        X.iloc[split.train_indices],
        y.iloc[split.train_indices],
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
    )
    preds = np.asarray(model.predict(X.iloc[split.test_indices]), dtype=float)
    actuals = np.asarray(y.iloc[split.test_indices], dtype=float)
    metrics = compute_all_metrics(actuals, preds)
    importance = extract_feature_importance(model, feature_cols)

    train_end_ts = split.train_end
    if train_end_ts is None and train_end is not None:
        train_end_ts = parse_period_bound(train_end)
    train_end_str = (
        train_end_ts.strftime("%Y-%m")
        if isinstance(train_end_ts, pd.Timestamp)
        else (str(train_end) if train_end else None)
    )

    artifact = {
        "kind": "xgboost",
        "model": model,
        "feature_cols": feature_cols,
        "target": target_col,
        "train_end": train_end_str,
        "importance": {"gain": importance["gain"], "weight": importance["weight"]},
        "forecast_mode": _FORECAST_MODE,
    }
    paths = save_xgboost_artifacts(artifact, artifact_dir=out_dir)

    test_periods = [
        pd.Timestamp(p).strftime("%Y-%m-%d")
        for p in periods.iloc[split.test_indices].tolist()
    ]
    return {
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "mape": metrics["mape"],
        "status": "ok",
        "artifact_path": paths["artifact_path"],
        "features_path": paths["features_path"],
        "importance_path": paths["importance_path"],
        "feature_cols": feature_cols,
        "importance": importance,
        "n_train": n_train,
        "n_test": n_test,
        "predictions": preds.tolist(),
        "actuals": actuals.tolist(),
        "test_periods": test_periods,
    }


# Columns recomputed from the IIP path during recursive multi-step forecast.
_IIP_DERIVED = frozenset(
    {
        "iip_lag1",
        "iip_lag2",
        "iip_lag3",
        "iip_roll3m",
        "iip_roll6m",
        "iip_growth",
        "online_revenue_ratio_x_iip_growth",
    }
)


def _rolling_mean(values: list[float], window: int) -> float:
    if not values:
        raise InsufficientDataError("Cannot compute rolling mean on empty IIP history")
    use = values[-window:] if len(values) >= window else values
    return float(np.mean(use))


def _build_next_step_features(
    *,
    feature_cols: list[str],
    held_exog: dict[str, float],
    iip_history: list[float],
) -> dict[str, float]:
    """Feature vector for the month immediately after ``iip_history[-1]``."""
    if len(iip_history) < 1:
        raise InsufficientDataError("history_df must include at least one iip value")

    row: dict[str, float] = {}
    for col in feature_cols:
        if col in _IIP_DERIVED:
            continue
        # Hold last known exogenous; NaN allowed (XGBoost native missing handling).
        val = held_exog.get(col, np.nan)
        row[col] = float(val) if val is not None and not pd.isna(val) else float("nan")

    if "iip_lag1" in feature_cols:
        row["iip_lag1"] = float(iip_history[-1])
    if "iip_lag2" in feature_cols:
        row["iip_lag2"] = float(iip_history[-2]) if len(iip_history) >= 2 else float(iip_history[-1])
    if "iip_lag3" in feature_cols:
        row["iip_lag3"] = float(iip_history[-3]) if len(iip_history) >= 3 else float(iip_history[0])
    if "iip_roll3m" in feature_cols:
        row["iip_roll3m"] = _rolling_mean(iip_history, 3)
    if "iip_roll6m" in feature_cols:
        row["iip_roll6m"] = _rolling_mean(iip_history, 6)
    if "iip_growth" in feature_cols:
        prev = iip_history[-2] if len(iip_history) >= 2 else iip_history[-1]
        cur = iip_history[-1]
        row["iip_growth"] = float((cur - prev) / prev) if prev != 0 else 0.0
    if "online_revenue_ratio_x_iip_growth" in feature_cols:
        orr = row.get("online_revenue_ratio", held_exog.get("online_revenue_ratio", np.nan))
        growth = row.get("iip_growth", np.nan)
        if orr is None or pd.isna(orr) or growth is None or pd.isna(growth):
            row["online_revenue_ratio_x_iip_growth"] = float("nan")
        else:
            row["online_revenue_ratio_x_iip_growth"] = float(orr) * float(growth)

    for col in feature_cols:
        if col not in row:
            raise InsufficientDataError(f"Incomplete recursive feature row; missing {col!r}")
    return row


def forecast_xgboost(
    artifact: dict[str, Any] | Path | str,
    *,
    history_df: pd.DataFrame,
    steps: int = 6,
) -> np.ndarray:
    """Recursive one-step forecast for ``steps`` months.

    ``history_df`` must include the artifact feature columns and ``iip`` for recent
    rows. Returns shape ``(steps,)``. Never invents a growth line on failure.
    """
    if steps < 1:
        raise InsufficientDataError("steps must be >= 1")

    art = load_xgboost_artifact(artifact)
    model: xgb.XGBRegressor = art["model"]
    feature_cols: list[str] = list(art["feature_cols"])
    target_col = art.get("target", "iip")

    if history_df is None or history_df.empty:
        raise InsufficientDataError("history_df is empty")
    if target_col not in history_df.columns:
        raise InsufficientDataError(f"history_df missing target {target_col!r}")

    missing = [c for c in feature_cols if c not in history_df.columns]
    if missing:
        raise InsufficientDataError(f"history_df missing feature columns: {missing}")

    hist = history_df.copy()
    if "period" in hist.columns:
        hist["period"] = pd.to_datetime(hist["period"])
        hist = hist.sort_values("period").reset_index(drop=True)
    else:
        hist = hist.reset_index(drop=True)

    hist = hist.dropna(subset=[target_col]).reset_index(drop=True)
    if hist.empty:
        raise InsufficientDataError("history_df has no non-NaN iip rows")

    complete = hist.dropna(subset=feature_cols)
    seed_row = complete.iloc[-1] if not complete.empty else hist.iloc[-1]
    held_exog = {
        c: float(seed_row[c])
        for c in feature_cols
        if c not in _IIP_DERIVED and c in seed_row.index and pd.notna(seed_row[c])
    }
    # Keep optional held copies of IIP-derived cols only as fallback seeds for exog cross terms.
    for c in feature_cols:
        if c in _IIP_DERIVED and c in seed_row.index and pd.notna(seed_row[c]):
            held_exog.setdefault(c, float(seed_row[c]))

    iip_history = [float(v) for v in hist[target_col].tolist() if pd.notna(v)]
    if len(iip_history) < 1:
        raise InsufficientDataError("Need at least one iip observation in history_df")

    forecasts: list[float] = []
    for _ in range(steps):
        features = _build_next_step_features(
            feature_cols=feature_cols,
            held_exog=held_exog,
            iip_history=iip_history,
        )
        X_row = pd.DataFrame([[features[c] for c in feature_cols]], columns=feature_cols)
        pred = float(np.asarray(model.predict(X_row), dtype=float)[0])
        forecasts.append(pred)
        iip_history.append(pred)
        # Exogenous held values stay fixed; IIP-derived cols refresh each step from iip_history.
        held_exog = {**held_exog, **{k: v for k, v in features.items() if k not in _IIP_DERIVED}}

    return np.asarray(forecasts, dtype=float)
