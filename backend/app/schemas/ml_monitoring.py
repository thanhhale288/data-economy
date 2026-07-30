"""ML monitoring contract schemas (Task #63) — quality / drift snapshots."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModelMetricSnapshot(BaseModel):
    """Per-model quality snapshot. Missing pieces stay null + warning."""

    model_name: str
    metrics: dict[str, float | None] = Field(default_factory=dict)
    as_of: datetime | None = None
    drift_flag: bool | None = None
    drift_score: float | None = None
    sample_count: int | None = None
    warning: str | None = None
    artifact_present: bool = False
    is_active: bool | None = None
    version: str | None = None


class MlMonitoringCounters(BaseModel):
    """Dashboard-readable counters for Pipeline / ML monitor."""

    models_tracked: int = 0
    models_with_metrics: int = 0
    models_missing_metrics: int = 0
    models_with_drift: int = 0
    models_unknown_drift: int = 0
    artifacts_on_disk: int = 0
    baseline_available: bool = False


class MlMonitoringStatusOut(BaseModel):
    """GET /api/ml/monitoring response."""

    as_of: datetime
    models: list[ModelMetricSnapshot] = Field(default_factory=list)
    counters: MlMonitoringCounters
    warnings: list[str] = Field(default_factory=list)
    note: str | None = None
    great_expectations: bool = False
    backend: str = "sqlalchemy_registry"


class MlMonitoringBaselineIn(BaseModel):
    """Optional baseline payload shape (file or future POST — not wired in #63)."""

    models: dict[str, dict[str, Any]] = Field(default_factory=dict)
    mape_drift_threshold: float = 5.0
