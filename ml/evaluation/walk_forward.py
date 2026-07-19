"""Chronological train/test splits and walk-forward evaluation.

Public API for model trainers (Subagents B/C/D):

- ``TimeSplit`` — one fold with positional (iloc) train/test indices
- ``parse_period_bound`` — normalize ``'2023-12'`` / Timestamp to month-start
- ``iter_time_splits`` — yield folds; never shuffles; empty if too short
- ``evaluate_walk_forward`` — run ``predict_fn`` per fold, mean MAE/RMSE/MAPE
- ``assert_no_leakage`` — raise if train overlaps or follows test

Guarantees per fold: ``max(train_indices) < min(test_indices)`` (no future leakage).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd

from ml.evaluation.metrics import compute_all_metrics


@dataclass(frozen=True)
class TimeSplit:
    """One chronological train/test fold. Indices are positional (iloc) into the original series/frame."""

    fold: int
    train_indices: np.ndarray  # int positions, strictly increasing, all < min(test_indices)
    test_indices: np.ndarray  # int positions
    train_end: pd.Timestamp | None  # last train period if periods provided
    test_start: pd.Timestamp | None  # first test period if periods provided


def parse_period_bound(value: str | pd.Timestamp | None) -> pd.Timestamp | None:
    """Parse '2023-12' / '2023-12-01' / Timestamp to month-start Timestamp."""
    if value is None:
        return None
    ts = pd.Timestamp(value)
    if pd.isna(ts):
        raise ValueError(f"Invalid period bound: {value!r}")
    return ts.to_period("M").to_timestamp()


def assert_no_leakage(split: TimeSplit) -> None:
    """Raise ``AssertionError`` if train indices leak into or past the test window."""
    if split.train_indices.size == 0 or split.test_indices.size == 0:
        raise AssertionError("train and test indices must be non-empty")
    if not np.all(np.diff(split.train_indices) > 0):
        raise AssertionError("train_indices must be strictly increasing")
    if not np.all(np.diff(split.test_indices) > 0):
        raise AssertionError("test_indices must be strictly increasing")
    if int(split.train_indices.max()) >= int(split.test_indices.min()):
        raise AssertionError(
            f"leakage: max(train)={split.train_indices.max()} "
            f">= min(test)={split.test_indices.min()}"
        )


def _normalize_periods(
    periods: Sequence | pd.Series | pd.DatetimeIndex | np.ndarray,
) -> pd.DatetimeIndex:
    if isinstance(periods, pd.DatetimeIndex):
        idx = periods
    elif isinstance(periods, pd.Series):
        idx = pd.DatetimeIndex(pd.to_datetime(periods))
    else:
        idx = pd.DatetimeIndex(pd.to_datetime(list(periods)))
    if idx.isna().any():
        raise ValueError("periods contain invalid / unparseable values")
    return idx.to_period("M").to_timestamp()


def _period_bounds(
    periods: pd.DatetimeIndex,
    train_indices: np.ndarray,
    test_indices: np.ndarray,
) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    train_end = periods[int(train_indices[-1])] if train_indices.size else None
    test_start = periods[int(test_indices[0])] if test_indices.size else None
    return train_end, test_start


def _make_split(
    fold: int,
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    periods: pd.DatetimeIndex,
) -> TimeSplit:
    train_indices = np.asarray(train_indices, dtype=int)
    test_indices = np.asarray(test_indices, dtype=int)
    train_end, test_start = _period_bounds(periods, train_indices, test_indices)
    split = TimeSplit(
        fold=fold,
        train_indices=train_indices,
        test_indices=test_indices,
        train_end=train_end,
        test_start=test_start,
    )
    assert_no_leakage(split)
    return split


def _resolve_fixed_cut(
    periods: pd.DatetimeIndex,
    *,
    train_end: pd.Timestamp | None,
    test_start: pd.Timestamp | None,
    test_size: int | None,
) -> tuple[np.ndarray, np.ndarray] | None:
    n = len(periods)
    if n == 0:
        return None

    if test_start is not None:
        test_indices = np.flatnonzero(periods >= test_start)
    elif train_end is not None:
        test_indices = np.flatnonzero(periods > train_end)
    elif test_size is not None:
        if test_size <= 0 or test_size >= n:
            return None
        test_indices = np.arange(n - test_size, n, dtype=int)
    else:
        return None

    if test_indices.size == 0:
        return None

    test_min = int(test_indices.min())
    if train_end is not None:
        train_indices = np.flatnonzero(periods <= train_end)
        train_indices = train_indices[train_indices < test_min]
    else:
        train_indices = np.arange(0, test_min, dtype=int)

    if train_indices.size == 0:
        return None
    return train_indices, test_indices


def _first_test_origin(
    periods: pd.DatetimeIndex,
    *,
    train_end: pd.Timestamp | None,
    test_start: pd.Timestamp | None,
    min_train_size: int,
) -> int | None:
    """Index where the first walk-forward test window should start."""
    n = len(periods)
    if test_start is not None:
        candidates = np.flatnonzero(periods >= test_start)
        if candidates.size == 0:
            return None
        origin = int(candidates[0])
    elif train_end is not None:
        train_idx = np.flatnonzero(periods <= train_end)
        if train_idx.size == 0:
            return None
        origin = int(train_idx[-1]) + 1
    else:
        origin = min_train_size

    if origin < min_train_size or origin >= n:
        return None
    return origin


def iter_time_splits(
    periods: Sequence | pd.Series | pd.DatetimeIndex | np.ndarray,
    *,
    train_end: str | pd.Timestamp | None = None,
    test_start: str | pd.Timestamp | None = None,
    min_train_size: int = 24,
    test_size: int | None = 6,
    step_size: int = 1,
    mode: Literal["expanding", "rolling", "fixed"] = "fixed",
    rolling_train_size: int | None = None,
) -> Iterator[TimeSplit]:
    """
    Chronological splits only — NEVER shuffle.

    modes:
    - fixed: single split. If train_end and/or test_start given, use them.
      Else if test_size given, train = all but last test_size rows.
    - expanding: walk-forward; each fold grows train; test windows of test_size stepping by step_size.
      Optional train_end/test_start constrain the first fold / test region.
    - rolling: like expanding but train window capped at rolling_train_size.

    Guarantees:
    - max(train_indices) < min(test_indices) for every fold
    - no future leakage into train
    - empty iterator if data too short (don't raise unless periods invalid)
    """
    if min_train_size < 1:
        return
    if step_size < 1:
        return

    periods_idx = _normalize_periods(periods)
    n = len(periods_idx)
    train_end_ts = parse_period_bound(train_end)
    test_start_ts = parse_period_bound(test_start)

    if mode == "fixed":
        cut = _resolve_fixed_cut(
            periods_idx,
            train_end=train_end_ts,
            test_start=test_start_ts,
            test_size=test_size,
        )
        if cut is None:
            return
        train_indices, test_indices = cut
        if train_indices.size < min_train_size:
            return
        yield _make_split(0, train_indices, test_indices, periods_idx)
        return

    if test_size is None or test_size < 1:
        return

    roll_cap: int | None = None
    if mode == "rolling":
        if rolling_train_size is None or rolling_train_size < 1:
            return
        if rolling_train_size < min_train_size:
            return
        roll_cap = rolling_train_size

    origin = _first_test_origin(
        periods_idx,
        train_end=train_end_ts,
        test_start=test_start_ts,
        min_train_size=min_train_size,
    )
    if origin is None:
        return

    fold = 0
    test_start_idx = origin
    while test_start_idx + test_size <= n:
        train_end_excl = test_start_idx
        if roll_cap is None:
            train_start = 0
        else:
            train_start = max(0, train_end_excl - roll_cap)

        train_len = train_end_excl - train_start
        if train_len >= min_train_size:
            train_indices = np.arange(train_start, train_end_excl, dtype=int)
            test_indices = np.arange(test_start_idx, test_start_idx + test_size, dtype=int)
            yield _make_split(fold, train_indices, test_indices, periods_idx)
            fold += 1

        test_start_idx += step_size


def evaluate_walk_forward(
    periods: Sequence | pd.Series | pd.DatetimeIndex | np.ndarray,
    y: np.ndarray | pd.Series,
    predict_fn: Callable[[TimeSplit], np.ndarray],
    *,
    train_end: str | pd.Timestamp | None = "2023-12",
    test_start: str | pd.Timestamp | None = "2024-01",
    min_train_size: int = 24,
    test_size: int | None = 6,
    step_size: int = 1,
    mode: Literal["expanding", "rolling", "fixed"] = "fixed",
    rolling_train_size: int | None = None,
) -> dict[str, Any]:
    """
    For each split, call predict_fn(split) which must return predictions aligned
    to split.test_indices (same length). Aggregate mean MAE/RMSE/MAPE via
    ml.evaluation.metrics.compute_all_metrics.

    Return dict:
    {
      "mae": float, "rmse": float, "mape": float,  # means across folds
      "n_folds": int,
      "folds": [{"fold": int, "mae": ..., "rmse": ..., "mape": ..., "n_test": int}, ...],
      "status": "ok" | "insufficient_data",
    }
    If no folds: status=insufficient_data, metrics as None or omit numeric means — use None for mae/rmse/mape.
    """
    y_arr = np.asarray(y, dtype=float)
    folds_out: list[dict[str, Any]] = []
    mae_vals: list[float] = []
    rmse_vals: list[float] = []
    mape_vals: list[float] = []

    for split in iter_time_splits(
        periods,
        train_end=train_end,
        test_start=test_start,
        min_train_size=min_train_size,
        test_size=test_size,
        step_size=step_size,
        mode=mode,
        rolling_train_size=rolling_train_size,
    ):
        y_true = y_arr[split.test_indices]
        y_pred = np.asarray(predict_fn(split), dtype=float)
        if y_pred.shape[0] != split.test_indices.shape[0]:
            raise ValueError(
                f"predict_fn fold {split.fold}: expected {split.test_indices.shape[0]} "
                f"predictions, got {y_pred.shape[0]}"
            )
        metrics = compute_all_metrics(y_true, y_pred)
        folds_out.append(
            {
                "fold": split.fold,
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "mape": metrics["mape"],
                "n_test": int(split.test_indices.shape[0]),
            }
        )
        mae_vals.append(metrics["mae"])
        rmse_vals.append(metrics["rmse"])
        mape_vals.append(metrics["mape"])

    if not folds_out:
        return {
            "mae": None,
            "rmse": None,
            "mape": None,
            "n_folds": 0,
            "folds": [],
            "status": "insufficient_data",
        }

    return {
        "mae": float(np.mean(mae_vals)),
        "rmse": float(np.mean(rmse_vals)),
        "mape": float(np.mean(mape_vals)),
        "n_folds": len(folds_out),
        "folds": folds_out,
        "status": "ok",
    }
