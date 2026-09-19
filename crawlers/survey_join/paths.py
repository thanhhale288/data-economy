"""Filesystem defaults for survey ↔ web join (no network)."""

from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parents[1]

CASCADE_JSONL = ROOT / "data" / "processed" / "extraction_cascade" / "indicators_raw.jsonl"
FRAME_PILOT_CSV = ROOT / "data" / "raw" / "frame_pilot" / "frame_pilot.csv"
# Leftover demo financials — survey_join must never read this for DT × %.
SEED_COMPANIES_JSON = ROOT / "data" / "seeds" / "companies.json"

JOINED_CSV_NAME = "joined.csv"
JOINED_JSONL_NAME = "joined.jsonl"
SUMMARY_JSON_NAME = "summary.json"

SURVEY_COLUMNS = (
    "mst",
    "company_name",
    "vsic_4digit",
    "ticker",
    "website_url_self_report",
    "has_website",
    "has_product_catalog",
    "has_order_cart",
    "payment_methods",
    "has_social_links",
    "has_marketplace_links",
    "marketplace_names",
    "online_revenue_share_bin",
    "revenue_vnd",
    "revenue_year",
    "respondent_role",
    "respondent_email",
    "notes",
)

WEB_FLAG_FIELDS = (
    "has_website",
    "has_product_catalog",
    "has_order_cart",
    "has_social_links",
    "has_marketplace_links",
    "has_payment_methods",
)
