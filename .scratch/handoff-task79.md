# Handoff — Task #79 Feedback alias harvest (v1)

**Status:** DONE  
**Branch:** `cursor/epic5-phase4-task79-feedback-alias-harvest`  
**Date:** 2026-08-19  
**Phase:** Epic 5 Phase 5.4 (Narrative + feedback)  
**Base:** `origin/main` @ `f17bf4c`  
**Commit:** `266ef2d`  
**PR:** https://github.com/thanhhale288/data-economy/pull/72  
**Prefect:** **không cài** (không gọi Prefect; không retrain sklearn/OCR)

---

## Delivered

| Piece | Path |
|-------|------|
| Harvest service | `backend/app/services/feedback_alias_harvest.py` |
| CLI | `scripts/harvest_feedback_aliases.py` |
| JSONL fixture | `tests/benchmark/fixtures/feedback_alias_harvest.jsonl` |
| Tests | `tests/benchmark/test_feedback_alias_harvest.py` |
| Ops note | `docs/ops-demo.md` (subsection mới, không đụng OCR) |

---

## How proposals work

1. Đọc JSONL (`data/feedback/training_signals.jsonl` hoặc `--input`). Mỗi dòng chỉ có `field_diffs` (field allowlisted + before/after số), `ticker`, `source_type`, timestamp — **không** có nhãn BCTC gốc hay PDF.
2. Đếm số lần người sửa **theo field** (và breakdown theo ticker).
3. Khi count ≥ N (mặc định 3; `--min-count` hoặc env `FEEDBACK_ALIAS_HARVEST_MIN_COUNT`) → proposal `review_aliases`: *nên xem lại* `_LABEL_ALIASES` / unit rules. `proposed_aliases` luôn `[]` (không bịa alias vì JSONL không có label).
4. Heuristic đơn vị: nếu ≥ N edit cùng field có after/before ≈ 1000 hoặc 1e6 (dung sai 8%) → thêm `review_unit_scale` (`nghin` / `trieu`, hoặc over-applied ×0.001 / ×1e-6). `employees` / mã VSIC không scale.
5. Output markdown + JSON tuỳ chọn. **Không** ghi `bctc_extract.py`. **Không** auto-apply.

---

## Verify

```bash
PYTHONPATH=. pytest -q tests/benchmark/ -k 'feedback or harvest or alias'
# 25 passed, 66 deselected

PYTHONPATH=. python scripts/harvest_feedback_aliases.py --help
PYTHONPATH=. python scripts/harvest_feedback_aliases.py \
  --input tests/benchmark/fixtures/feedback_alias_harvest.jsonl
```

Fixture: `operating_revenue` ×3 (ratio 1000) → alias review + nghìn unit proposal; `employees` ×2 → không proposal.

---

## Boundaries respected

- Không patch `_LABEL_ALIASES` / không ghi `bctc_extract.py` lúc runtime
- Không persist raw PDF / secrets trong report
- Không Prefect, không retrain sklearn/OCR
- Không tick `docs/plan.md` / epic5 checklist
- Không sửa `Benchmark.jsx` / categorizer / shop matcher seeds
- Không bịa số GSO/OECD

---

## Giải thích dễ hiểu

### Đã làm
- Script đọc các lần user sửa số trên form Benchmark/DocAI, đếm theo field, và **đề xuất** field nào cần người xem lại alias/đơn vị (nghìn/triệu) khi sửa đủ nhiều lần.
- Báo cáo markdown/JSON cho ops; extract code giữ nguyên.

### Hạn chế
- JSONL không có chữ trên BCTC gốc → v1 **không** đề xuất chuỗi alias mới.
- Không tự sửa extract. Người vẫn phải edit `bctc_extract.py` tay nếu đồng ý proposal.
