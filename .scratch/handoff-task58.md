# Handoff — Task #58 ML Lab anomaly panel + LightGBM

**Status:** DONE  
**Branch:** `cursor/epic4-phase2-task58-mllab-anomaly-lightgbm`  
**Date:** 2026-07-30  
**Phase:** Epic 4 Phase 4.2 (Forecast & anomaly)  
**Base:** `origin/main` (post-#57 / #63)  
**PR:** _(filled after open)_  

---

## Delivered

- **NEW** `ml/models/lightgbm_model.py`
  - Train/forecast on same feature frame as XGBoost; **target stays `iip`**
  - Soft-fail `status=unavailable` when `lightgbm` missing (no crash of `train_all_models`)
  - Artifacts: `lightgbm_model.joblib`, `lightgbm_features.joblib`, `lightgbm_importance.json`
- **Extend** `ml/models/trainer.py` — `train_lightgbm` + compare path in `train_all_models` / `generate_forecast`
- **Extend** `backend/app/services/ml_lab_service.py` — feature importance for `lightgbm`
- **FE** `MLLab.jsx` — anomaly timeline (consume `GET /api/ml/anomaly`) + LightGBM in compare cards/holdout
- **Additive** `frontend/src/api.js` — `getAnomalies`, `getLightgbmFeatureImportance`, `forecastLightgbm`
- **Tests** `tests/ml/test_lightgbm.py` + lab/API importance coverage

## Verify results

```bash
python3 -c "import lightgbm; print(lightgbm.__version__)"  # 4.5.0
# darts not installed (ok)
PYTHONPATH=. pytest -q tests/ml/
# 50 passed
```

Pre-flight: #57 anomaly endpoint on `main` (`/api/ml/anomaly`).

## Boundaries respected

- Did **not** edit `ml/anomaly/**` core detector
- Did **not** touch shop_matcher / product_categorizer / Benchmark / monitoring (#63) / `docs/plan.md`
- No darts install

## Limitations

- LightGBM only appears in compare cards after a successful train registers metrics
- Anomaly panel honesty: empty/short series → banner, no fake points
- Monitoring contract (#63) still lists prior models only (out of scope)

## Next

- Task #60 shop matcher v2 / #64 feedback (per epic plan) — or wire LightGBM into monitoring candidates if desired
