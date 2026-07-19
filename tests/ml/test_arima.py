"""ARIMA/SARIMAX trainer tests (statsmodels; not EMA)."""

from __future__ import annotations

import numpy as np
import pytest

statsmodels = pytest.importorskip("statsmodels")

from ml.models.arima_model import (  # noqa: E402
    forecast_arima,
    load_arima_artifact,
    train_arima_model,
)


def test_train_arima_fits_and_forecasts(synthetic_iip_series, tmp_path):
    artifact_path = tmp_path / "arima_model.joblib"
    result = train_arima_model(
        synthetic_iip_series,
        periods=synthetic_iip_series.index,
        artifact_path=artifact_path,
    )

    assert result["status"] == "ok"
    assert artifact_path.exists()
    for key in ("mae", "rmse", "mape"):
        assert result[key] is not None
        assert np.isfinite(result[key])

    artifact = load_arima_artifact(artifact_path)
    assert artifact["kind"] in {"arima", "sarimax"}
    assert "order" in artifact
    assert isinstance(artifact["order"], tuple)
    assert len(artifact["order"]) == 3
    assert artifact["order"][0] >= 0
    # Real statsmodels fit — not an EMA placeholder
    assert "model_results" in artifact
    assert artifact.get("fitted_params") is not None

    horizon = 6
    preds = forecast_arima(artifact, steps=horizon)
    assert preds.shape == (horizon,)
    assert np.isfinite(preds).all()


def test_forecast_arima_from_path(synthetic_iip_series, tmp_path):
    artifact_path = tmp_path / "arima_model.joblib"
    train_arima_model(
        synthetic_iip_series,
        periods=synthetic_iip_series.index,
        artifact_path=artifact_path,
    )
    preds = forecast_arima(artifact_path, steps=3)
    assert preds.shape == (3,)
    assert np.isfinite(preds).all()
