"""Real ARIMA/SARIMAX for monthly IIP Section C (statsmodels; not EMA).

Baseline order
--------------
ARIMA(1, 1, 1) per CONTEXT.md / proposal-v2. On fit failure, falls back once to
ARIMA(1, 1, 0). With aligned exogenous columns uses SARIMAX (same non-seasonal
order; ``seasonal_order=None`` / (0,0,0,0)).

Optional exogenous (used only if present and row-aligned; never invent mei_bci)
------------------------------------------------------------------------------
``indigo``, ``indigo_lag1``, ``mei_ip``.

Artifact schema (``data/models/arima_model.joblib``)
----------------------------------------------------
::

    {
      "kind": "arima" | "sarimax",
      "order": (p, d, q),
      "seasonal_order": None | (P, D, Q, s),
      "exog_cols": list[str] | None,
      "fitted_params": dict[str, float],
      "model_results": <statsmodels results>,  # primary forecast engine
      "train_end_period": str,   # YYYY-MM of last train observation used in eval
      "last_period": str,        # YYYY-MM of last observation in fitted history
      "history_values": list[float],
      "history_periods": list[str],
      "exog_history": list[list[float]] | None,  # rows aligned to history
    }

``forecast_arima`` loads the artifact (if path) and returns ``np.ndarray`` of
shape ``(steps,)`` via ``model_results.forecast`` (real ARIMA/SARIMAX, not EMA).

Train / eval
------------
Uses ``ml.evaluation.walk_forward`` (fixed holdout default ``train_end=2023-12``,
``test_start=2024-01`` when those months exist; else last ``test_size`` months).
Raises ``InsufficientDataError`` when the series is too short to fit or no
valid chronological split exists.

Note: a small scipy/statsmodels shim strips the removed ``disp`` kwarg from
``fmin_l_bfgs_b`` so default L-BFGS fits work on scipy>=1.15.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import joblib
import numpy as np
import pandas as pd
import scipy.optimize as sco
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

from ml.evaluation.metrics import compute_all_metrics
from ml.evaluation.walk_forward import TimeSplit, evaluate_walk_forward, iter_time_splits

MODELS_DIR = Path(__file__).resolve().parents[2] / "data" / "models"
DEFAULT_ARTIFACT_PATH = MODELS_DIR / "arima_model.joblib"
DEFAULT_ORDER: tuple[int, int, int] = (1, 1, 1)
FALLBACK_ORDER: tuple[int, int, int] = (1, 1, 0)
EXOG_CANDIDATES: tuple[str, ...] = ("indigo", "indigo_lag1", "mei_ip")
DEFAULT_TEST_SIZE = 6


class InsufficientDataError(ValueError):
    """Raised when the IIP series is too short to fit or no valid time split exists."""


def _period_str(value: Any) -> str:
    ts = pd.Timestamp(value)
    return f"{ts.year:04d}-{ts.month:02d}"


def _to_month_period_index(periods: pd.Series | pd.DatetimeIndex | np.ndarray | list) -> pd.DatetimeIndex:
    idx = pd.to_datetime(pd.Index(periods))
    return pd.DatetimeIndex(idx.to_period("M").to_timestamp())


def _select_exog(exog: pd.DataFrame | None) -> tuple[pd.DataFrame | None, list[str] | None]:
    if exog is None or exog.empty:
        return None, None
    cols = [c for c in EXOG_CANDIDATES if c in exog.columns]
    if not cols:
        return None, None
    frame = exog[cols].apply(pd.to_numeric, errors="coerce")
    if frame.isna().all(axis=None):
        return None, None
    return frame, cols


def _align_inputs(
    series: pd.Series,
    periods: pd.Series | pd.DatetimeIndex | None,
    exog: pd.DataFrame | None,
) -> tuple[np.ndarray, pd.DatetimeIndex, pd.DataFrame | None, list[str] | None]:
    if periods is None:
        if isinstance(series.index, pd.DatetimeIndex) or len(series.index):
            period_index = _to_month_period_index(series.index)
        else:
            raise InsufficientDataError("series has no period index; pass periods=")
    else:
        period_index = _to_month_period_index(periods)

    y = np.asarray(series, dtype=float).reshape(-1)
    if len(y) != len(period_index):
        raise InsufficientDataError(
            f"series length ({len(y)}) != periods length ({len(period_index)})"
        )

    order = np.argsort(period_index.values)
    period_index = period_index[order]
    y = y[order]

    exog_frame, exog_cols = _select_exog(exog)
    if exog_frame is not None:
        if len(exog_frame) != len(y):
            raise InsufficientDataError(
                f"exog length ({len(exog_frame)}) != series length ({len(y)})"
            )
        exog_frame = exog_frame.iloc[order].reset_index(drop=True)
        # Drop rows with any NaN in selected exog to keep SARIMAX aligned
        valid = ~exog_frame.isna().any(axis=1).to_numpy()
        if valid.sum() < len(y):
            y = y[valid]
            period_index = period_index[valid]
            exog_frame = exog_frame.loc[valid].reset_index(drop=True)
        if exog_frame.empty or len(y) == 0:
            exog_frame, exog_cols = None, None

    return y, period_index, exog_frame, exog_cols


def _bounds_available(
    periods: pd.DatetimeIndex,
    train_end: str | None,
    test_start: str | None,
    min_train_size: int,
) -> bool:
    if train_end is None and test_start is None:
        return False
    months = periods.to_period("M")
    if train_end is not None:
        te = pd.Timestamp(train_end).to_period("M")
        n_train = int((months <= te).sum())
        if n_train < min_train_size:
            return False
    if test_start is not None:
        ts = pd.Timestamp(test_start).to_period("M")
        if int((months >= ts).sum()) < 1:
            return False
    if train_end is not None and test_start is not None:
        te = pd.Timestamp(train_end).to_period("M")
        ts = pd.Timestamp(test_start).to_period("M")
        if ts <= te:
            return False
    return True


@contextmanager
def _scipy_lbfgs_disp_compat() -> Iterator[None]:
    """scipy>=1.15 dropped ``disp`` on fmin_l_bfgs_b; statsmodels 0.14 still passes it."""
    original = sco.fmin_l_bfgs_b

    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        kwargs.pop("disp", None)
        return original(*args, **kwargs)

    sco.fmin_l_bfgs_b = _wrapped  # type: ignore[assignment]
    try:
        yield
    finally:
        sco.fmin_l_bfgs_b = original


def _fit_arima(
    endog: np.ndarray,
    exog: np.ndarray | pd.DataFrame | None,
    order: tuple[int, int, int],
) -> tuple[Any, tuple[int, int, int], str]:
    """Fit ARIMA or SARIMAX; on failure with baseline order, retry FALLBACK_ORDER once."""
    orders_to_try = [order]
    if order != FALLBACK_ORDER:
        orders_to_try.append(FALLBACK_ORDER)

    last_err: Exception | None = None
    for candidate in orders_to_try:
        try:
            with _scipy_lbfgs_disp_compat():
                if exog is None:
                    model = ARIMA(endog, order=candidate)
                    results = model.fit()
                    return results, candidate, "arima"
                exog_arr = np.asarray(exog, dtype=float)
                model = SARIMAX(
                    endog,
                    exog=exog_arr,
                    order=candidate,
                    seasonal_order=(0, 0, 0, 0),
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )
                results = model.fit(disp=False)
                return results, candidate, "sarimax"
        except Exception as exc:  # noqa: BLE001 — fall back once, then raise
            last_err = exc
            continue
    raise RuntimeError(f"ARIMA/SARIMAX fit failed for orders {orders_to_try}: {last_err}")


def _exog_slice(
    exog: pd.DataFrame | None,
    indices: np.ndarray,
) -> np.ndarray | None:
    if exog is None:
        return None
    return np.asarray(exog.iloc[np.asarray(indices, dtype=int)], dtype=float)


def _forecast_from_results(
    results: Any,
    steps: int,
    exog_future: np.ndarray | pd.DataFrame | None,
) -> np.ndarray:
    if steps < 1:
        return np.asarray([], dtype=float)
    kwargs: dict[str, Any] = {}
    if exog_future is not None:
        arr = np.asarray(exog_future, dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        if arr.shape[0] != steps:
            raise ValueError(
                f"exog_future rows ({arr.shape[0]}) must equal steps ({steps})"
            )
        kwargs["exog"] = arr
    fc = results.forecast(steps=steps, **kwargs)
    out = np.asarray(fc, dtype=float).reshape(-1)
    if out.shape != (steps,):
        raise RuntimeError(f"forecast shape {out.shape} != ({steps},)")
    return out


def _params_dict(results: Any) -> dict[str, float]:
    try:
        params = results.params
        if hasattr(params, "items"):
            return {str(k): float(v) for k, v in params.items()}
        return {f"p{i}": float(v) for i, v in enumerate(np.asarray(params).ravel())}
    except Exception:  # noqa: BLE001
        return {}


def _build_artifact(
    *,
    results: Any,
    kind: str,
    order: tuple[int, int, int],
    exog_cols: list[str] | None,
    y: np.ndarray,
    periods: pd.DatetimeIndex,
    exog: pd.DataFrame | None,
    train_end_period: str,
) -> dict[str, Any]:
    exog_history = None
    if exog is not None and exog_cols:
        exog_history = np.asarray(exog, dtype=float).tolist()
    return {
        "kind": kind,
        "order": tuple(int(x) for x in order),
        "seasonal_order": None,
        "exog_cols": list(exog_cols) if exog_cols else None,
        "fitted_params": _params_dict(results),
        "model_results": results,
        "train_end_period": train_end_period,
        "last_period": _period_str(periods[-1]),
        "history_values": [float(v) for v in y],
        "history_periods": [_period_str(p) for p in periods],
        "exog_history": exog_history,
    }


def save_arima_artifact(artifact: dict, path: Path | str) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, out)
    return out


def load_arima_artifact(path: Path | str) -> dict:
    artifact = joblib.load(Path(path))
    if not isinstance(artifact, dict):
        raise TypeError(f"ARIMA artifact must be a dict, got {type(artifact)}")
    if "model_results" not in artifact and "history_values" not in artifact:
        raise ValueError("ARIMA artifact missing model_results/history_values")
    return artifact


def forecast_arima(
    artifact: dict | Path | str,
    steps: int = 6,
    *,
    exog_future: np.ndarray | pd.DataFrame | None = None,
) -> np.ndarray:
    """Load if path; return shape (steps,) float forecasts via statsmodels."""
    if not isinstance(artifact, dict):
        artifact = load_arima_artifact(artifact)

    results = artifact.get("model_results")
    if results is not None:
        return _forecast_from_results(results, steps, exog_future)

    # Refit from stored history if results were not persisted
    history = np.asarray(artifact["history_values"], dtype=float)
    order = tuple(artifact.get("order") or DEFAULT_ORDER)
    exog_hist = artifact.get("exog_history")
    exog_arr = np.asarray(exog_hist, dtype=float) if exog_hist is not None else None
    results, _, _ = _fit_arima(history, exog_arr, order)  # type: ignore[arg-type]
    return _forecast_from_results(results, steps, exog_future)


def train_arima_model(
    series: pd.Series,
    *,
    periods: pd.Series | pd.DatetimeIndex | None = None,
    exog: pd.DataFrame | None = None,
    order: tuple[int, int, int] = DEFAULT_ORDER,
    train_end: str | None = "2023-12",
    test_start: str | None = "2024-01",
    min_train_size: int = 24,
    artifact_path: Path | str | None = None,
) -> dict:
    """Fit ARIMA(1,1,1) (or fallback), evaluate on a fixed chronological holdout, save artifact.

    Raises
    ------
    InsufficientDataError
        If the series is too short to fit or walk-forward yields no valid split.
    """
    y, period_index, exog_frame, exog_cols = _align_inputs(series, periods, exog)

    if len(y) < min_train_size + 1:
        raise InsufficientDataError(
            f"need at least min_train_size+1={min_train_size + 1} points, got {len(y)}"
        )

    use_calendar = _bounds_available(period_index, train_end, test_start, min_train_size)
    te = train_end if use_calendar else None
    ts = test_start if use_calendar else None

    splits = list(
        iter_time_splits(
            period_index,
            train_end=te,
            test_start=ts,
            min_train_size=min_train_size,
            test_size=DEFAULT_TEST_SIZE,
            mode="fixed",
        )
    )
    if not splits:
        raise InsufficientDataError("no valid chronological train/test split")

    split0 = splits[0]
    state: dict[str, Any] = {"order_used": order, "kind": "arima"}

    def predict_fn(split: TimeSplit) -> np.ndarray:
        y_train = y[split.train_indices]
        exog_train = _exog_slice(exog_frame, split.train_indices)
        results, order_used, kind = _fit_arima(y_train, exog_train, order)
        state["order_used"] = order_used
        state["kind"] = kind
        h = len(split.test_indices)
        exog_test = _exog_slice(exog_frame, split.test_indices)
        return _forecast_from_results(results, h, exog_test)

    wf = evaluate_walk_forward(
        period_index,
        y,
        predict_fn,
        train_end=te,
        test_start=ts,
        min_train_size=min_train_size,
        test_size=DEFAULT_TEST_SIZE,
        mode="fixed",
    )
    if wf.get("status") != "ok":
        raise InsufficientDataError("walk-forward evaluation returned insufficient_data")

    # Honest test predictions from the fixed split (re-fit train only)
    y_train = y[split0.train_indices]
    exog_train = _exog_slice(exog_frame, split0.train_indices)
    results_train, order_used, kind = _fit_arima(y_train, exog_train, order)
    state["order_used"] = order_used
    state["kind"] = kind
    n_test = len(split0.test_indices)
    predictions = _forecast_from_results(
        results_train, n_test, _exog_slice(exog_frame, split0.test_indices)
    )
    actuals = y[split0.test_indices]
    fold_metrics = compute_all_metrics(actuals, predictions)

    # Persist a model fitted on the full observed history for forward forecasts
    results_full, order_full, kind_full = _fit_arima(
        y, None if exog_frame is None else np.asarray(exog_frame, dtype=float), order_used
    )
    train_end_period = _period_str(period_index[split0.train_indices[-1]])
    artifact = _build_artifact(
        results=results_full,
        kind=kind_full,
        order=order_full,
        exog_cols=exog_cols,
        y=y,
        periods=period_index,
        exog=exog_frame,
        train_end_period=train_end_period,
    )

    path = Path(artifact_path) if artifact_path is not None else DEFAULT_ARTIFACT_PATH
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    saved = save_arima_artifact(artifact, path)

    return {
        "mae": float(wf.get("mae", fold_metrics["mae"])),
        "rmse": float(wf.get("rmse", fold_metrics["rmse"])),
        "mape": float(wf.get("mape", fold_metrics["mape"])),
        "status": "ok",
        "artifact_path": str(saved),
        "order": order_full,
        "n_train": int(len(split0.train_indices)),
        "n_test": int(n_test),
        "predictions": predictions,
        "actuals": actuals,
        "test_periods": [_period_str(period_index[i]) for i in split0.test_indices],
    }
