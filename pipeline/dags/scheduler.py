"""Pipeline scheduler for periodic crawls."""

import time

import schedule

from backend.app.database import SessionLocal
from backend.app.models import PipelineJob
from backend.app.services import pipeline_service


def _run_job(name: str, func):
    db = SessionLocal()
    job = pipeline_service.create_job(db, name)
    try:
        records = func(db)
        pipeline_service.finish_job(db, job, "success", records)
        print(f"[{name}] completed: {records} records")
    except Exception as e:
        pipeline_service.finish_job(db, job, "failed", error=str(e))
        print(f"[{name}] failed: {e}")
    finally:
        db.close()


def run_all_pipelines():
    from crawlers.gso.iip_crawler import run_gso_crawl
    from crawlers.oecd.sdmx_client import run_oecd_crawl
    from crawlers.companies.listed_companies import run_company_crawl
    from crawlers.marketplace.shop_finder import run_marketplace_crawl
    from pipeline.cleaning.digital_metrics import compute_all_digital_metrics
    from pipeline.features.engineering import run_feature_engineering
    from ml.models.trainer import train_all_models

    pipelines = [
        ("gso_crawl", run_gso_crawl),
        ("oecd_crawl", run_oecd_crawl),
        ("company_crawl", run_company_crawl),
        ("marketplace_crawl", run_marketplace_crawl),
        ("digital_metrics", compute_all_digital_metrics),
        ("feature_engineering", run_feature_engineering),
        ("ml_training", train_all_models),
    ]
    for name, func in pipelines:
        _run_job(name, func)


def main():
    schedule.every().day.at("02:00").do(run_all_pipelines)
    print("Pipeline scheduler started. Running initial pipeline...")
    run_all_pipelines()
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
