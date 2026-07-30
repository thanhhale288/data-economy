"""Task #57 — API + service tests for /api/ml/anomaly (honesty when missing)."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import GsoMacro, VsicCode
from backend.app.services import anomaly_service as svc


@pytest.fixture()
def api_db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'anomaly_api_test.db'}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    session.add(
        VsicCode(
            vsic_code="C",
            isic_code="C",
            level=1,
            name_vi="Che bien",
            name_en="Manufacturing",
        )
    )
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def client(api_db):
    def override_get_db():
        try:
            yield api_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_iip(session, series: pd.Series) -> None:
    for period, value in series.items():
        p = (
            period.date()
            if hasattr(period, "date")
            else date(period.year, period.month, 1)
        )
        session.add(
            GsoMacro(
                vsic_code="C",
                indicator_code="IIP_C",
                indicator_name="IIP Section C",
                period=p,
                value=float(value),
                unit="index",
                source="test",
            )
        )
    session.commit()


def _seed_va(session, series: pd.Series, code: str = "VA_C") -> None:
    for period, value in series.items():
        p = (
            period.date()
            if hasattr(period, "date")
            else date(period.year, period.month, 1)
        )
        session.add(
            GsoMacro(
                vsic_code="C",
                indicator_code=code,
                indicator_name="VA Section C",
                period=p,
                value=float(value),
                unit="billion_vnd_constant_2010",
                source="test",
            )
        )
    session.commit()


def test_anomaly_endpoint_openapi(client):
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert "/api/ml/anomaly" in paths
    assert "get" in paths["/api/ml/anomaly"]


def test_anomaly_endpoint_missing_series_no_fake_alert(client):
    res = client.get("/api/ml/anomaly")
    assert res.status_code == 200
    body = res.json()
    assert body["available"] is False
    assert body["threshold"] is None
    assert body["iip"]["available"] is False
    assert body["iip"]["points"] == []
    assert body["iip"]["n_anomalies"] == 0
    assert any("missing_series:IIP_C" in w for w in body["warnings"])
    assert body["va"] is not None
    assert body["va"]["available"] is False
    assert body["va"]["points"] == []
    assert body["va"]["n_anomalies"] == 0
    assert "không bịa" in (body.get("message") or "").lower()


def test_anomaly_endpoint_sufficient_series_deterministic(
    client, api_db, synthetic_iip_series
):
    series = synthetic_iip_series.copy()
    series.iloc[40] = float(series.iloc[40]) + 80.0
    _seed_iip(api_db, series)
    # VA present but shorter than MIN — honesty: no fake VA anomalies.
    short_va = pd.Series(
        [1000.0, 1010.0, 1020.0],
        index=pd.date_range("2024-01-01", periods=3, freq="MS"),
    )
    _seed_va(api_db, short_va)

    a = client.get("/api/ml/anomaly").json()
    b = client.get("/api/ml/anomaly").json()

    assert a["available"] is True
    assert a["iip"]["available"] is True
    assert a["iip"]["n_scored"] > 0
    assert a["threshold"] is not None
    assert a["iip"]["n_anomalies"] == sum(
        1 for p in a["iip"]["points"] if p["is_anomaly"]
    )
    assert a["va"]["available"] is False
    assert a["va"]["points"] == []
    assert a["va"]["n_anomalies"] == 0
    assert any("insufficient" in w for w in a["va"]["warnings"])

    assert [p["is_anomaly"] for p in a["iip"]["points"]] == [
        p["is_anomaly"] for p in b["iip"]["points"]
    ]
    scores_a = np.asarray([p["score"] for p in a["iip"]["points"]], dtype=float)
    scores_b = np.asarray([p["score"] for p in b["iip"]["points"]], dtype=float)
    np.testing.assert_allclose(scores_a, scores_b, rtol=0, atol=1e-12)


def test_anomaly_service_include_va_false_skips_va(api_db, synthetic_iip_series):
    _seed_iip(api_db, synthetic_iip_series)
    out = svc.detect_iip_va_anomalies(api_db, include_va=False)
    assert out["iip"]["available"] is True
    assert out["va"] is None


def test_anomaly_service_va_when_series_long_enough(api_db, synthetic_iip_series):
    _seed_iip(api_db, synthetic_iip_series)
    va = synthetic_iip_series * 10.0
    _seed_va(api_db, va)
    out = svc.detect_iip_va_anomalies(api_db, include_va=True)
    assert out["available"] is True
    assert out["iip"]["available"] is True
    assert out["va"]["available"] is True
    assert out["va"]["indicator_code"] == "VA_C"
    assert out["va"]["n_scored"] > 0
