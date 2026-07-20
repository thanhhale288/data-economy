"""Pipeline scheduler for periodic crawls."""

import time

import schedule

from backend.app.database import SessionLocal
from backend.app.services import pipeline_service


def _run_job(name: str, func, *, detail_from_result: bool = False):
    db = SessionLocal()
    job = pipeline_service.create_job(db, name)
    try:
        if detail_from_result:
            records, detail = func(db)
            pipeline_service.finish_job(db, job, "success", records, error=detail)
            print(f"[{name}] completed: {records} records — {detail}")
        else:
            records = func(db)
            pipeline_service.finish_job(db, job, "success", records)
            print(f"[{name}] completed: {records} records")
    except Exception as e:
        pipeline_service.finish_job(db, job, "failed", error=str(e))
        print(f"[{name}] failed: {e}")
    finally:
        db.close()


def _gso_with_detail(db):
    from crawlers.gso.iip_crawler import fetch_gso_macro, save_gso_records

    result = fetch_gso_macro()
    n = save_gso_records(db, result.records)
    return n, f"{result.status}: {result.detail[:400]}"


def _oecd_with_detail(db):
    from crawlers.oecd.sdmx_client import fetch_oecd_indicators, save_oecd_records

    result = fetch_oecd_indicators(country="VNM", include_peers=True)
    n = save_oecd_records(db, result.records)
    return n, result.detail_summary


def _data_cleaning_with_detail(db):
    from pipeline.cleaning.run_cleaning import run_data_cleaning

    return run_data_cleaning(db)


def run_all_pipelines():
    from crawlers.companies.listed_companies import run_company_crawl
    from crawlers.marketplace.shop_finder import run_marketplace_crawl
    from pipeline.cleaning.digital_metrics import compute_all_digital_metrics
    from pipeline.features.engineering import run_feature_engineering
    from ml.models.trainer import train_all_models

    _run_job("gso_crawl", _gso_with_detail, detail_from_result=True)
    _run_job("oecd_crawl", _oecd_with_detail, detail_from_result=True)
    for name, func in (
        ("company_crawl", run_company_crawl),
        ("marketplace_crawl", run_marketplace_crawl),
        ("digital_metrics", compute_all_digital_metrics),
    ):
        _run_job(name, func)
    # Task #10: primary clean before features (artifacts under data/processed/)
    _run_job("data_cleaning", _data_cleaning_with_detail, detail_from_result=True)
    for name, func in (
        ("feature_engineering", run_feature_engineering),
        ("ml_training", train_all_models),
    ):
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
