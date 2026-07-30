"""LightGBM IIP model tests (Task #58)."""

from __future__ import annotations

import json

import numpy as np
import pytest

lightgbm = pytest.importorskip("lightgbm")

from ml.models import lightgbm_model as lgbm_mod  # noqa: E402
from ml.models.lightgbm_model import (  # noqa: E402
    forecast_lightgbm,
    train_lightgbm_model,
)
from ml.models.xgboost_model import select_feature_columns  # noqa: E402


def test_lightgbm_target_remains_iip_va_is_exog(synthetic_feature_frame, tmp_path):
    """Do not silently switch forecast target to VA."""
    df = synthetic_feature_frame.copy()
    df["va_c"] = 500.0
    df["va_c_alignment"] = "step_hold_at_ingest"
    cols = select_feature_columns(df, target_col="iip")
    assert "va_c" in cols
    assert "iip" not in cols

    result = train_lightgbm_model(
        df,
        artifact_dir=tmp_path,
        n_estimators=10,
        max_depth=2,
        learning_rate=0.1,
    )
    assert result["status"] == "ok"
    assert "va_c" in result["feature_cols"]
    assert "iip" not in result["feature_cols"]
    import joblib

    art = joblib.load(result["artifact_path"])
    assert art.get("target", "iip") == "iip"
    assert art.get("kind") == "lightgbm"


def test_train_lightgbm_importance_and_forecast(synthetic_feature_frame, tmp_path):
    result = train_lightgbm_model(
        synthetic_feature_frame,
        artifact_dir=tmp_path,
        n_estimators=20,
        max_depth=3,
        learning_rate=0.1,
    )

    assert result["status"] == "ok"
    assert result["mae"] is not None
    assert np.isfinite(result["mae"])
    assert np.isfinite(result["rmse"])
    assert np.isfinite(result["mape"])

    feature_cols = result["feature_cols"]
    gain = result["importance"]["gain"]
    assert set(gain.keys()) == set(feature_cols)

    importance_path = tmp_path / "lightgbm_importance.json"
    assert importance_path.exists()
    dumped = json.loads(importance_path.read_text(encoding="utf-8"))
    assert set(dumped["gain"].keys()) == set(feature_cols)

    preds = forecast_lightgbm(
        tmp_path / "lightgbm_model.joblib",
        history_df=synthetic_feature_frame,
        steps=4,
    )
    assert preds.shape == (4,)
    assert np.isfinite(preds).all()


def test_lightgbm_soft_fail_when_unavailable(synthetic_feature_frame, tmp_path, monkeypatch):
    monkeypatch.setattr(lgbm_mod, "LIGHTGBM_AVAILABLE", False)
    result = train_lightgbm_model(synthetic_feature_frame, artifact_dir=tmp_path)
    assert result["status"] == "unavailable"
    assert result["mae"] is None
    assert result["predictions"] == []
    assert "soft fail" in (result.get("message") or "").lower() or "missing" in (
        result.get("message") or ""
    ).lower()
