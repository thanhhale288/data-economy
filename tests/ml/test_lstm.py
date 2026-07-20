"""LSTM multi-step IIP model tests (fast: small epochs)."""

from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from ml.models.lstm_model import forecast_lstm, train_lstm_model  # noqa: E402


def test_train_lstm_small_epochs_and_forecast(synthetic_iip_series, tmp_path):
    result = train_lstm_model(
        synthetic_iip_series,
        periods=synthetic_iip_series.index,
        epochs=5,
        horizon=6,
        seq_len=12,
        artifact_dir=tmp_path,
        seed=42,
    )

    assert result["status"] == "ok"
    for key in ("mae", "rmse", "mape"):
        assert result[key] is not None
        assert np.isfinite(result[key]), f"{key}={result[key]}"

    assert (tmp_path / "lstm_model.pt").exists()
    assert (tmp_path / "lstm_meta.joblib").exists()

    horizon = 6
    preds = forecast_lstm(
        tmp_path,
        history=synthetic_iip_series.values,
        steps=horizon,
    )
    assert preds.shape == (horizon,)
    assert np.isfinite(preds).all()


def test_forecast_lstm_rejects_steps_beyond_horizon(synthetic_iip_series, tmp_path):
    train_lstm_model(
        synthetic_iip_series,
        periods=synthetic_iip_series.index,
        epochs=5,
        horizon=6,
        seq_len=12,
        artifact_dir=tmp_path,
        seed=0,
    )
    with pytest.raises(ValueError, match="exceeds trained horizon"):
        forecast_lstm(tmp_path, history=synthetic_iip_series.values, steps=12)
