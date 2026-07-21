"""Task #18 — Benchmark API honesty + prefill contract."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.main import app
from backend.app.schemas import BenchmarkInput
from backend.app.services import benchmark_service as svc


def _client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_compare_empty_peers_api(db_session):
    client = _client(db_session)
    try:
        res = client.post(
            "/api/benchmark/compare",
            json={
                "vsic_code": "3290",
                "operating_revenue": 1e12,
                "profit_before_tax": 1e11,
                "employees": 100,
                "total_assets": 2e12,
                "total_equity": 1e12,
                "current_assets": 8e11,
                "current_liabilities": 4e11,
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["peer_count"] == 0
        assert "insufficient_peers" in body["warnings"]
        assert body["percentiles"].get("roa") is None
        assert body["comparison"].get("roa") == "insufficient_peers"
    finally:
        app.dependency_overrides.clear()


def test_compare_with_peers_api(peers_division_27):
    client = _client(peers_division_27)
    try:
        res = client.post(
            "/api/benchmark/compare",
            json={
                "vsic_code": "2740",
                "operating_revenue": 5.2e12,
                "profit_before_tax": 4.2e11,
                "employees": 3200,
                "total_assets": 6.8e12,
                "total_equity": 3.2e12,
                "current_assets": 3.1e12,
                "current_liabilities": 2.1e12,
                "operating_expenses": 4e12,
                "cost_of_goods": 3.2e12,
                "rental_cost": 8.5e10,
                "remuneration": 6.8e11,
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["peer_count"] == 2
        assert body["peer_scope"] == "vsic_division:27"
        assert body["roa"] is not None
        assert body["percentiles"]["roa"] is not None
        assert body["expenditure_related_ratio"] is not None
        assert body["purchase_goods_share"] is not None
        assert body["industry_averages"]["expenditure_related_ratio"] is not None
        assert "prototype_listed_sample" in body["warnings"]
    finally:
        app.dependency_overrides.clear()


def test_prefill_api(peers_division_27):
    client = _client(peers_division_27)
    try:
        ok = client.get("/api/benchmark/prefill/RAL")
        assert ok.status_code == 200
        assert ok.json()["stock_code"] == "RAL"

        missing = client.get("/api/benchmark/prefill/BMP")
        # BMP not seeded in this fixture → 404 honest
        assert missing.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_run_benchmark_matches_schema(peers_division_27):
    result = svc.run_benchmark(
        peers_division_27,
        BenchmarkInput(
            vsic_code="2740",
            operating_revenue=5.2e12,
            profit_before_tax=4.2e11,
            employees=3200,
            total_assets=6.8e12,
            total_equity=3.2e12,
            current_assets=3.1e12,
            current_liabilities=2.1e12,
        ),
    )
    dumped = result.model_dump()
    assert "peer_count" in dumped
    assert "warnings" in dumped
    assert dumped["percentiles"]["equity_ratio"] is not None
