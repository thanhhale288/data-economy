# Handoff — Task #71 LightGBM train ops + monitoring candidate

**Status:** DONE  
**Branch:** `cursor/epic5-phase2-task71-lightgbm-train-ops`  
**Date:** 2026-08-19  
**Phase:** Epic 5 Phase 5.2 (Forecast / anomaly productize)  
**Base:** `origin/main` @ `58d2bc2`  
**PR:** https://github.com/thanhhale288/data-economy/pull/61  
**Commit:** `3cd1652`

---

## Delivered

- `CANONICAL_MODELS` and `ARTIFACT_CANDIDATES` in `backend/app/services/ml_monitoring.py` now include **lightgbm** (`lightgbm_model.joblib`, `lightgbm_importance.json`).
- Empty registry: LightGBM still appears with **null** mae/rmse/mape + `registry_missing` / `artifact_missing` (existing honesty path). Soft-fail when the `lightgbm` package is missing is unchanged.
- `docs/ops-demo.md` — how to train on local DB: `POST /api/ml/train`, `./run.sh train`, or `train_all_models`; Pipeline job `ml_training`. Target remains `iip`.
- `.gitignore` — do not commit `data/models/lightgbm_model.joblib` / `lightgbm_features.joblib`.
- Tests updated: empty monitor tracks **4** models; untrained LightGBM stays null.

## Train command actually run

Ran **`train_lightgbm`** only (not `train_all_models` / `POST /api/ml/train`) against local Postgres `mfg_economy` (114 `IIP_C` rows). Reason: `train_all_models` would overwrite git-tracked ARIMA/XGBoost/LSTM artifacts in the worktree.

```
status=ok  mae=20.2852  rmse=25.65  mape=9.9306
```

These MAPE/MAE/RMSE are from that local fit — not invented. Registry now has an active `lightgbm` row. Artifacts written under the worktree (`…/.worktrees/t71/data/models/lightgbm_*`); **not committed**. `artifact_path` in Postgres points at that worktree path — re-run train from the checkout you serve (see ops-demo) before removing the worktree.

`POST /api/ml/train` was **not** called (would retrain all four models).

## Testing results

```bash
cd ".worktrees/t71"
source ".venv/bin/activate"   # repo-root venv
PYTHONPATH=. pytest -q tests/ml/ -k 'lightgbm or ml_monitoring'
# 12 passed, 45 deselected, 2 warnings
```

## Boundaries

- Did not install darts; did not change Digital VA / VDEI; did not edit `docs/plan.md` or `.scratch/epic5-remain-plan.md`.
- Did not commit `.env`, `.pt`, or LightGBM `.joblib`.
- Did not tick the Epic 5 checklist.

## Do not reopen

Monitoring list + ops note + local train recorded. Drift baseline file is Task #72. Do not reopen this task to invent MAPE, bake binaries, or switch the forecast target off `iip`.
