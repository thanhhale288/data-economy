"""Unit tests for lag helpers and feature-frame validation."""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.features.macro_helpers import add_lag_features, add_rolling_features
from pipeline.features.validation import FeatureValidationError, validate_feature_frame


def _macro_frame():
    df = pd.DataFrame(
        {
            "period": pd.date_range("2024-01-01", periods=5, freq="MS"),
            "iip": [100.0, 110.0, 105.0, 120.0, 115.0],
            "indigo": [90.0, 91.0, 92.0, 93.0, 94.0],
        }
    )
    df = add_lag_features(df, "iip", [1, 2, 3])
    df = add_rolling_features(df, "iip", [3, 6])
    df = add_lag_features(df, "indigo", [1, 2, 3])
    df = add_rolling_features(df, "indigo", [3, 6])
    return df


def test_lag_equals_shift_no_future_leak():
    df = _macro_frame()
    assert df["iip_lag1"].tolist()[1:] == df["iip"].tolist()[:-1]
    assert pd.isna(df.loc[0, "iip_lag1"])
    report = validate_feature_frame(df)
    assert report["valid"] is True


def test_validator_detects_future_leak():
    df = _macro_frame()
    df["iip_lag1"] = df["iip"].shift(-1)  # intentional leak
    with pytest.raises(FeatureValidationError, match="Future-leak"):
        validate_feature_frame(df)


def test_validator_rejects_mei_bci():
    df = _macro_frame()
    df["mei_bci"] = 100.0
    with pytest.raises(FeatureValidationError, match="mei_bci"):
        validate_feature_frame(df)


def test_validator_soft_note_missing_digital():
    df = _macro_frame()
    report = validate_feature_frame(df, require_digital=False)
    assert any("digital" in note for note in report["notes"])


def test_rolling_min_periods_uses_available_history_only():
    df = pd.DataFrame({"iip": [10.0, 20.0, 30.0]})
    out = add_rolling_features(df, "iip", [3])
    assert out["iip_roll3m"].tolist() == [10.0, 15.0, 20.0]
