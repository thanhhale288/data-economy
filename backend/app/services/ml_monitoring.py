"""ML monitoring contract — model quality metrics + optional drift vs baseline.

Honesty rules (Task #63):
- Missing registry row / metrics / artifact → null fields + explicit warning.
- Drift flag/score only when a baseline artifact exists; never invent drift.
- great-expectations is optional and not required for this contract.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models import ModelPrediction, ModelRegistry
from backend.app.schemas.ml_monitoring import (
    MlMonitoringCounters,
    MlMonitoringStatusOut,
    ModelMetricSnapshot,
)
from backend.app.services import feedback_signal as feedback_signal_service


logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = REPO_ROOT / "data" / "models"
DEFAULT_BASELINE_PATH = MODELS_DIR / "ml_monitoring_baseline.json"

# Canonical forecast models the monitor always reports (even if registry empty).
CANONICAL_MODELS: tuple[str, ...] = ("arima", "xgboost", "lstm")

# Disk artifacts used to set artifact_present (honesty when file missing).
ARTIFACT_CANDIDATES: dict[str, tuple[str, ...]] = {
    "arima": ("arima_model.joblib",),
    "xgboost": ("xgboost_model.joblib", "xgboost_importance.json"),
    "lstm": ("lstm_model.pt", "lstm_meta.joblib"),
}

METRIC_KEYS = ("mae", "rmse", "mape")
DEFAULT_MAPE_DRIFT_THRESHOLD = 5.0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _coerce_metric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_metrics(raw: dict[str, Any] | None) -> dict[str, float | None]:
    raw = raw or {}
    out: dict[str, float | None] = {}
    for key in METRIC_KEYS:
        out[key] = _coerce_metric(raw.get(key))
    # Preserve extra numeric metrics without inventing keys.
    for key, value in raw.items():
        if key in out:
            continue
        coerced = _coerce_metric(value)
        if coerced is not None:
            out[str(key)] = coerced
    return out


def _has_any_metric(metrics: dict[str, float | None]) -> bool:
    return any(v is not None for v in metrics.values())


def artifact_present(model_name: str, *, models_dir: Path | None = None) -> bool:
    root = models_dir or MODELS_DIR
    names = ARTIFACT_CANDIDATES.get(model_name.lower())
    if not names:
        # Unknown model: treat any path hint as absent unless file exists later.
        return False
    return any((root / name).is_file() for name in names)


def load_baseline(
    path: Path | None = None,
) -> tuple[dict[str, dict[str, Any]], float, bool, str | None]:
    """Return (models_map, mape_threshold, available, warning)."""
    baseline_path = path or DEFAULT_BASELINE_PATH
    if not baseline_path.is_file():
        return {}, DEFAULT_MAPE_DRIFT_THRESHOLD, False, None
    try:
        payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (
            {},
            DEFAULT_MAPE_DRIFT_THRESHOLD,
            False,
            f"baseline_unreadable:{baseline_path.name}:{exc}",
        )
    if not isinstance(payload, dict):
        return (
            {},
            DEFAULT_MAPE_DRIFT_THRESHOLD,
            False,
            f"baseline_invalid_shape:{baseline_path.name}",
        )
    models = payload.get("models") if "models" in payload else payload
    if not isinstance(models, dict):
        return (
            {},
            DEFAULT_MAPE_DRIFT_THRESHOLD,
            False,
            f"baseline_missing_models:{baseline_path.name}",
        )
    threshold = _coerce_metric(payload.get("mape_drift_threshold"))
    if threshold is None:
        threshold = DEFAULT_MAPE_DRIFT_THRESHOLD
    return models, float(threshold), True, None


def _compute_drift(
    metrics: dict[str, float | None],
    baseline_row: dict[str, Any] | None,
    threshold: float,
    *,
    baseline_available: bool,
) -> tuple[bool | None, float | None, str | None]:
    """Compare current MAPE to baseline MAPE. No baseline → null drift."""
    if not baseline_available:
        return None, None, "no_baseline_artifact"
    if not baseline_row:
        return None, None, "no_baseline_for_model"
    current = metrics.get("mape")
    base = _coerce_metric(baseline_row.get("mape"))
    if current is None or base is None:
        return None, None, "mape_unavailable_for_drift"
    score = float(current) - float(base)
    flag = abs(score) >= float(threshold)
    return flag, score, None


def _latest_registry_row(db: Session, model_name: str) -> ModelRegistry | None:
    return (
        db.query(ModelRegistry)
        .filter(ModelRegistry.model_name == model_name)
        .order_by(ModelRegistry.trained_at.desc(), ModelRegistry.id.desc())
        .first()
    )


def _sample_count(db: Session, model_name: str) -> int | None:
    n = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.model_name == model_name)
        .count()
    )
    return int(n)


def _model_names(db: Session) -> list[str]:
    names = list(CANONICAL_MODELS)
    extra = (
        db.query(ModelRegistry.model_name)
        .distinct()
        .order_by(ModelRegistry.model_name.asc())
        .all()
    )
    for (name,) in extra:
        if name and name not in names:
            names.append(name)
    return names


def build_model_snapshot(
    db: Session,
    model_name: str,
    *,
    baseline_models: dict[str, dict[str, Any]],
    baseline_available: bool,
    mape_threshold: float,
    models_dir: Path | None = None,
) -> ModelMetricSnapshot:
    row = _latest_registry_row(db, model_name)
    present = artifact_present(model_name, models_dir=models_dir)
    warnings: list[str] = []

    if row is None:
        warnings.append("registry_missing")
        metrics: dict[str, float | None] = {k: None for k in METRIC_KEYS}
        as_of = None
        is_active = None
        version = None
        samples = None
    else:
        metrics = _normalize_metrics(row.metrics if isinstance(row.metrics, dict) else None)
        as_of = row.trained_at
        is_active = bool(row.is_active)
        version = row.version
        samples = _sample_count(db, model_name)
        if not _has_any_metric(metrics):
            warnings.append("metrics_missing")
        if row.artifact_path:
            # Prefer explicit path when present.
            art = Path(row.artifact_path)
            if not art.is_file() and not present:
                warnings.append("artifact_path_missing")
                present = False
            elif art.is_file():
                present = True

    if not present:
        warnings.append("artifact_missing")

    drift_flag, drift_score, drift_warn = _compute_drift(
        metrics,
        baseline_models.get(model_name) if isinstance(baseline_models.get(model_name), dict) else None,
        mape_threshold,
        baseline_available=baseline_available,
    )
    if drift_warn:
        warnings.append(drift_warn)

    warning = ";".join(warnings) if warnings else None
    return ModelMetricSnapshot(
        model_name=model_name,
        metrics=metrics,
        as_of=as_of,
        drift_flag=drift_flag,
        drift_score=drift_score,
        sample_count=samples,
        warning=warning,
        artifact_present=present,
        is_active=is_active,
        version=version,
    )


def get_monitoring_status(
    db: Session,
    *,
    baseline_path: Path | None = None,
    models_dir: Path | None = None,
    feedback_store_path: Path | None = None,
) -> MlMonitoringStatusOut:
    """Assemble monitoring contract for API / Pipeline counters."""
    baseline_models, threshold, baseline_ok, baseline_warn = load_baseline(baseline_path)
    global_warnings: list[str] = []
    if baseline_warn:
        global_warnings.append(baseline_warn)
    if not baseline_ok:
        global_warnings.append(
            "drift_unavailable:no_baseline — không bịa drift_flag/score"
        )

    snapshots = [
        build_model_snapshot(
            db,
            name,
            baseline_models=baseline_models,
            baseline_available=baseline_ok,
            mape_threshold=threshold,
            models_dir=models_dir,
        )
        for name in _model_names(db)
    ]

    with_metrics = sum(1 for s in snapshots if _has_any_metric(s.metrics))
    missing_metrics = len(snapshots) - with_metrics
    with_drift = sum(1 for s in snapshots if s.drift_flag is True)
    unknown_drift = sum(1 for s in snapshots if s.drift_flag is None)
    artifacts = sum(1 for s in snapshots if s.artifact_present)
    feedback_count = feedback_signal_service.count_signals(
        store_path=feedback_store_path,
    ).count

    note = (
        "ML monitoring contract (Task #63): metrics from model_registry; "
        "drift only when data/models/ml_monitoring_baseline.json exists; "
        "feedback_signals_count from Task #64 JSONL store."
    )
    return MlMonitoringStatusOut(
        as_of=_utc_now(),
        models=snapshots,
        counters=MlMonitoringCounters(
            models_tracked=len(snapshots),
            models_with_metrics=with_metrics,
            models_missing_metrics=missing_metrics,
            models_with_drift=with_drift,
            models_unknown_drift=unknown_drift,
            artifacts_on_disk=artifacts,
            baseline_available=baseline_ok,
            feedback_signals_count=feedback_count,
        ),
        warnings=global_warnings,
        note=note,
        great_expectations=False,
        backend="sqlalchemy_registry",
    )
