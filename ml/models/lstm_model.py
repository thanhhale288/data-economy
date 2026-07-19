"""LSTM multi-step IIP forecasting (univariate by default).

Architecture
------------
- Input tensor: ``(batch, seq_len, n_features)`` — default ``n_features=1`` (IIP only).
- ``nn.LSTM(n_features, hidden_size, num_layers, batch_first=True)``
- Take the **last** timestep hidden state → ``nn.Linear(hidden_size, horizon)``.
- Direct multi-step output of length ``horizon`` (not recursive one-step rollouts).

Scaling
-------
IIP is z-scored with **train-only** mean/std (stored in ``lstm_meta.joblib``).
Predictions are inverse-transformed before metrics / ``forecast_lstm``.

Sequences
---------
For start index ``t``::

    X = y[t : t + seq_len]
    Y = y[t + seq_len : t + seq_len + horizon]

Training samples use train indices only (no shuffle). Time split via
``ml.evaluation.walk_forward`` (default ``train_end=2023-12``, ``test_start=2024-01``).

Metric aggregation
------------------
``metric_aggregation = "mean_over_horizon"``: MAE / RMSE / MAPE from
``compute_all_metrics`` on **flattened** horizon steps (all windows' steps
concatenated). Equivalent to averaging per-step errors across the horizon.

Artifacts under ``data/models/``
--------------------------------
- ``lstm_model.pt`` — ``state_dict`` only
- ``lstm_meta.joblib`` — primary metadata (seq_len, horizon, scaler, …)
- ``lstm_seq_len.joblib`` — seq_len int (backward compat)

Forecast
--------
``forecast_lstm`` runs a real forward pass. ``steps`` defaults to trained
``horizon``. Requires ``1 <= steps <= horizon`` (no recursive extension).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from ml.evaluation.metrics import compute_all_metrics
from ml.evaluation.walk_forward import TimeSplit, evaluate_walk_forward, iter_time_splits

MODELS_DIR = Path(__file__).resolve().parents[2] / "data" / "models"

DEFAULT_SEQ_LEN = 12
DEFAULT_HORIZON = 6
DEFAULT_HIDDEN = 32
DEFAULT_NUM_LAYERS = 1
DEFAULT_EPOCHS = 40
FEATURE_COLS = ["iip"]


class InsufficientDataError(ValueError):
    """Raised when the series is too short to build train sequences or a time split."""


class MultiStepLSTM(nn.Module):
    """LSTM → last hidden → Linear(hidden, horizon)."""

    def __init__(
        self,
        *,
        n_features: int = 1,
        hidden_size: int = DEFAULT_HIDDEN,
        num_layers: int = DEFAULT_NUM_LAYERS,
        horizon: int = DEFAULT_HORIZON,
    ) -> None:
        super().__init__()
        self.n_features = n_features
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.horizon = horizon
        self.lstm = nn.LSTM(
            n_features,
            hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden_size, horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, n_features)
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


def _resolve_dir(artifact_dir: Path | str | None) -> Path:
    path = Path(artifact_dir) if artifact_dir is not None else MODELS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _as_1d_float(series: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(series, dtype=float).reshape(-1)
    if arr.size == 0:
        raise InsufficientDataError("empty IIP series")
    if not np.isfinite(arr).all():
        raise InsufficientDataError("IIP series contains non-finite values")
    return arr


def _resolve_periods(
    series: pd.Series | np.ndarray,
    periods: Sequence | pd.DatetimeIndex | None,
) -> pd.DatetimeIndex:
    if periods is not None:
        idx = pd.DatetimeIndex(pd.to_datetime(list(periods)))
    elif isinstance(series, pd.Series) and len(series) > 0:
        try:
            idx = pd.DatetimeIndex(pd.to_datetime(series.index))
        except (TypeError, ValueError, pd.errors.OutOfBoundsDatetime):
            idx = pd.DatetimeIndex([])
        if idx.size == len(series) and not idx.isna().any():
            return idx.to_period("M").to_timestamp()
        idx = pd.date_range("2000-01-01", periods=len(series), freq="MS")
    else:
        n = len(np.asarray(series).reshape(-1))
        idx = pd.date_range("2000-01-01", periods=n, freq="MS")
    if idx.isna().any():
        raise ValueError("periods contain invalid / unparseable values")
    if len(idx) != len(np.asarray(series).reshape(-1)):
        raise ValueError("periods length must match series length")
    return idx.to_period("M").to_timestamp()


def _fit_scaler(train_y: np.ndarray) -> tuple[float, float]:
    mean = float(np.mean(train_y))
    std = float(np.std(train_y))
    if std < 1e-8:
        std = 1.0
    return mean, std


def _scale(y: np.ndarray, mean: float, std: float) -> np.ndarray:
    return (y - mean) / std


def _inverse_scale(y: np.ndarray, mean: float, std: float) -> np.ndarray:
    return y * std + mean


def create_sequences(
    y_scaled: np.ndarray,
    *,
    seq_len: int,
    horizon: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Build ``X (n, seq_len, 1)`` and ``Y (n, horizon)`` from a 1-d scaled series."""
    n = len(y_scaled)
    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    last = n - seq_len - horizon
    for t in range(0, last + 1):
        xs.append(y_scaled[t : t + seq_len])
        ys.append(y_scaled[t + seq_len : t + seq_len + horizon])
    if not xs:
        return (
            np.empty((0, seq_len, 1), dtype=np.float32),
            np.empty((0, horizon), dtype=np.float32),
        )
    X = np.stack(xs, axis=0).astype(np.float32)[..., np.newaxis]
    Y = np.stack(ys, axis=0).astype(np.float32)
    return X, Y


