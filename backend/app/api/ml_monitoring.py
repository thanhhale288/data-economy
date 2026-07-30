"""ML monitoring API (Task #63) — quality/drift contract + counters."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.ml_monitoring import MlMonitoringStatusOut
from backend.app.services import ml_monitoring as ml_monitoring_service

router = APIRouter()


@router.get("/monitoring", response_model=MlMonitoringStatusOut)
def ml_monitoring_status(db: Session = Depends(get_db)) -> MlMonitoringStatusOut:
    """Model quality metrics + optional drift vs baseline.

    Mounted under ``/api/ml/monitoring`` (same ``/ml`` prefix as forecast/anomaly).
    Missing registry metrics or baseline → null drift + warnings (no invented values).
    """
    return ml_monitoring_service.get_monitoring_status(db)
