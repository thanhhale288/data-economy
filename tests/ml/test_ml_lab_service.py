"""Task #16 — ML Lab feature-importance reader (artifact #12, no invented scores)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.services import ml_lab_service as svc


def test_feature_importance_missing_is_explicit(tmp_path: Path):
    result = svc.get_feature_importance("xgboost", artifact_dir=tmp_path)

    assert result["available"] is False
    assert result["features"] == []
    assert result["gain"] == {}
    assert result["message"]
    assert "không bịa" in result["message"].lower()


def test_feature_importance_arima_unsupported(tmp_path: Path):
    result = svc.get_feature_importance("arima", artifact_dir=tmp_path)

    assert result["available"] is False
    assert result["features"] == []
    assert "arima" in result["message"].lower()
    assert "không bịa" in result["message"].lower()


def test_feature_importance_lstm_unsupported(tmp_path: Path):
    result = svc.get_feature_importance("lstm", artifact_dir=tmp_path)

    assert result["available"] is False
    assert "lstm" in result["message"].lower()


def test_feature_importance_reads_real_json(tmp_path: Path):
    path = tmp_path / "xgboost_importance.json"
    path.write_text(
        json.dumps(
            {
                "gain": {"iip_lag1": 12.5, "indigo": 3.0, "digital_va": 1.2},
                "weight": {"iip_lag1": 4, "indigo": 2, "digital_va": 1},
                "feature_cols": ["iip_lag1", "indigo", "digital_va"],
            }
        ),
        encoding="utf-8",
    )

    result = svc.get_feature_importance("xgboost", artifact_dir=tmp_path)

    assert result["available"] is True
    assert result["message"] is None
    assert result["source"] == str(path)
    assert result["gain"]["iip_lag1"] == 12.5
    # Ranked by gain desc
    assert result["features"][0]["feature"] == "iip_lag1"
    assert result["features"][0]["gain"] == 12.5
    assert result["features"][0]["weight"] == 4
    # Must not invent extra features
    assert {f["feature"] for f in result["features"]} == {"iip_lag1", "indigo", "digital_va"}


def test_feature_importance_empty_gain_is_unavailable(tmp_path: Path):
    (tmp_path / "xgboost_importance.json").write_text(
        json.dumps({"gain": {}, "weight": {}, "feature_cols": []}),
        encoding="utf-8",
    )
    result = svc.get_feature_importance("xgboost", artifact_dir=tmp_path)
    assert result["available"] is False
    assert "không bịa" in result["message"].lower()


def test_feature_importance_joblib_fallback(tmp_path: Path):
    joblib = pytest.importorskip("joblib")
    artifact = {
        "kind": "xgboost",
        "feature_cols": ["a", "b"],
        "importance": {"gain": {"a": 2.0, "b": 1.0}, "weight": {"a": 1, "b": 1}},
    }
    joblib.dump(artifact, tmp_path / "xgboost_model.joblib")

    result = svc.get_feature_importance("xgboost", artifact_dir=tmp_path)

    assert result["available"] is True
    assert result["gain"]["a"] == 2.0
    assert result["features"][0]["feature"] == "a"
