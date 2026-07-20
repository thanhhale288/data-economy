"""Task #17 — FE contract smoke: api.js paths match Module 1–4 E2E surface."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
API_JS = REPO_ROOT / "frontend" / "src" / "api.js"

# Endpoints the offline E2E chain exercises (Dashboard / Company / Pipeline / ML).
REQUIRED_API_SNIPPETS = (
    "/dashboard/summary",
    "/dashboard/iip",
    "/dashboard/heatmap",
    "/dashboard/oecd-vs-gso",
    "/companies/",
    "/companies/${code}",
    "/pipeline/jobs",
    "/pipeline/status",
    "/pipeline/quality",
    "/pipeline/trigger",
    "/ml/models",
    "/ml/predictions",
    "/ml/feature-importance",
    "/ml/forecast",
)

REQUIRED_EXPORTS = (
    "getSummary",
    "getIip",
    "getHeatmap",
    "getOecdVsGso",
    "getCompanies",
    "getCompany",
    "getPipelineJobs",
    "getPipelineStatus",
    "getPipelineQuality",
    "getModels",
    "getPredictions",
    "getFeatureImportance",
    "forecast",
)


def test_frontend_api_js_covers_e2e_surface():
    """FE client exposes the routes used after crawl→clean→ML (build verifies compile)."""
    if not API_JS.is_file():
        pytest.skip(f"frontend api.js missing: {API_JS}")
    text = API_JS.read_text(encoding="utf-8")
    for snippet in REQUIRED_API_SNIPPETS:
        assert snippet in text, f"api.js missing path snippet {snippet!r}"
    for name in REQUIRED_EXPORTS:
        assert f"{name}:" in text or f"{name} :" in text, f"api.js missing export {name!r}"


def test_frontend_pages_exist_for_modules():
    """Module pages exist so npm run build can smoke-compile the E2E UI surface."""
    pages = REPO_ROOT / "frontend" / "src" / "pages"
    for name in ("Dashboard.jsx", "CompanyDetail.jsx", "Pipeline.jsx", "MLLab.jsx"):
        path = pages / name
        assert path.is_file(), f"missing FE page for E2E surface: {path}"
