"""Task #15 — HTTP API tests for pipeline monitor endpoints."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import PipelineJob


@pytest.fixture()
def api_db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pipeline_api_test.db'}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()


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


def test_get_jobs_splits_detail_and_error(client, api_db):
    api_db.add_all(
        [
            PipelineJob(
                job_name="data_cleaning",
                status="success",
                records_processed=12,
                error_message="nan_filled=0; outliers=1",
                started_at=datetime(2024, 1, 1, 10, 0, 0),
                finished_at=datetime(2024, 1, 1, 10, 5, 0),
                created_at=datetime(2024, 1, 1, 10, 0, 0),
            ),
            PipelineJob(
                job_name="crawl_gso",
                status="failed",
                records_processed=0,
                error_message="connection reset",
                started_at=datetime(2024, 1, 2, 10, 0, 0),
                finished_at=datetime(2024, 1, 2, 10, 1, 0),
                created_at=datetime(2024, 1, 2, 10, 0, 0),
            ),
        ]
    )
    api_db.commit()

    res = client.get("/api/pipeline/jobs")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2

    by_name = {row["job_name"]: row for row in body}
    assert by_name["data_cleaning"]["detail"] == "nan_filled=0; outliers=1"
    assert by_name["data_cleaning"]["error_message"] is None
    assert by_name["crawl_gso"]["error_message"] == "connection reset"
    assert by_name["crawl_gso"]["detail"] is None


def test_get_status_last_runs(client, api_db):
    api_db.add(
        PipelineJob(
            job_name="oecd_crawl",
            status="success",
            records_processed=5,
            error_message="oecd:ok",
            started_at=datetime(2024, 3, 1, 8, 0, 0),
            finished_at=datetime(2024, 3, 1, 8, 2, 0),
            created_at=datetime(2024, 3, 1, 8, 0, 0),
        )
    )
    api_db.commit()

    res = client.get("/api/pipeline/status")
    assert res.status_code == 200
    body = res.json()
    assert body["staging_postgres"] is False
    families = {row["family"]: row for row in body["last_runs"]}
    assert set(families) >= {"gso", "oecd", "companies", "marketplace", "data_cleaning"}
    assert families["oecd"]["status"] == "success"
    assert families["oecd"]["detail"] == "oecd:ok"
    assert families["gso"]["status"] is None


def test_get_quality_available_and_missing(client, monkeypatch):
    from backend.app.api import pipeline as pipeline_api

    monkeypatch.setattr(
        pipeline_api.pipeline_service,
        "get_quality_report",
        lambda: {
            "available": False,
            "report_path": "data/processed/cleaning_report.json",
            "message": "Chưa có cleaning_report.json — không bịa số quality.",
            "summary": None,
            "report": None,
        },
    )
    missing = client.get("/api/pipeline/quality")
    assert missing.status_code == 200
    assert missing.json()["available"] is False
    assert missing.json()["summary"] is None
    assert "không bịa" in missing.json()["message"].lower()

    monkeypatch.setattr(
        pipeline_api.pipeline_service,
        "get_quality_report",
        lambda: {
            "available": True,
            "report_path": "data/processed/cleaning_report.json",
            "message": None,
            "summary": {
                "nan_filled": 3,
                "outliers_handled": 1,
                "marketplace_outliers_flagged": 2,
                "vsic_fails": 0,
                "series_missing": ["mei_ip"],
                "artifacts": ["cleaned_macro.parquet"],
                "vsic_companies_fail": 0,
                "vsic_gso_fail": 0,
            },
            "report": {"series_missing": ["mei_ip"]},
        },
    )
    ok = client.get("/api/pipeline/quality")
    assert ok.status_code == 200
    payload = ok.json()
    assert payload["available"] is True
    assert payload["summary"]["nan_filled"] == 3
    assert payload["summary"]["series_missing"] == ["mei_ip"]


def test_trigger_cleaning_creates_data_cleaning_job(client, api_db, monkeypatch):
    from backend.app.api import pipeline as pipeline_api

    calls: list[tuple[str, int]] = []

    def fake_run(crawler: str, job_id: int):
        calls.append((crawler, job_id))

    monkeypatch.setattr(pipeline_api, "_run_crawler", fake_run)

    res = client.post("/api/pipeline/trigger", json={"crawler": "cleaning"})
    assert res.status_code == 200
    body = res.json()
    assert body["job_name"] == "data_cleaning"
    assert body["status"] == "running"
    assert calls == [("cleaning", body["id"])]

    # Job persisted via overridden session
    job = api_db.query(PipelineJob).filter_by(id=body["id"]).one()
    assert job.job_name == "data_cleaning"


def test_trigger_rejects_unknown_crawler(client):
    res = client.post("/api/pipeline/trigger", json={"crawler": "not-a-real-job"})
    assert res.status_code == 400
    assert "crawler must be one of" in res.json()["detail"]
