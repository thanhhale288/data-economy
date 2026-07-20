"""Pipeline job tracking + Module 3 monitor helpers (parquet quality report)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models import PipelineJob
from pipeline.cleaning.run_cleaning import CLEANING_REPORT_NAME, PROCESSED_DIR

# Canonical monitor families → job_name variants (scheduler vs API trigger).
MONITOR_FAMILIES: dict[str, tuple[str, ...]] = {
    "gso": ("gso_crawl", "crawl_gso"),
    "oecd": ("oecd_crawl", "crawl_oecd"),
    "companies": ("company_crawl", "crawl_companies"),
    "marketplace": ("marketplace_crawl", "crawl_marketplace"),
    "data_cleaning": ("data_cleaning", "crawl_cleaning"),
}


def list_jobs(db: Session, limit: int = 50) -> list[PipelineJob]:
    return (
        db.query(PipelineJob)
        .order_by(PipelineJob.created_at.desc())
        .limit(limit)
        .all()
    )


def create_job(db: Session, job_name: str) -> PipelineJob:
    job = PipelineJob(job_name=job_name, status="running", started_at=datetime.utcnow())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def finish_job(
    db: Session,
    job: PipelineJob,
    status: str,
    records: int = 0,
    error: str | None = None,
    *,
    detail: str | None = None,
) -> PipelineJob:
    """Persist outcome. Success notes go in ``detail``; failures in ``error``.

    Both are stored in ``pipeline_jobs.error_message`` (no migration); the API
    splits them when serializing responses.
    """
    job.status = status
    job.records_processed = records
    if status == "failed":
        job.error_message = error
    else:
        job.error_message = detail if detail is not None else error
    job.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


def split_job_messages(job: PipelineJob) -> tuple[str | None, str | None]:
    """Return ``(error_message, detail)`` for API responses."""
    raw = job.error_message
    if not raw:
        return None, None
    if job.status == "failed":
        return raw, None
    return None, raw


def get_last_runs(db: Session) -> list[dict[str, Any]]:
    """Latest job per monitor family (crawl + data_cleaning)."""
    rows: list[dict[str, Any]] = []
    for family, names in MONITOR_FAMILIES.items():
        job = (
            db.query(PipelineJob)
            .filter(PipelineJob.job_name.in_(names))
            .order_by(PipelineJob.created_at.desc())
            .first()
        )
        if job is None:
            rows.append(
                {
                    "family": family,
                    "job_name": None,
                    "status": None,
                    "records_processed": None,
                    "started_at": None,
                    "finished_at": None,
                    "error_message": None,
                    "detail": None,
                }
            )
            continue
        err, detail = split_job_messages(job)
        rows.append(
            {
                "family": family,
                "job_name": job.job_name,
                "status": job.status,
                "records_processed": job.records_processed,
                "started_at": job.started_at,
                "finished_at": job.finished_at,
                "error_message": err,
                "detail": detail,
            }
        )
    return rows


def get_monitor_status(db: Session, *, job_limit: int = 50) -> dict[str, Any]:
    jobs = list_jobs(db, limit=job_limit)
    failed = sum(1 for j in jobs if j.status == "failed")
    return {
        "last_runs": get_last_runs(db),
        "jobs_listed": len(jobs),
        "jobs_failed_in_list": failed,
        "staging_postgres": False,
        "note": (
            "Bản sạch mặc định = parquet + pipeline_jobs; "
            "staging Postgres chưa bật (tuỳ chọn §4.1)."
        ),
    }


def _sum_macro_field(macro: dict[str, Any], field: str) -> int:
    total = 0
    for series in macro.values():
        if isinstance(series, dict):
            val = series.get(field)
            if isinstance(val, (int, float)):
                total += int(val)
    return total


def _sum_flagged(flagged: Any) -> int:
    if not isinstance(flagged, dict):
        return 0
    total = 0
    for val in flagged.values():
        if isinstance(val, (int, float)):
            total += int(val)
    return total


def summarize_cleaning_report(report: dict[str, Any]) -> dict[str, Any]:
    """Derive Module 3 quality chips from a real cleaning_report.json body."""
    macro = report.get("macro") if isinstance(report.get("macro"), dict) else {}
    vsic = report.get("vsic") if isinstance(report.get("vsic"), dict) else {}
    marketplace = (
        report.get("marketplace") if isinstance(report.get("marketplace"), dict) else {}
    )

    nan_filled = _sum_macro_field(macro, "short_gap_filled") + _sum_macro_field(
        macro, "long_gap_filled"
    )
    outliers_handled = _sum_macro_field(macro, "outliers_handled")
    mp_flagged = _sum_flagged(marketplace.get("outliers_flagged"))
    vsic_fails = int(vsic.get("companies_fail") or 0) + int(vsic.get("gso_fail") or 0)
    series_missing = report.get("series_missing")
    if not isinstance(series_missing, list):
        series_missing = []
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list):
        artifacts = []

    return {
        "nan_filled": nan_filled,
        "outliers_handled": outliers_handled,
        "marketplace_outliers_flagged": mp_flagged,
        "vsic_fails": vsic_fails,
        "series_missing": [str(s) for s in series_missing],
        "artifacts": [str(a) for a in artifacts],
        "vsic_companies_fail": int(vsic.get("companies_fail") or 0),
        "vsic_gso_fail": int(vsic.get("gso_fail") or 0),
    }


def get_quality_report(
    *,
    report_path: Path | None = None,
) -> dict[str, Any]:
    """Read ``data/processed/cleaning_report.json`` or return available=false.

    Never invent counts when the file is missing or unreadable.
    """
    path = report_path or (PROCESSED_DIR / CLEANING_REPORT_NAME)
    rel = str(path)
    try:
        rel = str(path.relative_to(Path.cwd()))
    except ValueError:
        pass

    if not path.is_file():
        return {
            "available": False,
            "report_path": rel,
            "message": (
                "Chưa có cleaning_report.json — chạy job data_cleaning "
                "(không bịa số quality)."
            ),
            "summary": None,
            "report": None,
        }

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "available": False,
            "report_path": rel,
            "message": f"Không đọc được cleaning_report.json: {exc}",
            "summary": None,
            "report": None,
        }

    if not isinstance(raw, dict):
        return {
            "available": False,
            "report_path": rel,
            "message": "cleaning_report.json không đúng schema (cần object).",
            "summary": None,
            "report": None,
        }

    return {
        "available": True,
        "report_path": rel,
        "message": None,
        "summary": summarize_cleaning_report(raw),
        "report": raw,
    }
