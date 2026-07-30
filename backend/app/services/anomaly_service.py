"""Anomaly detection service for IIP (+ optional VA) from gso_macro.

Does not write to the database. Missing series → empty payload + warnings
(no invented anomaly alerts).
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models import GsoMacro
from ml.anomaly.detector import (
    DEFAULT_CONTAMINATION,
    DEFAULT_RANDOM_STATE,
    detect_series_anomalies,
)

_IIP_CODE = "IIP_C"
_VA_CODE = "VA_C"
_VA_CODES = frozenset({"VA_C", "VA_C_NOMINAL"})


def _load_macro_series(
    db: Session,
    indicator_code: str,
    vsic_code: str = "C",
) -> pd.Series:
    """Load GSO macro series as a period-indexed Series. Empty if absent."""
    rows = (
        db.query(GsoMacro)
        .filter(
            GsoMacro.indicator_code == indicator_code,
            GsoMacro.vsic_code == vsic_code,
        )
        .order_by(GsoMacro.period)
        .all()
    )
    if not rows:
        return pd.Series(dtype=float)
    periods = [r.period for r in rows]
    values = [float(r.value) for r in rows]
    return pd.Series(values, index=pd.DatetimeIndex(periods), name=indicator_code)


def _series_payload(
    *,
    indicator_code: str,
    result: dict[str, Any],
    extra_warnings: list[str] | None = None,
) -> dict[str, Any]:
    warnings = list(result.get("warnings") or [])
    if extra_warnings:
        warnings = list(extra_warnings) + warnings
    return {
        "indicator_code": indicator_code,
        "available": bool(result.get("available")),
        "method": result.get("method"),
        "contamination": result.get("contamination"),
        "threshold": result.get("threshold"),
        "n_input": result.get("n_input", 0),
        "n_scored": result.get("n_scored", 0),
        "n_anomalies": result.get("n_anomalies", 0),
        "points": list(result.get("points") or []),
        "warnings": warnings,
    }


def detect_iip_va_anomalies(
    db: Session,
    *,
    vsic_code: str = "C",
    include_va: bool = True,
    va_indicator: str = _VA_CODE,
    contamination: float = DEFAULT_CONTAMINATION,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> dict[str, Any]:
    """Run Isolation Forest on IIP_C and optionally VA from the DB.

    Returns scores/flags + baseline threshold. Never invents alerts when a
    series is missing or too short.
    """
    vsic = (vsic_code or "C").strip() or "C"
    top_warnings: list[str] = []

    iip_series = _load_macro_series(db, _IIP_CODE, vsic)
    iip_extra: list[str] = []
    if iip_series.empty:
        iip_extra.append(f"missing_series:{_IIP_CODE}")
        top_warnings.append(f"missing_series:{_IIP_CODE}")
    iip_result = detect_series_anomalies(
        iip_series if not iip_series.empty else None,
        contamination=contamination,
        random_state=random_state,
    )
    iip_payload = _series_payload(
        indicator_code=_IIP_CODE,
        result=iip_result,
        extra_warnings=iip_extra or None,
    )

    va_payload: dict[str, Any] | None = None
    if include_va:
        va_code = (va_indicator or _VA_CODE).strip().upper()
        if va_code not in _VA_CODES:
            va_payload = _series_payload(
                indicator_code=va_code,
                result={
                    "available": False,
                    "method": "isolation_forest",
                    "contamination": contamination,
                    "threshold": None,
                    "n_input": 0,
                    "n_scored": 0,
                    "n_anomalies": 0,
                    "points": [],
                    "warnings": [f"unsupported_va_indicator:{va_code}"],
                },
            )
            top_warnings.append(f"unsupported_va_indicator:{va_code}")
        else:
            va_series = _load_macro_series(db, va_code, vsic)
            va_extra: list[str] = []
            if va_series.empty:
                va_extra.append(f"missing_series:{va_code}")
                top_warnings.append(f"missing_series:{va_code}")
            va_result = detect_series_anomalies(
                va_series if not va_series.empty else None,
                contamination=contamination,
                random_state=random_state,
            )
            va_payload = _series_payload(
                indicator_code=va_code,
                result=va_result,
                extra_warnings=va_extra or None,
            )

    available = bool(iip_payload["available"]) or bool(
        va_payload and va_payload.get("available")
    )
    # Aggregate threshold when any series scored; else null (no invented baseline).
    thresholds = []
    if iip_payload.get("threshold") is not None:
        thresholds.append(iip_payload["threshold"])
    if va_payload and va_payload.get("threshold") is not None:
        thresholds.append(va_payload["threshold"])
    threshold = thresholds[0] if thresholds else None

    return {
        "available": available,
        "method": "isolation_forest",
        "contamination": float(contamination),
        "threshold": threshold,
        "vsic_code": vsic,
        "as_of": date.today().isoformat(),
        "iip": iip_payload,
        "va": va_payload,
        "warnings": top_warnings,
        "message": (
            None
            if available
            else (
                "Thiếu series IIP/VA đủ dài để chạy anomaly — "
                "không bịa alert (chạy crawl GSO / seed macro trước)."
            )
        ),
    }
