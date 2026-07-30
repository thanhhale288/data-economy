# Handoff — Task #57 Anomaly detector v1 (IIP/VA)

**Status:** DONE  
**Branch:** `cursor/epic4-phase2-task57-anomaly-detector-v1`  
**Date:** 2026-07-30  
**Phase:** Epic 4 Phase 4.2 (Forecast & anomaly)  
**Base:** `origin/main`  
**Commit:** `6df4c41`  
**PR:** https://github.com/thanhhale288/data-economy/pull/45  
**Next:** Task #58 — ML Lab anomaly panel + model compare refresh

---

## Delivered

- **Pipeline** `ml/anomaly/`:
  - `detector.py` — Isolation Forest on lag/roll/growth features
  - Fixed `random_state=42` for deterministic scores/flags
  - Baseline threshold = sklearn decision boundary `0.0`
  - Empty / short series → `available=false`, empty `points`, explicit warnings (no invented alerts)
- **Service** `backend/app/services/anomaly_service.py`:
  - Loads `IIP_C` (+ optional `VA_C` / `VA_C_NOMINAL`) from `gso_macro`
  - No DB writes
- **API** `GET /api/ml/anomaly` via `backend/app/api/anomaly.py` (included under `/ml`)
  - Query: `vsic_code`, `include_va`, `va_indicator`, `contamination`
  - Response: scores/flags + threshold + per-series warnings + honesty message when unavailable
- **Tests** `tests/ml/test_anomaly.py`, `tests/ml/test_anomaly_api.py`

---

## Verify results

```bash
PYTHONPATH=. pytest -q tests/ml/ -k anomaly
# 10 passed, 30 deselected
```

Smoke: OpenAPI contains `/api/ml/anomaly`; empty DB → `available=false`, no fake anomalies.

Pre-flight: `import sklearn, torch` → ok (no new deps; no darts / sentence-transformers / OCR).

---

## Boundaries respected

- No `frontend/**` (Task #58)
- No `ml/shop_matcher/**`, `ml/product_categorizer/**`, `ml/models/lightgbm*`
- No DocAI / benchmark extract changes
- No edits to `docs/plan.md` or handoff-task5[2-6]
- Forecast / train logic in `ml.py` untouched

---

## Next (#58)

- FE ML Lab anomaly timeline panel wiring `GET /api/ml/anomaly`
- Optional LightGBM train path + model compare refresh
