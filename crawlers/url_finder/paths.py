"""Filesystem locations for URL-finder v0 (Evol-1 T03)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "url_finder"
PROCESSED_DIR = ROOT / "data" / "processed" / "url_finder"
CONFIG_DIR = Path(__file__).resolve().parent / "config"
SEED_FILE = ROOT / "data" / "seeds" / "companies.json"

HINTS_FILE = RAW_DIR / "masothue_hints.json"
IDENTITY_FILE = RAW_DIR / "identity_28.json"
LABELS_FILE = RAW_DIR / "labels_28.json"
PROVENANCE_FILE = RAW_DIR / "PROVENANCE.md"
SERP_CACHE_DIR = RAW_DIR / "serps_cache"
PAGE_CACHE_DIR = RAW_DIR / "pages_cache"

PREDICTIONS_FILE = PROCESSED_DIR / "predictions.json"
METRICS_FILE = PROCESSED_DIR / "metrics.json"
ERROR_ANALYSIS_FILE = PROCESSED_DIR / "error_analysis.md"
MANIFEST_FILE = PROCESSED_DIR / "manifest.json"
