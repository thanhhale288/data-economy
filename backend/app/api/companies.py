from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import CompanyDetail, CompanyOut
from backend.app.services import company_service

router = APIRouter()


@router.get("/", response_model=list[CompanyOut])
def list_companies(
    db: Session = Depends(get_db),
    vsic: str | None = Query(
        default=None,
        description="Filter by VSIC code or 2-digit division (e.g. 27, 2740)",
    ),
):
    return company_service.list_companies(db, vsic=vsic)


@router.get("/{stock_code}", response_model=CompanyDetail)
def get_company(stock_code: str, db: Session = Depends(get_db)):
    company = company_service.get_company(db, stock_code)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company
