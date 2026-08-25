"""Filesystem layout for the Japan calibration pilot (Evol-1 T08)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "jp_calibration"
LABELS_DIR = ROOT / "data" / "raw" / "jp_labels"
PROCESSED_DIR = ROOT / "data" / "processed" / "jp_calibration"

NTA_ZIP_DIR = RAW_DIR / "nta_zips"
NTA_CSV_DIR = RAW_DIR / "nta_csv"
SEARCH_CACHE_DIR = RAW_DIR / "search_cache"
PROFILE_CACHE_DIR = RAW_DIR / "profile_cache"
SERP_CACHE_DIR = RAW_DIR / "serps_cache"
PAGE_CACHE_DIR = RAW_DIR / "pages_cache"

NTA_INDEX_FILE = RAW_DIR / "nta_index.json"
SEARCH_POOL_FILE = RAW_DIR / "gbizinfo_search_pool.json"
PROVENANCE_NTA = RAW_DIR / "PROVENANCE.md"
PROVENANCE_LABELS = LABELS_DIR / "PROVENANCE.md"

IDENTITY_FILE = RAW_DIR / "identity_300.json"
LABELS_FILE = LABELS_DIR / "labels_300.json"
SAMPLE_MANIFEST = PROCESSED_DIR / "sample_manifest.json"
PREDICTIONS_FILE = PROCESSED_DIR / "predictions.json"
METRICS_FILE = PROCESSED_DIR / "metrics.json"
ERROR_ANALYSIS_FILE = PROCESSED_DIR / "error_analysis.md"
COMPARISON_FILE = PROCESSED_DIR / "comparison_vn28.md"
REVIEW_CSV = PROCESSED_DIR / "review_30.csv"
RQ3_FILE = PROCESSED_DIR / "rq3_logic_changes.md"

VN_METRICS_FILE = ROOT / "data" / "processed" / "url_finder" / "metrics.json"

SAMPLE_N = 300
SAMPLE_SEED = 20260825
DEFAULT_PREFECTURES = ("静岡県", "愛知県", "大阪府")
DEFAULT_PREFECTURE_CODES = {"静岡県": "22", "愛知県": "23", "大阪府": "27"}
