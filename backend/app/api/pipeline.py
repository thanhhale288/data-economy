from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal, get_db
from backend.app.schemas import (
    CleaningQualityReportOut,
    CrawlTriggerRequest,
    PipelineJobOut,
    PipelineMonitorStatusOut,
)
from backend.app.models import PipelineJob
from backend.app.services import pipeline_service

router = APIRouter()

# Trigger ids accepted by POST /trigger (includes Module 3 data_cleaning).
TRIGGER_IDS = frozenset(
    {
        "gso",
        "oecd",
        "companies",
        "marketplace",
        "metrics",
        "features",
        "ml",
        "cleaning",
        "all",
    }
)


def _job_out(job: PipelineJob) -> PipelineJobOut:
    err, detail = pipeline_service.split_job_messages(job)
    return PipelineJobOut(
        id=job.id,
        job_name=job.job_name,
        status=job.status,
        records_processed=job.records_processed,
        error_message=err,
        detail=detail,
        started_at=job.started_at,
        finished_at=job.finished_at,
        created_at=job.created_at,
    )


def _trigger_job_name(crawler: str) -> str:
    if crawler == "cleaning":
        return "data_cleaning"
    return f"crawl_{crawler}"


def _run_crawler(crawler: str, job_id: int):
    db = SessionLocal()
    job = db.query(PipelineJob).get(job_id)
    notes: list[str] = []
    try:
        records = 0
        if crawler in ("gso", "all"):
            from crawlers.gso.iip_crawler import fetch_gso_macro, save_gso_records

            result = fetch_gso_macro()
            records += save_gso_records(db, result.records)
            notes.append(f"gso:{result.status}:{result.detail[:400]}")
        if crawler in ("oecd", "all"):
            from crawlers.oecd.sdmx_client import fetch_oecd_indicators, save_oecd_records

            result = fetch_oecd_indicators(country="VNM", include_peers=True)
            records += save_oecd_records(db, result.records)
            notes.append(f"oecd:{result.detail_summary}")
        if crawler in ("companies", "all"):
            from crawlers.companies.listed_companies import run_company_crawl

            records += run_company_crawl(db)
        if crawler in ("marketplace", "all"):
            from crawlers.marketplace.shop_finder import run_marketplace_crawl

            records += run_marketplace_crawl(db)
        if crawler in ("metrics", "all"):
            from pipeline.cleaning.digital_metrics import compute_all_digital_metrics

            records += compute_all_digital_metrics(db)
        # Task #10 / Module 3: clean before features (parquet + cleaning_report.json).
        if crawler in ("cleaning", "all"):
            from pipeline.cleaning.run_cleaning import run_data_cleaning

            n, detail = run_data_cleaning(db)
            records += n
            notes.append(f"data_cleaning:{detail}")
        if crawler in ("features", "all"):
            from pipeline.features.engineering import run_feature_engineering

            records += run_feature_engineering(db)
        if crawler in ("ml", "all"):
            from ml.models.trainer import train_all_models

            records += train_all_models(db)

        message = " | ".join(notes) if notes else None
        pipeline_service.finish_job(db, job, "success", records, detail=message)
    except Exception as e:
        pipeline_service.finish_job(db, job, "failed", error=str(e))
    finally:
        db.close()


@router.get("/jobs", response_model=list[PipelineJobOut])
def list_jobs(db: Session = Depends(get_db)):
    return [_job_out(j) for j in pipeline_service.list_jobs(db)]


@router.get("/status", response_model=PipelineMonitorStatusOut)
def monitor_status(db: Session = Depends(get_db)):
    return pipeline_service.get_monitor_status(db)


@router.get("/quality", response_model=CleaningQualityReportOut)
def cleaning_quality():
    """Tóm tắt quality report từ parquet artifact — không bịa khi thiếu file."""
    return pipeline_service.get_quality_report()


@router.post("/trigger", response_model=PipelineJobOut)
def trigger_crawl(
    request: CrawlTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    crawler = (request.crawler or "").strip().lower()
    if crawler not in TRIGGER_IDS:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=f"crawler must be one of: {', '.join(sorted(TRIGGER_IDS))}",
        )
    job = pipeline_service.create_job(db, _trigger_job_name(crawler))
    background_tasks.add_task(_run_crawler, crawler, job.id)
    return _job_out(job)
