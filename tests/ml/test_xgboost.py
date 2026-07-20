"""XGBoost IIP model tests."""

from __future__ import annotations

import json

import numpy as np
import pytest

xgboost = pytest.importorskip("xgboost")

from ml.models.xgboost_model import (  # noqa: E402
    forecast_xgboost,
    select_feature_columns,
    train_xgboost_model,
)


def test_select_feature_columns_excludes_period_and_strings(synthetic_feature_frame):
    cols = select_feature_columns(synthetic_feature_frame, target_col="iip")
    assert "period" not in cols
    assert "iip" not in cols
    assert "digital_alignment" not in cols
    assert "financial_alignment" not in cols
    assert "iip_lag1" in cols
    assert "indigo" in cols


def test_train_xgboost_importance_and_forecast(synthetic_feature_frame, tmp_path):
    result = train_xgboost_model(
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
    importance = result["importance"]
    gain = importance["gain"]
    assert set(gain.keys()) == set(feature_cols)
    # Keys must be real column names, not opaque f0/f1 indices only
    assert all(isinstance(k, str) and not (k.startswith("f") and k[1:].isdigit()) for k in gain)

    importance_path = tmp_path / "xgboost_importance.json"
    assert importance_path.exists()
    dumped = json.loads(importance_path.read_text(encoding="utf-8"))
    assert set(dumped["gain"].keys()) == set(feature_cols)

    preds = forecast_xgboost(
        tmp_path / "xgboost_model.joblib",
        history_df=synthetic_feature_frame,
        steps=4,
    )
    assert preds.shape == (4,)
    assert np.isfinite(preds).all()
