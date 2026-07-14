from sqlalchemy.orm import Session, joinedload

from backend.app.models import Company
from backend.app.schemas import CompanyDetail, CompanyOut


def list_companies(db: Session) -> list[CompanyOut]:
    return db.query(Company).order_by(Company.stock_code).all()


def get_company(db: Session, stock_code: str) -> CompanyDetail | None:
    company = (
        db.query(Company)
        .options(
            joinedload(Company.digital_presence),
            joinedload(Company.digital_metrics),
            joinedload(Company.financial_reports),
            joinedload(Company.marketplace_listings),
            joinedload(Company.vsic),
        )
        .filter(Company.stock_code == stock_code.upper())
        .first()
    )
    return company
