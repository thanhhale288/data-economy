"""Shared helpers for company crawler tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import VsicCode

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'companies_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Minimal VSIC rows used by the 10 seed tickers.
    for code, name_vi in (
        ("2740", "Sản xuất thiết bị chiếu sáng điện"),
        ("2410", "Sản xuất sắt, thép"),
        ("1050", "Chế biến sữa"),
        ("2620", "Sản xuất máy vi tính"),
        ("2211", "Sản xuất sản phẩm từ cao su"),
        ("2011", "Sản xuất hóa chất cơ bản"),
        ("1071", "Sản xuất bánh mì"),
        ("3211", "Sản xuất đồ trang sức"),
        ("2710", "Sản xuất động cơ điện"),
        ("2220", "Sản xuất sản phẩm từ plastic"),
    ):
        session.add(
            VsicCode(
                vsic_code=code,
                isic_code=code,
                level=4,
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
