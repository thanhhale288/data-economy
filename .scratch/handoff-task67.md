# Handoff — Task #67 English aliases for BCTC extract

**Status:** DONE  
**Branch:** `cursor/epic5-phase1-task67-bctc-english-aliases`  
**Date:** 2026-08-19  
**Phase:** Epic 5 Phase 5.1 (DocAI harden)  
**Base:** `origin/main` @ `58d2bc2`  
**Commit / PR:** (filled after `gh pr create`)

---

## Delivered

- English label aliases in `backend/app/services/bctc_extract.py` `_LABEL_ALIASES` (longer phrases before shorter), **in addition to** existing Vietnamese aliases:
  - `profit before tax` → `profit_before_tax`
  - `revenue from sales`, `net revenue` → `operating_revenue`
  - `total assets` → `total_assets` (with `total current assets` / `current assets` steal-prevention, same pattern as VI)
  - `owner's equity` / `owners' equity` / `owners equity` / `total equity` → `total_equity`
  - `number of employees` / `employees` → `employees`
- English unit phrases, same scales as nghìn/triệu (no new scales):
  - million: `in millions of dong/VND`, `VND million`, close variants → ×1_000_000, warning `unit_detected_million_vnd`
  - thousand: `in thousands` (+ of dong/VND variants) → ×1_000, warning `unit_detected_thousand_vnd`
  - `employees` still never scaled; `DEFAULT_FIELD_CONFIDENCE_THRESHOLD` unchanged (0.75)
- `_fold` maps typographic apostrophes (`’`) to ASCII so Helvetica/pdfplumber `owner's equity` still matches
- Synthetic English text PDF (no PII, not a HOSE filing): `tests/benchmark/fixtures/sample_bctc_text_en.pdf`
- Golden case `text_full_en` in `tests/benchmark/golden/extract_golden_cases.json`
- Tests in `tests/benchmark/test_bctc_extract.py` + eval slot counts updated in `test_bctc_extract_eval.py`

**Not changed:** API, FE, OCR deps/`lang`, `docs/plan.md`, `.scratch/epic5-remain-plan.md`.

---

## Giải thích dễ hiểu

### Đã làm được gì
- PDF chữ tiếng Anh với nhãn chuẩn (Net revenue, Profit before tax, Employees, Total assets, Owner's equity) map đủ 5 field whitelist, cùng đơn vị triệu/nghìn như báo cáo tiếng Việt.
- Báo cáo tiếng Việt cũ không bị hỏng — alias VI vẫn đứng trước/cùng nhóm, không bị thay thế.
- Không match thì vẫn `null` + `missing_field:*`, không bịa số, không hạ ngưỡng confidence.

### Hạn chế / chưa làm được
- Không cover scan OCR `lang=en` (gated #85 / ops #69).
- Không phải BCTC HOSE thật — fixture synthetic (#70 mới mở golden “realish”).
- Không thêm thang `tỷ` / billion — chỉ nghìn/triệu như cũ.
- Nhãn lạ / layout 2 cột phức tạp vẫn có thể miss.

### Ghi chú một dòng
- Task kế có liên quan: #70 golden extract de-identified (sau khi #67 merge).

---

## Testing results — Task #67

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: fixture English map đủ `EXTRACT_FIELDS`; VI golden + unit nghìn/triệu không regress; eval 4 cases accuracy 1.0

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. pytest -q tests/benchmark/ -k extract` | extract + eval + OCR | **42 passed, 32 deselected** | ~60s; OCR tests included by `-k extract` |

Worktree: `.worktrees/t67`  
Venv: repo root `.venv`

### Failures
- None

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Full `pytest -q` CI | AC chỉ yêu cầu extract slice | CI trên PR |
| Real HOSE English PDF | cấm PII | #70 |
| OCR lang=en | out of scope | #85 / #69 |

### CI
- Push + PR sau commit (wave 1 authorized).

---

## Do not reopen

- Do not lower `DEFAULT_FIELD_CONFIDENCE_THRESHOLD` to inflate English coverage.
- Do not commit real company BCTC PDFs.
- Do not tick `docs/plan.md` / `.scratch/epic5-remain-plan.md` in this PR (wave conflict).
- Do not add billion/`tỷ` unit scale without a sourced convention.
- Do not change API/FE/OCR dependencies in a follow-up on this branch.
