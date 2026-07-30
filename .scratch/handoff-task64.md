# Handoff — Task #64 Feedback-to-training loop

**Status:** DONE  
**Branch:** `cursor/epic4-phase5-task64-feedback-training-loop`  
**Date:** 2026-07-30  
**Phase:** Epic 4 Phase 4.5 (Monitoring & feedback loop)  
**Base:** `origin/main`  
**Next:** (phase 4.5 closed when #63+#64 merged) — optional Prefect only if OCR batch + retrain needs it later  
**Prefect:** **không cài** (thin `schedule` hook đủ)

---

## Delivered

| Piece | Path |
|-------|------|
| Schema | `backend/app/schemas/feedback_signal.py` |
| Service + JSONL store | `backend/app/services/feedback_signal.py` → `data/feedback/training_signals.jsonl` |
| API | `POST /api/benchmark/feedback` in `backend/app/api/benchmark.py` |
| FE soft hook | `Benchmark.jsx` confirm checkbox → `api.benchmarkFeedback` (no narrative/#61 touch beyond existing) |
| API client | `frontend/src/api.js` → `benchmarkFeedback` |
| Monitoring counter (#63) | `feedback_signals_count` on `MlMonitoringCounters` + Pipeline strip |
| Scheduler | thin `feedback_ingest` job in `pipeline/dags/scheduler.py` (count only, no retrain) |
| Tests | `tests/benchmark/test_feedback_signal.py` |

---

## Signal schema (persisted JSONL line)

```json
{
  "id": "uuid",
  "timestamp": "ISO-8601 UTC (naive)",
  "ticker": "RAL | null",
  "source_type": "docai_extract | cafef_prefill | manual | …",
  "diff_count": 1,
  "field_diffs": [
    { "field": "operating_revenue", "before": 1000000, "after": 1200000 }
  ]
}
```

**Allowlisted fields only:** stock_code, vsic_code, operating_revenue, profit_before_tax, employees, operating_expenses, cost_of_goods, rental_cost, remuneration, total_assets, total_equity, current_assets, current_liabilities.

**Never persisted:** `raw_pdf`, `file_bytes`, `content`, `api_key`, `filename`, tokens/secrets, binary/base64 blobs.

---

## Verify

```bash
PYTHONPATH=. pytest -q -k feedback
# 6 passed
```

---

## Boundaries respected

- Không sửa OCR/extract core (#52–#56)
- Không sửa shop matcher / categorizer / anomaly
- Không rewrite `docs/plan.md`
- Soft touch Benchmark confirm only; narrative panel #61 untouched

---

## Giải thích dễ hiểu

### Đã làm
- Khi user tick xác nhận sau DocAI prefill, FE gửi trước/sau field lên API; backend ghi 1 dòng JSONL an toàn.
- Pipeline Monitor hiện thêm counter số feedback signals; scheduler chỉ đếm (chưa auto-retrain).

### Hạn chế
- Chưa train lại model từ signal (chỉ lưu tín hiệu).
- CafeF prefill lưu snapshot nhưng POST signal chỉ khi confirm DocAI (checkbox); có thể mở rộng sau.
