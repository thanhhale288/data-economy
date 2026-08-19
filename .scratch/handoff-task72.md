# Handoff — Task #72 Drift baseline from registry MAPE

**Status:** DONE  
**Branch:** `cursor/epic5-phase2-task72-ml-drift-baseline`  
**Date:** 2026-08-19  
**Phase:** Epic 5 Phase 2  
**Base:** `origin/main` @ `3772afe` (Task #71 LightGBM already merged)

---

## Delivered

| Piece | Path |
|-------|------|
| Writer | `scripts/write_ml_monitoring_baseline.py` |
| Baseline JSON | `data/models/ml_monitoring_baseline.json` |
| Tests | `tests/ml/test_write_ml_monitoring_baseline.py` (existing `test_ml_monitoring.py` unchanged) |
| Docs | `docs/ops-demo.md` — refresh baseline after a retrain that meets the quality bar |

### Writer behaviour

- Reads the **latest** `ModelRegistry` row per canonical model (`arima`, `xgboost`, `lightgbm`, `lstm`).
- Writes only models with a real numeric `mape`. Never invents MAPE or fills zeros.
- Empty / unreachable registry → warning, exit non-zero, **no file written**.
- `--dry-run` prints payload and does not write.
- `--database-url` points at a DB without copying `.env` into a worktree.

### Baseline JSON — written from real registry

**Yes — committed.** Source = `ModelRegistry` on parent local sqlite `data/mfg_economy.db` (absolute `sqlite:////Users/hale/Code/AI in Data Economy/data/mfg_economy.db`). Latest row per model:

| model | mape | trained_at (UTC naive) | version |
|-------|------|------------------------|---------|
| arima | 31.7036 | 2026-07-28T03:38:13.243398 | 1.0 |
| xgboost | 6.4405 | 2026-07-28T03:38:13.328289 | 1.0 |
| lstm | 10.0786 | 2026-07-28T03:38:14.244912 | 1.0 |

**Omitted:** `lightgbm` — `registry_missing` (no ModelRegistry row in that sqlite). Parent `.env` Postgres was not queried (avoid copying/printing secrets); sqlite already had real MAPE.

`mape_drift_threshold` = 5.0 (service default). Payload `source` = `ModelRegistry`.

---

## Testing results

```bash
source "/Users/hale/Code/AI in Data Economy/.venv/bin/activate"
cd "/Users/hale/Code/AI in Data Economy/.worktrees/t72"
PYTHONPATH=. pytest -q tests/ml/ -k 'ml_monitoring or baseline or drift'
# 9 passed, 52 deselected
```

Existing missing-file → null drift and present-baseline → drift tests still pass (`models_tracked == 4`). Writer tests use a sqlite fixture (fixture MAPE only).

Script stdout (write, real MAPE):

```
source=ModelRegistry database=cli --database-url
wrote .../data/models/ml_monitoring_baseline.json
  arima: mape=31.7036 trained_at=2026-07-28T03:38:13.243398
  xgboost: mape=6.4405 trained_at=2026-07-28T03:38:13.328289
  lstm: mape=10.0786 trained_at=2026-07-28T03:38:14.244912
omitted (no real numeric mape):
  lightgbm:registry_missing
```

---

## Boundaries respected

- Did not invent GSO/OECD numbers or MAPE.
- Forecast target stays `iip`.
- Did not commit `.pt` / `.joblib` binaries.
- Did not copy `.env` into the worktree.
- Did not tick `docs/plan.md`.
