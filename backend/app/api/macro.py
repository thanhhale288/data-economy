from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import GsoMacro, OecdIndicator
from backend.app.schemas import GsoMacroOut, OecdIndicatorOut

router = APIRouter()


@router.get("/gso", response_model=list[GsoMacroOut])
def list_gso(
    vsic_code: str | None = None,
    indicator_code: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(GsoMacro)
    if vsic_code:
        q = q.filter(GsoMacro.vsic_code == vsic_code)
    if indicator_code:
        q = q.filter(GsoMacro.indicator_code == indicator_code)
    return q.order_by(GsoMacro.period).all()


@router.get("/oecd", response_model=list[OecdIndicatorOut])
def list_oecd(
    indicator_code: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(OecdIndicator)
    if indicator_code:
        q = q.filter(OecdIndicator.indicator_code == indicator_code)
    return q.order_by(OecdIndicator.period).all()
