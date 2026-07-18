"""Shared helpers for marketplace crawler tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import Company, VsicCode

FIXTURES = Path(__file__).parent / "fixtures"

FIXED_TICKERS = (
    "RAL",
    "HPG",
    "VNM",
    "FPT",
    "GVR",
    "DGC",
    "MSN",
    "PNJ",
    "REE",
    "BMP",
)


def load_fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def load_fixture_json(name: str) -> dict:
    import json

    return json.loads(load_fixture_text(name))


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'marketplace_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(
        VsicCode(
            vsic_code="2740",
            isic_code="2740",
            level=4,
            name_vi="Sản xuất thiết bị chiếu sáng điện",
            name_en="Manufacture of electric lighting equipment",
        )
    )
    session.add(
        VsicCode(
            vsic_code="1050",
            isic_code="1050",
            level=4,
            name_vi="Chế biến sữa và các sản phẩm từ sữa",
            name_en="Manufacture of dairy products",
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def sample_company(db_session):
    company = Company(
        stock_code="RAL",
        name="Công ty Cổ phần Bóng đèn Rạng Đông",
        vsic_code="2740",
        exchange="HOSE",
        website_url="https://rangdong.com.vn",
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture()
def ten_companies(db_session):
    """Minimal company rows for the fixed 10-ticker set."""
    specs = [
        ("RAL", "Công ty Cổ phần Bóng đèn Rạng Đông", "2740"),
        ("HPG", "Tập đoàn Hòa Phát", "2410"),
        ("VNM", "Công ty Cổ phần Sữa Việt Nam", "1050"),
        ("FPT", "Tập đoàn FPT", "2620"),
        ("GVR", "Tập đoàn Công nghiệp Cao su Việt Nam", "2211"),
        ("DGC", "Công ty Cổ phần Hóa chất Đức Giang", "2011"),
        ("MSN", "Tập đoàn Masan", "1071"),
        ("PNJ", "Công ty Cổ phần Vàng bạc Đá quý Phú Nhuận", "3211"),
        ("REE", "Công ty Cổ phần Cơ điện lạnh", "2710"),
        ("BMP", "Công ty Cổ phần Nhựa Bình Minh", "2220"),
    ]
    # Extra VSIC codes referenced above (beyond fixtures)
    for code, name_vi in [
        ("2410", "Sản xuất sắt, thép"),
        ("2620", "Sản xuất máy vi tính"),
        ("2211", "Sản xuất sản phẩm từ cao su"),
        ("2011", "Sản xuất hóa chất cơ bản"),
        ("1071", "Sản xuất bánh mì"),
        ("3211", "Sản xuất đồ trang sức"),
        ("2710", "Sản xuất động cơ điện"),
        ("2220", "Sản xuất sản phẩm từ plastic"),
    ]:
        if not db_session.query(VsicCode).filter_by(vsic_code=code).first():
            db_session.add(
                VsicCode(
                    vsic_code=code,
                    isic_code=code,
                    level=4,
                    name_vi=name_vi,
                    name_en=name_vi,
                )
            )
    db_session.commit()

    companies = []
    for stock_code, name, vsic in specs:
        c = Company(
            stock_code=stock_code,
            name=name,
            vsic_code=vsic,
            exchange="HOSE",
        )
        db_session.add(c)
        companies.append(c)
    db_session.commit()
    for c in companies:
        db_session.refresh(c)
    return companies
