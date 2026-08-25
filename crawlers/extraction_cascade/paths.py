"""Filesystem layout for extraction-cascade artifacts."""

from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = PACKAGE_DIR / "config"
ROOT = PACKAGE_DIR.parents[1]
RAW_DIR = ROOT / "data" / "raw" / "extraction_cascade"
PROCESSED_DIR = ROOT / "data" / "processed" / "extraction_cascade"
PAGES_CACHE_DIR = RAW_DIR / "pages_cache"
COHORT_PATH = RAW_DIR / "cohort.json"
INDICATORS_JSONL = PROCESSED_DIR / "indicators_raw.jsonl"
INDICATORS_CSV = PROCESSED_DIR / "indicators_raw.csv"
CONFLICTS_CSV = PROCESSED_DIR / "tier_conflicts.csv"
SUMMARY_JSON = PROCESSED_DIR / "summary.json"
MANIFEST_JSON = PROCESSED_DIR / "manifest.json"
PROVENANCE_MD = PROCESSED_DIR / "PROVENANCE.md"
CONFLICT_NOTES_MD = PROCESSED_DIR / "conflict_notes.md"
