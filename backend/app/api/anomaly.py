"""Anomaly detection API (Task #57) — IIP / VA Isolation Forest."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services import anomaly_service

router = APIRouter()


@router.get("/anomaly")
def detect_anomaly(
    vsic_code: str = Query("C", description="VSIC section / division filter for gso_macro"),
    include_va: bool = Query(True, description="Also score VA_C when present"),
    va_indicator: str = Query(
        "VA_C",
        description="VA indicator: VA_C or VA_C_NOMINAL",
    ),
    contamination: float = Query(
        0.05,
        ge=0.01,
        le=0.49,
        description="IsolationForest contamination (expected outlier fraction)",
    ),
    db: Session = Depends(get_db),
):
    """Score IIP (+ optional VA) for anomalies. Missing series → empty + warning.

    Does not write to the database. Never invents anomaly alerts when data is
    absent or too short for a stable Isolation Forest fit.
    """
    return anomaly_service.detect_iip_va_anomalies(
        db,
        vsic_code=vsic_code,
        include_va=include_va,
        va_indicator=va_indicator,
        contamination=contamination,
    )
