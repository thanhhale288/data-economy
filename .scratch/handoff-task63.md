# Handoff — Task #63 ML monitoring contract

**Status:** DONE  
**Branch:** `cursor/epic4-phase5-task63-ml-monitoring-contract`  
**Date:** 2026-07-30  
**Phase:** Epic 4 Phase 4.5 (Monitoring & feedback loop)  
**Base:** `origin/main` @ `179957c`  
**Commit / PR:** *(điền sau push)*  
**Next:** Task #64 — Feedback-to-training loop  
**great-expectations:** **không cài** (default SQLAlchemy/API contract đủ)

---

## Delivered

| Piece | Path |
|-------|------|
| Schemas | `backend/app/schemas/ml_monitoring.py` |
| Service | `backend/app/services/ml_monitoring.py` |
| API | `backend/app/api/ml_monitoring.py` → **`GET /api/ml/monitoring`** |
| Router mount | `backend/app/api/__init__.py` under `/ml` (cùng prefix forecast/anomaly) |
| FE counters | `frontend/src/pages/Pipeline.jsx` + `api.getMlMonitoring()` |
| Tests | `tests/ml/test_ml_monitoring.py` |

### Contract fields (per model)

`model_name`, `metrics` (mae/rmse/mape…), `as_of`, `drift_flag`, `drift_score`, `sample_count`, `warning`, `artifact_present`

### Honesty

- Registry / metrics thiếu → null metrics + `warning` (`registry_missing` / `metrics_missing`)
- Không có `data/models/ml_monitoring_baseline.json` → `drift_flag`/`drift_score` = **null** + warning (không bịa drift)
- Có baseline → `drift_score = current_mape - baseline_mape`; flag khi `|score| >= threshold` (default 5.0)

### Counters (API + Pipeline strip)

`models_tracked`, `models_with_metrics`, `models_missing_metrics`, `models_with_drift`, `models_unknown_drift`, `artifacts_on_disk`, `baseline_available`

---

## Verify

```bash
PYTHONPATH=. pytest -q -k ml_monitoring
# 4 passed
```

---

## Boundaries respected

- Không sửa anomaly (#57), LightGBM/MLLab (#58), marketplace matcher/categorizer, narrative, feedback (#64), `docs/plan.md`
- Không cài Prefect / great-expectations

---

## Giải thích dễ hiểu

### Đã làm
- API + schema theo dõi chất lượng model (MAE/RMSE/MAPE) và drift (chỉ khi có baseline).
- Pipeline Monitor hiện counters + bảng trạng thái model.

### Hạn chế
- Chưa có auto-retrain / feedback ingest (#64).
- Baseline file chưa ship sẵn — cần tạo `ml_monitoring_baseline.json` để bật drift.
- GE optional chưa dùng.
