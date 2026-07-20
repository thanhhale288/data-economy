"""Task #15 — Pipeline monitor service (status + quality report)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from backend.app.models import PipelineJob
from backend.app.services import pipeline_service as svc


@pytest.fixture()
def db_session(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from backend.app.database import Base

    engine = create_engine(f"sqlite:///{tmp_path / 'pipeline_monitor_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_quality_report_missing_is_explicit(tmp_path):
    missing = tmp_path / "cleaning_report.json"
    result = svc.get_quality_report(report_path=missing)

    assert result["available"] is False
    assert result["summary"] is None
    assert result["report"] is None
    assert "không bịa" in result["message"].lower() or "chưa có" in result["message"].lower()


def test_quality_report_summarizes_real_json(tmp_path):
    path = tmp_path / "cleaning_report.json"
    path.write_text(
        json.dumps(
            {
                "macro": {
                    "iip": {
                        "short_gap_filled": 2,
                        "long_gap_filled": 1,
                        "outliers_handled": 3,
                    },
                    "indigo": {
                        "short_gap_filled": 0,
                        "long_gap_filled": 0,
                        "outliers_handled": 1,
                    },
                },
                "vsic": {"companies_fail": 1, "gso_fail": 2},
                "marketplace": {"outliers_flagged": {"price": 4, "revenue_est": 1}},
                "artifacts": ["cleaned_macro.parquet"],
                "series_missing": ["mei_ip"],
            }
        ),
        encoding="utf-8",
    )

    result = svc.get_quality_report(report_path=path)

    assert result["available"] is True
    assert result["message"] is None
    summary = result["summary"]
    assert summary["nan_filled"] == 3
    assert summary["outliers_handled"] == 4
    assert summary["marketplace_outliers_flagged"] == 5
    assert summary["vsic_fails"] == 3
    assert summary["series_missing"] == ["mei_ip"]
    assert summary["artifacts"] == ["cleaned_macro.parquet"]
    # Must not invent series that aren't in the file
    assert "mei_bci" not in summary["series_missing"]


def test_last_runs_groups_scheduler_and_trigger_names(db_session):
    db_session.add_all(
        [
            PipelineJob(
                job_name="crawl_gso",
                status="success",
                records_processed=10,
                error_message="gso:ok",
                started_at=datetime(2024, 1, 1, 1, 0, 0),
                finished_at=datetime(2024, 1, 1, 1, 5, 0),
                created_at=datetime(2024, 1, 1, 1, 0, 0),
            ),
            PipelineJob(
                job_name="gso_crawl",
                status="failed",
                records_processed=0,
                error_message="timeout",
                started_at=datetime(2024, 1, 2, 1, 0, 0),
                finished_at=datetime(2024, 1, 2, 1, 1, 0),
                created_at=datetime(2024, 1, 2, 1, 0, 0),
            ),
            PipelineJob(
                job_name="data_cleaning",
                status="success",
                records_processed=100,
                error_message="records=100; nan_filled=0",
                started_at=datetime(2024, 1, 2, 2, 0, 0),
                finished_at=datetime(2024, 1, 2, 2, 10, 0),
                created_at=datetime(2024, 1, 2, 2, 0, 0),
            ),
        ]
    )
    db_session.commit()

    runs = {row["family"]: row for row in svc.get_last_runs(db_session)}

    assert runs["gso"]["job_name"] == "gso_crawl"
    assert runs["gso"]["status"] == "failed"
    assert runs["gso"]["error_message"] == "timeout"
    assert runs["gso"]["detail"] is None

    assert runs["data_cleaning"]["status"] == "success"
    assert runs["data_cleaning"]["detail"] == "records=100; nan_filled=0"
    assert runs["data_cleaning"]["error_message"] is None

    assert runs["oecd"]["status"] is None
    assert runs["marketplace"]["job_name"] is None


def test_finish_job_splits_success_detail_from_failure(db_session):
    ok = svc.create_job(db_session, "data_cleaning")
    svc.finish_job(db_session, ok, "success", 5, detail="nan_filled=0")
    err_msg, detail = svc.split_job_messages(ok)
    assert err_msg is None
    assert detail == "nan_filled=0"

    bad = svc.create_job(db_session, "crawl_oecd")
    svc.finish_job(db_session, bad, "failed", error="boom")
    err_msg, detail = svc.split_job_messages(bad)
    assert err_msg == "boom"
    assert detail is None


def test_monitor_status_notes_no_staging(db_session):
    status = svc.get_monitor_status(db_session)
    assert status["staging_postgres"] is False
    assert "parquet" in status["note"].lower()
