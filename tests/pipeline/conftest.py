"""Shared fixtures for pipeline cleaning tests."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import Company, GsoMacro, VsicCode


@pytest.fixture()
def db_session(tmp_path):
    """SQLite session with minimal VSIC + optional seed helpers (no network)."""
    engine = create_engine(f"sqlite:///{tmp_path / 'pipeline_cleaning_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    for code, name_vi in (
        ("C", "Công nghiệp chế biến, chế tạo"),
        ("10", "Sản xuất thực phẩm"),
        ("24", "Sản xuất kim loại"),
        ("2740", "Sản xuất thiết bị chiếu sáng điện"),
        ("2410", "Sản xuất sắt, thép"),
        ("1050", "Chế biến sữa"),
    ):
        level = 1 if code == "C" else (2 if len(code) == 2 else 4)
        session.add(
            VsicCode(
                vsic_code=code,
                isic_code=code,
                level=level,
                name_vi=name_vi,
                name_en=name_vi,
            )
        )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def seeded_cleaning_db(db_session):
    """Company + GSO macro rows so run_data_cleaning has something to touch."""
    company = Company(
        stock_code="RAL",
        name="Công ty Cổ phần Bóng đèn Rạng Đông",
        vsic_code="2740",
        exchange="HOSE",
    )
    db_session.add(company)
    db_session.add(
        GsoMacro(
            indicator_code="IIP",
            indicator_name="Chỉ số sản xuất công nghiệp",
            vsic_code="C",
            period=date(2024, 1, 1),
            value=100.0,
            unit="index",
            source="GSO",
        )
    )
    db_session.commit()
    return db_session
