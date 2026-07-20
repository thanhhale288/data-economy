"""Thin glue: wire DB + features into Wave 1 ARIMA / XGBoost / LSTM trainers."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models import GsoMacro, ModelPrediction, ModelRegistry
from ml.models.arima_model import (
    EXOG_CANDIDATES,
    InsufficientDataError as ArimaInsufficientDataError,
    forecast_arima,
    train_arima_model,
)
from ml.models.lstm_model import (
    InsufficientDataError as LstmInsufficientDataError,
    forecast_lstm,
    train_lstm_model,
)
from ml.models.xgboost_model import forecast_xgboost, train_xgboost_model
from pipeline.features.engineering import build_features

MODELS_DIR = Path(__file__).resolve().parents[2] / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

ARIMA_ARTIFACT = MODELS_DIR / "arima_model.joblib"
XGB_ARTIFACT = MODELS_DIR / "xgboost_model.joblib"
LSTM_ARTIFACT = MODELS_DIR / "lstm_model.pt"


def _get_iip_series(db: Session) -> pd.Series:
    rows = (
        db.query(GsoMacro)
        .filter(GsoMacro.indicator_code == "IIP_C", GsoMacro.vsic_code == "C")
        .order_by(GsoMacro.period)
        .all()
    )
    df = pd.DataFrame([{"period": r.period, "value": r.value} for r in rows])
    df = df.set_index("period")
    return df["value"]


def _exog_from_features(db: Session, series: pd.Series) -> pd.DataFrame | None:
    """Align optional ARIMA exog (indigo, indigo_lag1, mei_ip) to IIP periods."""
    try:
        features = build_features(db)
    except Exception:
        return None
    if features is None or features.empty:
        return None

    cols = [c for c in EXOG_CANDIDATES if c in features.columns]
    if not cols:
        return None

    frame = features[["period", *cols]].copy()
    frame["period"] = pd.to_datetime(frame["period"])
    frame = frame.set_index("period").sort_index()
    aligned = frame.reindex(pd.to_datetime(pd.Index(series.index)))
    if aligned.isna().all(axis=None):
        return None
    return aligned[cols]


def _metrics_only(result: dict) -> dict:
    return {
        "mae": result.get("mae"),
        "rmse": result.get("rmse"),
        "mape": result.get("mape"),
        "status": result.get("status", "ok"),
    }


def _align_preds_to_periods(
    periods: list | None,
    predictions: np.ndarray | list | None,
    actuals: np.ndarray | list | None,
) -> tuple[list, np.ndarray, np.ndarray]:
    """Match lengths for registry rows.

    LSTM may return flattened multi-step windows (n_windows * horizon). When
    lengths differ, truncate all three to the shared min length so one value
    is stored per period without inventing placeholders.
    """
    period_list = list(periods or [])
    preds = np.asarray([] if predictions is None else predictions, dtype=float).ravel()
    acts = np.asarray([] if actuals is None else actuals, dtype=float).ravel()
    n = min(len(period_list), len(preds), len(acts))
    if n == 0:
        return [], np.array([]), np.array([])
    return period_list[:n], preds[:n], acts[:n]


def train_arima(db: Session) -> dict:
    """Train ARIMA/SARIMAX via ``train_arima_model``; register real artifact path.

    Eval uses exog from features when present. The saved full-history fit may
    include those exog cols; ``generate_forecast`` then repeats the last known
    exog row for ``exog_future`` (no growth placeholders).
    """
    series = _get_iip_series(db)
    if series.empty:
        raise ArimaInsufficientDataError("no IIP_C series in database")

    exog = _exog_from_features(db, series)
    result = train_arima_model(series, periods=series.index, exog=exog)

    periods, preds, acts = _align_preds_to_periods(
        result.get("test_periods", []),
        result.get("predictions", []),
        result.get("actuals", []),
    )
    metrics = _metrics_only(result)
    if periods:
        _save_predictions(db, "arima", periods, preds, acts, metrics)
    _register_model(
        db,
        "arima",
        "statistical",
        metrics,
        artifact_path=result["artifact_path"],
    )
    return metrics


def train_xgboost(db: Session) -> dict:
    df = build_features(db)
    result = train_xgboost_model(df)

    if result.get("status") == "insufficient_data":
        return {
            "mae": None,
            "rmse": None,
            "mape": None,
            "status": "insufficient_data",
            "n_train": result.get("n_train", 0),
            "n_test": result.get("n_test", 0),
        }

    periods, preds, acts = _align_preds_to_periods(
        result.get("test_periods", []),
        result.get("predictions", []),
        result.get("actuals", []),
    )
    metrics = _metrics_only(result)
    if periods:
        _save_predictions(db, "xgboost", periods, preds, acts, metrics)
    _register_model(
        db,
        "xgboost",
        "ml",
        metrics,
        artifact_path=result["artifact_path"],
    )
    return metrics


def train_lstm(db: Session) -> dict:
    series = _get_iip_series(db)
    if series.empty:
        raise LstmInsufficientDataError("no IIP_C series in database")

    result = train_lstm_model(series, periods=series.index)

    periods, preds, acts = _align_preds_to_periods(
        result.get("test_periods", []),
        result.get("predictions", []),
        result.get("actuals", []),
    )
    metrics = _metrics_only(result)
    if periods:
        _save_predictions(db, "lstm", periods, preds, acts, metrics)
    _register_model(
        db,
        "lstm",
        "dl",
        metrics,
        artifact_path=result["artifact_path"],
    )
    return metrics


def _save_predictions(db, model_name, periods, preds, actuals, metrics):
    for i, period in enumerate(periods):
        p = pd.Timestamp(period).date() if not isinstance(period, date) else period
        existing = (
            db.query(ModelPrediction)
            .filter(
                ModelPrediction.model_name == model_name,
                ModelPrediction.period == p,
            )
            .first()
        )
        if existing:
            existing.predicted_value = float(preds[i])
            existing.actual_value = float(actuals[i])
            existing.mae = metrics.get("mae")
            existing.rmse = metrics.get("rmse")
            existing.mape = metrics.get("mape")
        else:
            db.add(
                ModelPrediction(
                    model_name=model_name,
                    target_indicator="IIP_C",
                    period=p,
                    predicted_value=float(preds[i]),
                    actual_value=float(actuals[i]),
                    mae=metrics.get("mae"),
                    rmse=metrics.get("rmse"),
                    mape=metrics.get("mape"),
                )
            )
    db.commit()


def _register_model(
    db: Session,
    name: str,
    model_type: str,
    metrics: dict,
    *,
    artifact_path: str | Path,
) -> None:
    db.query(ModelRegistry).filter(ModelRegistry.model_name == name).update(
        {"is_active": False}
    )
    db.add(
        ModelRegistry(
            model_name=name,
            model_type=model_type,
            version="1.0",
            metrics=metrics,
            artifact_path=str(artifact_path),
            is_active=True,
        )
    )
    db.commit()


def train_all_models(db: Session) -> int:
    results = {}
    for name, func in [
        ("arima", train_arima),
        ("xgboost", train_xgboost),
        ("lstm", train_lstm),
    ]:
        try:
            results[name] = func(db)
        except Exception as e:
            results[name] = {"error": str(e), "status": "error"}
    return len(results)


def _advance_periods(last_period, horizon: int) -> list[date]:
    periods: list[date] = []
    for i in range(horizon):
        if isinstance(last_period, date):
            month = last_period.month + i + 1
            year = last_period.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            periods.append(date(year, month, 1))
        else:
            periods.append(
                (pd.Timestamp(last_period) + pd.DateOffset(months=i + 1)).date()
            )
    return periods


def _arima_exog_future(
    artifact: dict,
    db: Session,
    series: pd.Series,
    steps: int,
) -> np.ndarray | None:
    """Repeat last known exog row ``steps`` times when the artifact was fit with exog."""
    exog_cols = artifact.get("exog_cols")
    if not exog_cols:
        return None

    exog_hist = artifact.get("exog_history")
    if exog_hist:
        last_row = np.asarray(exog_hist[-1], dtype=float)
        return np.tile(last_row, (steps, 1))

    # Fallback: last non-null row from live features (same columns).
    live = _exog_from_features(db, series)
    if live is None:
        raise ValueError(
            "ARIMA artifact requires exog_future but no exog_history/features available"
        )
    cols = [c for c in exog_cols if c in live.columns]
    if not cols:
        raise ValueError(
            f"ARIMA artifact exog_cols={exog_cols} not found in features"
        )
    last = live[cols].dropna(how="all").iloc[-1].astype(float).values
    return np.tile(last, (steps, 1))


def generate_forecast(db: Session, model_name: str, horizon: int = 6) -> dict:
    """Forecast from real trained artifacts — never invent growth placeholder lines."""
    if horizon < 1:
        raise ValueError("horizon must be >= 1")

    series = _get_iip_series(db)
    if series.empty:
        raise ValueError("no IIP_C series in database")
    last_period = series.index[-1]

    name = model_name.lower().strip()
    if name == "arima":
        path = ARIMA_ARTIFACT
        if not path.exists():
            raise FileNotFoundError(f"No trained artifact for arima: {path}")
        artifact = joblib.load(path)
        exog_future = _arima_exog_future(artifact, db, series, horizon)
        values = forecast_arima(artifact, steps=horizon, exog_future=exog_future)
    elif name == "xgboost":
        path = XGB_ARTIFACT
        if not path.exists():
            raise FileNotFoundError(f"No trained artifact for xgboost: {path}")
        history_df = build_features(db)
        values = forecast_xgboost(path, history_df=history_df, steps=horizon)
    elif name == "lstm":
        path = LSTM_ARTIFACT
        if not path.exists():
            raise FileNotFoundError(f"No trained artifact for lstm: {path}")
        if horizon > 6:
            raise ValueError(
                f"LSTM horizon={horizon} exceeds trained max of 6; require horizon <= 6"
            )
        values = forecast_lstm(
            MODELS_DIR,
            history=series.values,
            steps=horizon,
        )
    else:
        raise ValueError(f"Unknown model_name={model_name!r}; use arima|xgboost|lstm")

    values = np.asarray(values, dtype=float).ravel()
    if len(values) != horizon:
        raise ValueError(
            f"{name} forecast length {len(values)} != requested horizon {horizon}"
        )

    forecast_periods = _advance_periods(last_period, horizon)
    forecasts = [
        {"period": str(p), "predicted_value": round(float(val), 2)}
        for p, val in zip(forecast_periods, values)
    ]
    return {"model": name, "horizon": horizon, "forecasts": forecasts}