def _train_torch(
    model: MultiStepLSTM,
    X: np.ndarray,
    Y: np.ndarray,
    *,
    epochs: int,
    seed: int,
    lr: float = 0.01,
) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cpu")
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    xt = torch.from_numpy(X).to(device)
    yt = torch.from_numpy(Y).to(device)
    model.train()
    for _ in range(epochs):
        opt.zero_grad()
        pred = model(xt)
        loss = criterion(pred, yt)
        loss.backward()
        opt.step()


@torch.no_grad()
def _forward_np(model: MultiStepLSTM, x_seq: np.ndarray) -> np.ndarray:
    """x_seq: (seq_len,) or (seq_len, n_features) scaled → (horizon,) scaled."""
    model.eval()
    arr = np.asarray(x_seq, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr[:, np.newaxis]
    xt = torch.from_numpy(arr).unsqueeze(0)  # (1, seq_len, n_features)
    out = model(xt).cpu().numpy().reshape(-1)
    return out.astype(float)


def _min_train_for_sequences(seq_len: int, horizon: int, min_train_size: int) -> int:
    return max(min_train_size, seq_len + horizon)


def _eval_windows_mean_over_horizon(
    model: MultiStepLSTM,
    y: np.ndarray,
    y_scaled: np.ndarray,
    test_indices: np.ndarray,
    *,
    seq_len: int,
    horizon: int,
    mean: float,
    std: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Collect all windows whose full horizon target lies in the test set."""
    test_set = set(int(i) for i in test_indices)
    preds: list[float] = []
    actuals: list[float] = []
    n = len(y)
    for t in range(0, n - seq_len - horizon + 1):
        target_idx = range(t + seq_len, t + seq_len + horizon)
        if not all(i in test_set for i in target_idx):
            continue
        scaled_pred = _forward_np(model, y_scaled[t : t + seq_len])
        pred = _inverse_scale(scaled_pred, mean, std)
        actual = y[t + seq_len : t + seq_len + horizon]
        preds.extend(pred.tolist())
        actuals.extend(actual.tolist())
    return np.asarray(preds, dtype=float), np.asarray(actuals, dtype=float)


def _block_predict_for_test(
    model: MultiStepLSTM,
    y: np.ndarray,
    y_scaled: np.ndarray,
    test_indices: np.ndarray,
    *,
    seq_len: int,
    horizon: int,
    mean: float,
    std: float,
) -> np.ndarray:
    """Fill predictions aligned to ``test_indices`` with non-overlapping horizon blocks."""
    n_test = int(test_indices.shape[0])
    out = np.empty(n_test, dtype=float)
    i = 0
    while i < n_test:
        abs_start = int(test_indices[i])
        if abs_start < seq_len:
            raise InsufficientDataError(
                f"need seq_len={seq_len} history before test index {abs_start}"
            )
        scaled_pred = _forward_np(model, y_scaled[abs_start - seq_len : abs_start])
        pred = _inverse_scale(scaled_pred, mean, std)
        n = min(horizon, n_test - i)
        out[i : i + n] = pred[:n]
        i += n
    return out


def train_lstm_model(
    series: pd.Series | np.ndarray,
    *,
    periods: Sequence | pd.DatetimeIndex | None = None,
    seq_len: int = DEFAULT_SEQ_LEN,
    horizon: int = DEFAULT_HORIZON,
    train_end: str | None = "2023-12",
    test_start: str | None = "2024-01",
    min_train_size: int = 24,
    epochs: int = DEFAULT_EPOCHS,
    hidden_size: int = DEFAULT_HIDDEN,
    num_layers: int = DEFAULT_NUM_LAYERS,
    artifact_dir: Path | str | None = None,
    seed: int = 42,
) -> dict[str, Any]:
    """
    Train a multi-step LSTM on IIP and evaluate with a chronological split.

    Returns a metrics dict with ``mae`` / ``rmse`` / ``mape``
    (``mean_over_horizon``), ``status``, artifact paths, and test
    ``predictions`` / ``actuals``.

    Prediction shapes
    -----------------
    - ``predictions`` / ``actuals``: 1-d arrays of length
      ``n_windows * horizon`` (flattened multi-step windows), or a single
      ``(horizon,)`` window when only one eval window exists.
    - Walk-forward fold preds (via ``evaluate_walk_forward``) are aligned
      1:1 with each fold's ``test_indices``.
    """
    if seq_len < 1 or horizon < 1:
        raise ValueError("seq_len and horizon must be >= 1")
    if epochs < 1:
        raise ValueError("epochs must be >= 1")

    y = _as_1d_float(series)
    periods_idx = _resolve_periods(series, periods)
    need = _min_train_for_sequences(seq_len, horizon, min_train_size)

    splits = list(
        iter_time_splits(
            periods_idx,
            train_end=train_end,
            test_start=test_start,
            min_train_size=need,
            test_size=horizon,
            mode="fixed",
        )
    )
    if not splits:
        raise InsufficientDataError(
            f"no chronological split with min_train_size={need} "
            f"(seq_len={seq_len}, horizon={horizon})"
        )
    split: TimeSplit = splits[0]
    train_idx = split.train_indices
    test_idx = split.test_indices

    if train_idx.size < need:
        raise InsufficientDataError(
            f"train length {train_idx.size} < required {need} "
            f"(seq_len + horizon and min_train_size)"
        )

    y_train = y[train_idx]
    mean, std = _fit_scaler(y_train)
    y_scaled = _scale(y, mean, std)
    # Sequences from the contiguous train prefix (indices 0..train_end)
    train_end_pos = int(train_idx[-1]) + 1
    X_tr, Y_tr = create_sequences(
        y_scaled[:train_end_pos],
        seq_len=seq_len,
        horizon=horizon,
    )
    if X_tr.shape[0] < 1:
        raise InsufficientDataError(
            f"cannot build LSTM sequences: need >= {seq_len + horizon} train points, "
            f"got {train_end_pos}"
        )

    torch.manual_seed(seed)
    np.random.seed(seed)
    model = MultiStepLSTM(
        n_features=1,
        hidden_size=hidden_size,
        num_layers=num_layers,
        horizon=horizon,
    )
    _train_torch(model, X_tr, Y_tr, epochs=epochs, seed=seed)

    pred_flat, actual_flat = _eval_windows_mean_over_horizon(
        model,
        y,
        y_scaled,
        test_idx,
        seq_len=seq_len,
        horizon=horizon,
        mean=mean,
        std=std,
    )
    if pred_flat.size == 0:
        # Fallback: single direct forecast from end of train into first horizon test points
        if train_end_pos < seq_len:
            raise InsufficientDataError("not enough history for forecast window")
        n_out = min(horizon, int(test_idx.shape[0]))
        scaled_pred = _forward_np(
            model, y_scaled[train_end_pos - seq_len : train_end_pos]
        )
        pred_flat = _inverse_scale(scaled_pred[:n_out], mean, std)
        actual_flat = y[test_idx[:n_out]]

    metrics = compute_all_metrics(actual_flat, pred_flat)

    # Walk-forward helper: same fitted weights; block-fill aligned to test_indices
    def predict_fn(s: TimeSplit) -> np.ndarray:
        return _block_predict_for_test(
            model,
            y,
            y_scaled,
            s.test_indices,
            seq_len=seq_len,
            horizon=horizon,
            mean=mean,
            std=std,
        )

    wf = evaluate_walk_forward(
        periods_idx,
        y,
        predict_fn,
        train_end=train_end,
        test_start=test_start,
        min_train_size=need,
        test_size=horizon,
        mode="fixed",
    )

    out_dir = _resolve_dir(artifact_dir)
    model_path = out_dir / "lstm_model.pt"
    meta_path = out_dir / "lstm_meta.joblib"
    seq_path = out_dir / "lstm_seq_len.joblib"

    train_end_str = (
        split.train_end.strftime("%Y-%m") if split.train_end is not None else train_end
    )
    meta: dict[str, Any] = {
        "kind": "lstm",
        "seq_len": int(seq_len),
        "horizon": int(horizon),
        "hidden_size": int(hidden_size),
        "num_layers": int(num_layers),
        "n_features": 1,
        "feature_cols": list(FEATURE_COLS),
        "scaler": {"mean": mean, "std": std},
        "train_end": train_end_str,
        "epochs": int(epochs),
        "metric_aggregation": "mean_over_horizon",
    }

    torch.save(model.state_dict(), model_path)
    joblib.dump(meta, meta_path)
    joblib.dump(int(seq_len), seq_path)

    return {
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "mape": metrics["mape"],
        "status": "ok",
        "metric_aggregation": "mean_over_horizon",
        "seq_len": int(seq_len),
        "horizon": int(horizon),
        "n_train": int(train_idx.size),
        "n_test": int(test_idx.size),
        "n_train_sequences": int(X_tr.shape[0]),
        "artifact_dir": str(out_dir),
        "artifact_path": str(model_path),
        "meta_path": str(meta_path),
        "predictions": pred_flat,
        "actuals": actual_flat,
        "test_periods": [str(periods_idx[int(i)]) for i in test_idx],
        "walk_forward": wf,
        "train_end": train_end_str,
        "test_start": (
            split.test_start.strftime("%Y-%m")
            if split.test_start is not None
            else test_start
        ),
    }


def load_lstm_artifacts(
    artifact_dir: Path | str | None = None,
) -> tuple[nn.Module, dict[str, Any]]:
    """Load ``lstm_model.pt`` + ``lstm_meta.joblib``; return ``(model, meta)``."""
    out_dir = _resolve_dir(artifact_dir)
    meta_path = out_dir / "lstm_meta.joblib"
    model_path = out_dir / "lstm_model.pt"
    if not meta_path.exists():
        raise FileNotFoundError(f"missing LSTM meta: {meta_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"missing LSTM weights: {model_path}")

    meta = joblib.load(meta_path)
    model = MultiStepLSTM(
        n_features=int(meta.get("n_features", 1)),
        hidden_size=int(meta.get("hidden_size", DEFAULT_HIDDEN)),
        num_layers=int(meta.get("num_layers", DEFAULT_NUM_LAYERS)),
        horizon=int(meta.get("horizon", DEFAULT_HORIZON)),
    )
    state = torch.load(model_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return model, meta


def forecast_lstm(
    artifact_dir: Path | str | None = None,
    *,
    history: np.ndarray | pd.Series,
    steps: int | None = None,
) -> np.ndarray:
    """
    Load artifacts and run a forward pass.

    Returns shape ``(steps,)`` with ``steps`` defaulting to trained ``horizon``.
    Requires ``1 <= steps <= horizon`` (trained multi-step head only; no
    recursive extension beyond horizon).
    """
    model, meta = load_lstm_artifacts(artifact_dir)
    seq_len = int(meta["seq_len"])
    horizon = int(meta["horizon"])
    scaler = meta["scaler"]
    mean = float(scaler["mean"] if not isinstance(scaler["mean"], list) else scaler["mean"][0])
    std = float(scaler["std"] if not isinstance(scaler["std"], list) else scaler["std"][0])

    n_steps = horizon if steps is None else int(steps)
    if n_steps < 1:
        raise ValueError("steps must be >= 1")
    if n_steps > horizon:
        raise ValueError(
            f"steps={n_steps} exceeds trained horizon={horizon}; "
            "require steps <= horizon (no recursive extension)"
        )

    hist = _as_1d_float(history)
    if hist.size < seq_len:
        raise InsufficientDataError(
            f"history length {hist.size} < seq_len={seq_len} required for forecast"
        )

    tail = hist[-seq_len:]
    scaled = _scale(tail, mean, std)
    pred_scaled = _forward_np(model, scaled)
    pred = _inverse_scale(pred_scaled, mean, std)
    return pred[:n_steps].astype(float)
