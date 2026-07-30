"""LightGBM IIP forecaster (Task #58) — mirrors XGBoost train/forecast contract.

Target stays ``iip`` (never silently switched to VA). Soft-fails when the
``lightgbm`` package is missing: train returns ``status="unavailable"`` instead
of crashing the multi-model train loop.

Feature selection and recursive multi-step forecast reuse the XGBoost helpers
so lag/roll/exog behaviour stays aligned across tree models.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ml.evaluation.metrics import compute_all_metrics
from ml.evaluation.walk_forward import (
    TimeSplit,
    evaluate_walk_forward,
    iter_time_splits,
    parse_period_bound,
)
from ml.models.xgboost_model import (
    _IIP_DERIVED,
    _build_next_step_features,
    select_feature_columns,
)

try:
    import lightgbm as lgb

    LIGHTGBM_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised via monkeypatch in tests
    lgb = None  # type: ignore[assignment]
    LIGHTGBM_AVAILABLE = False

MODELS_DIR = Path(__file__).resolve().parents[2] / "data" / "models"

_ARTIFACT_MODEL = "lightgbm_model.joblib"
_ARTIFACT_FEATURES = "lightgbm_features.joblib"
_ARTIFACT_IMPORTANCE = "lightgbm_importance.json"
_FORECAST_MODE = "recursive_one_step"


class InsufficientDataError(ValueError):
    """Raised when train/forecast cannot proceed with the given data/artifact."""


class LightGBMUnavailableError(RuntimeError):
    """Raised when the lightgbm package is not importable."""


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

    cols = (
        feature_cols
        if feature_cols is not None
        else select_feature_columns(df, target_col=target_col)
    )
    if not cols:
        raise InsufficientDataError("No numeric feature columns available")

    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise InsufficientDataError(f"Missing feature columns: {missing}")

    work = df.loc[:, ["period", target_col, *cols]].copy()
    work["period"] = pd.to_datetime(work["period"])
    work = work.sort_values("period").reset_index(drop=True)
    work = work.dropna(subset=[target_col]).reset_index(drop=True)
    return work, cols


def extract_feature_importance(
    model: Any,
    feature_cols: list[str],
) -> dict[str, Any]:
    """Map LightGBM gain/split importance onto real feature column names."""
    booster = model.booster_
    names = list(booster.feature_name() or feature_cols)
    gain_arr = np.asarray(booster.feature_importance(importance_type="gain"), dtype=float)
    split_arr = np.asarray(booster.feature_importance(importance_type="split"), dtype=float)

    gain: dict[str, float] = {c: 0.0 for c in feature_cols}
    weight: dict[str, float] = {c: 0.0 for c in feature_cols}
    for i, name in enumerate(names):
        col = name if name in gain else (feature_cols[i] if i < len(feature_cols) else None)
        if col is None or col not in gain:
            continue
        if i < len(gain_arr):
            gain[col] = float(gain_arr[i])
        if i < len(split_arr):
            weight[col] = float(split_arr[i])
    return {"gain": gain, "weight": weight, "feature_cols": list(feature_cols)}


def save_lightgbm_artifacts(
    artifact: dict[str, Any],
    *,
    artifact_dir: Path | str | None = None,
) -> dict[str, str]:
    """Write lightgbm_model.joblib, lightgbm_features.joblib, lightgbm_importance.json."""
    out_dir = _resolve_artifact_dir(artifact_dir)
    model_path = out_dir / _ARTIFACT_MODEL
    features_path = out_dir / _ARTIFACT_FEATURES
    importance_path = out_dir / _ARTIFACT_IMPORTANCE

    feature_cols = list(artifact["feature_cols"])
    importance = artifact.get("importance") or {
        "gain": {},
        "weight": {},
        "feature_cols": feature_cols,
    }
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


def load_lightgbm_artifact(path: Path | str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(path, dict):
        artifact = path
    else:
        artifact = joblib.load(Path(path))
    if not isinstance(artifact, dict) or "model" not in artifact:
        raise InsufficientDataError(
            "LightGBM artifact must be a dict with at least 'model' and 'feature_cols'"
        )
    if "feature_cols" not in artifact:
        raise InsufficientDataError("LightGBM artifact missing 'feature_cols'")
    return artifact


def _fit_regressor(
    X: pd.DataFrame,
    y: pd.Series | np.ndarray,
    *,
    n_estimators: int,
    max_depth: int,
    learning_rate: float,
) -> Any:
    if not LIGHTGBM_AVAILABLE or lgb is None:
        raise LightGBMUnavailableError(
            "lightgbm package is not installed — skip LightGBM train (soft fail)"
        )
    model = lgb.LGBMRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        random_state=42,
        objective="regression",
        verbosity=-1,
        n_jobs=1,
        force_col_wise=True,
    )
    model.fit(X, y)
    return model


def _unavailable_result(*, artifact_dir: Path) -> dict[str, Any]:
    return {
        "mae": None,
        "rmse": None,
        "mape": None,
        "status": "unavailable",
        "artifact_path": str(artifact_dir / _ARTIFACT_MODEL),
        "features_path": str(artifact_dir / _ARTIFACT_FEATURES),
        "importance_path": str(artifact_dir / _ARTIFACT_IMPORTANCE),
        "feature_cols": [],
        "importance": {"gain": {}, "weight": {}, "feature_cols": []},
        "n_train": 0,
        "n_test": 0,
        "predictions": [],
        "actuals": [],
        "test_periods": [],
        "message": "lightgbm package missing — không train LightGBM (soft fail).",
    }


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


def train_lightgbm_model(
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
    """Train LGBMRegressor with the same chronological split as XGBoost.

    Target defaults to ``iip`` — do not pass VA as target from the train path.
    """
    out_dir = _resolve_artifact_dir(artifact_dir)
    if not LIGHTGBM_AVAILABLE:
        return _unavailable_result(artifact_dir=out_dir)

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
        "kind": "lightgbm",
        "model": model,
        "feature_cols": feature_cols,
        "target": target_col,
        "train_end": train_end_str,
        "importance": {"gain": importance["gain"], "weight": importance["weight"]},
        "forecast_mode": _FORECAST_MODE,
    }
    paths = save_lightgbm_artifacts(artifact, artifact_dir=out_dir)

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


def forecast_lightgbm(
    artifact: dict[str, Any] | Path | str,
    *,
    history_df: pd.DataFrame,
    steps: int = 6,
) -> np.ndarray:
    """Recursive one-step forecast for ``steps`` months (same contract as XGBoost)."""
    if not LIGHTGBM_AVAILABLE:
        raise LightGBMUnavailableError(
            "lightgbm package is not installed — cannot forecast LightGBM"
        )
    if steps < 1:
        raise InsufficientDataError("steps must be >= 1")

    art = load_lightgbm_artifact(artifact)
    model = art["model"]
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
        held_exog = {
            **held_exog,
            **{k: v for k, v in features.items() if k not in _IIP_DERIVED},
        }

    return np.asarray(forecasts, dtype=float)
