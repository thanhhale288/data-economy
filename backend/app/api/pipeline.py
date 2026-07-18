from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal, get_db
from backend.app.schemas import CrawlTriggerRequest, PipelineJobOut
from backend.app.models import PipelineJob
from backend.app.services import pipeline_service

router = APIRouter()


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
        if crawler in ("features", "all"):
            from pipeline.features.engineering import run_feature_engineering

            records += run_feature_engineering(db)
        if crawler in ("ml", "all"):
            from ml.models.trainer import train_all_models

            records += train_all_models(db)

        # Persist crawl notes on success (fallback / unavailable series visibility).
        message = " | ".join(notes) if notes else None
        pipeline_service.finish_job(db, job, "success", records, error=message)
    except Exception as e:
        pipeline_service.finish_job(db, job, "failed", error=str(e))
    finally:
        db.close()


@router.get("/jobs", response_model=list[PipelineJobOut])
def list_jobs(db: Session = Depends(get_db)):
    return pipeline_service.list_jobs(db)


@router.post("/trigger", response_model=PipelineJobOut)
def trigger_crawl(
    request: CrawlTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = pipeline_service.create_job(db, f"crawl_{request.crawler}")
    background_tasks.add_task(_run_crawler, request.crawler, job.id)
    return job
