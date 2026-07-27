"""Shallow company-universe coverage honesty (ADR-0003 / Task #50)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.universe import UniverseCoverageNote
from backend.app.services import universe_service

router = APIRouter()


@router.get("/coverage", response_model=UniverseCoverageNote)
def get_universe_coverage(db: Session = Depends(get_db)):
    """Return coverage honesty for Digital VA / percentiles vs Section C.

    Works with an empty universe stub — never invents national firm rows or
    treats ``companies`` count as Section C coverage.
    """
    return universe_service.get_coverage_note(db)
