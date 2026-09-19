"""Filesystem layout for mini-gold artifacts (T06)."""

from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parents[1]
CASCADE_JSONL = ROOT / "data" / "processed" / "extraction_cascade" / "indicators_raw.jsonl"
CASCADE_MANIFEST = ROOT / "data" / "processed" / "extraction_cascade" / "manifest.json"
PROCESSED_DIR = ROOT / "data" / "processed" / "mini_gold"
WORKSHEET_CSV = PROCESSED_DIR / "worksheet_89.csv"
SAMPLE_MANIFEST = PROCESSED_DIR / "sample_manifest.json"
PROVENANCE_MD = PROCESSED_DIR / "PROVENANCE.md"
METRICS_JSON = PROCESSED_DIR / "metrics.json"
ERROR_ANALYSIS_MD = PROCESSED_DIR / "error_analysis.md"
PREDICTIONS_VS_GOLD_CSV = PROCESSED_DIR / "predictions_vs_gold.csv"

BOOL_FIELDS = ("has_product_catalog", "has_order_cart")
PRESENCE_FIELDS = ("social_links", "marketplace_links")
PAYMENT_FIELD = "payment_methods"
LANG_FIELD = "website_language"
ALL_FIELDS = BOOL_FIELDS + (PAYMENT_FIELD,) + PRESENCE_FIELDS + (LANG_FIELD,)
