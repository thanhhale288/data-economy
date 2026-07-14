from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import DashboardSummary
from backend.app.services import dashboard_service

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    return dashboard_service.get_dashboard_summary(db)


@router.get("/iip")
def get_iip(vsic_code: str = "C", db: Session = Depends(get_db)):
    return dashboard_service.get_iip_timeseries(db, vsic_code)


@router.get("/heatmap")
def get_heatmap(db: Session = Depends(get_db)):
    return dashboard_service.get_industry_heatmap(db)


@router.get("/oecd-vs-gso")
def get_oecd_vs_gso(db: Session = Depends(get_db)):
    return dashboard_service.get_oecd_vs_gso(db)
