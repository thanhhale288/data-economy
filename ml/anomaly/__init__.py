"""Anomaly detection for macro series (IIP / VA) — Isolation Forest v1."""

from ml.anomaly.detector import (
    DEFAULT_CONTAMINATION,
    DEFAULT_RANDOM_STATE,
    MIN_POINTS,
    detect_series_anomalies,
)

__all__ = [
    "DEFAULT_CONTAMINATION",
    "DEFAULT_RANDOM_STATE",
    "MIN_POINTS",
    "detect_series_anomalies",
]
