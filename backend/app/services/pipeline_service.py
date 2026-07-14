from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models import PipelineJob


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
) -> PipelineJob:
    job.status = status
    job.records_processed = records
    job.error_message = error
    job.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job
