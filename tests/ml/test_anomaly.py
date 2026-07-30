"""Task #57 — Isolation Forest anomaly detector (honesty + determinism)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.anomaly.detector import (
    DEFAULT_CONTAMINATION,
    DECISION_THRESHOLD,
    MIN_POINTS,
    detect_series_anomalies,
)


def test_detect_empty_series_no_fake_anomaly():
    result = detect_series_anomalies(pd.Series(dtype=float))
    assert result["available"] is False
    assert result["points"] == []
    assert result["n_anomalies"] == 0
    assert result["threshold"] is None
    assert any("empty" in w or "missing" in w for w in result["warnings"])


def test_detect_none_series_no_fake_anomaly():
    result = detect_series_anomalies(None)
    assert result["available"] is False
    assert result["points"] == []
    assert result["n_anomalies"] == 0
    assert "missing_series" in result["warnings"]


def test_detect_short_series_no_fake_anomaly():
    periods = pd.date_range("2024-01-01", periods=5, freq="MS")
    series = pd.Series(np.linspace(100.0, 105.0, 5), index=periods)
    result = detect_series_anomalies(series)
    assert result["available"] is False
    assert result["points"] == []
    assert result["n_anomalies"] == 0
    assert any("insufficient" in w for w in result["warnings"])


def test_detect_fixture_series_deterministic(synthetic_iip_series):
    # Inject a clear spike so IsolationForest has something to flag (still
    # deterministic via random_state — we assert score equality, not count).
    series = synthetic_iip_series.copy()
    series.iloc[40] = float(series.iloc[40]) + 80.0

    a = detect_series_anomalies(series, contamination=0.05, random_state=42)
    b = detect_series_anomalies(series, contamination=0.05, random_state=42)

    assert a["available"] is True
    assert a["method"] == "isolation_forest"
    assert a["threshold"] == DECISION_THRESHOLD
    assert a["contamination"] == DEFAULT_CONTAMINATION
    assert a["n_scored"] >= MIN_POINTS
    assert a["n_input"] == len(series)
    assert len(a["points"]) == a["n_scored"]
    assert a["n_anomalies"] == sum(1 for p in a["points"] if p["is_anomaly"])
    assert a["warnings"] == []

    assert a["n_anomalies"] == b["n_anomalies"]
    assert [p["period"] for p in a["points"]] == [p["period"] for p in b["points"]]
    assert [p["is_anomaly"] for p in a["points"]] == [
        p["is_anomaly"] for p in b["points"]
    ]
    scores_a = np.asarray([p["score"] for p in a["points"]], dtype=float)
    scores_b = np.asarray([p["score"] for p in b["points"]], dtype=float)
    np.testing.assert_allclose(scores_a, scores_b, rtol=0, atol=1e-12)

    for point in a["points"]:
        assert "period" in point and "value" in point
        assert "score" in point and "is_anomaly" in point
        assert isinstance(point["is_anomaly"], bool)


def test_anomaly_points_use_decision_threshold(synthetic_iip_series):
    series = synthetic_iip_series.copy()
    series.iloc[30] = float(series.iloc[30]) + 100.0
    result = detect_series_anomalies(series)
    assert result["available"] is True
    # Sklearn IsolationForest: decision_function < 0 ↔ predict == -1.
    for point in result["points"]:
        if point["is_anomaly"]:
            assert point["score"] < DECISION_THRESHOLD
        else:
            assert point["score"] >= DECISION_THRESHOLD
