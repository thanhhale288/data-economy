# Handoff — Task #92 Benchmark Wave B

**Status:** DONE (uncommitted — commit/PR khi user yêu cầu)  
**Date:** 2026-08-19  
**Branch:** `cursor/epic5-phase6-task92-benchmark-wave-b` (from `origin/main` @ `045c8f6`, Wave A #81 đã merge)  
**Playbook:** `.scratch/epic5-remain-plan.md` + `docs/guides/frontend-benchmark-roadmap.md` Wave B  
**Không tick:** `docs/plan.md` / checklist epic5

---

## Đã làm được gì

- Tách `frontend/src/pages/Benchmark.jsx` (~1470 dòng) thành `frontend/src/components/benchmark/*` theo bảng Wave B:
  - `benchmarkLabels.js` — METRIC / COMPARISON / WARNING / DIGITAL labels
  - `formUtils.js` — EMPTY_FORM, coerce payload, prefill/extract snapshot, feedback source
  - `resultsModel.js` — formatRatio, percentile strength, radar rows
  - `BenchmarkHeader.jsx` — title, breadcrumb, industry context (Wave A)
  - `BenchmarkForm.jsx` — fields, upload, nạp RAL/REE, confirm, submit
  - `BenchmarkWarnings.jsx` — `warnings[]` honesty banners
  - `BenchmarkResults.jsx` — cards, radar, quartile, digital, expenditure
- `pages/Benchmark.jsx` còn orchestration + API (extract → confirm → compare, feedback #64/#78).
- Không đổi API / `benchmark_service.py` math. Không invent GSO.

## Hallmark (không AI slop)

- Giữ theme **locked blue-report** (Be Vietnam Pro + JetBrains Mono) — không catalog mới, không purple gradient.
- Đưa inline style tĩnh sang class token (`metric-card-*`, `warning-code`, `visually-hidden`, radar `var(--accent)`).
- Width % của quartile / percentile **còn inline** vì phụ thuộc số thật.
- Copy honesty Wave A giữ nguyên (peer niêm yết mẫu, N/A khi thiếu).

## Hạn chế / chưa làm được

- Không làm Wave C (polish toàn trang / đổi nav).
- Không chunk-split Recharts (warning bundle > 500 kB còn).
- Chưa commit / PR.

## Testing results

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: split không đổi coerce/honesty; Vite build OK.

### Lệnh đã chạy
| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `cd frontend && node --test src/benchmarkIndustryContext.test.js src/benchmarkWaveB.test.js src/extractWarningCopy.test.js` | FE unit | **19 passed** | Wave A + Wave B + extract copy |
| 2 | `cd frontend && npm run build` | Vite | **pass** | chunk-size warning sẵn có |

### Skipped
| Kiểm tra | Lý do |
|----------|-------|
| Prefill RAL → compare UI | Cần API + DB local |
| Demo VSIC 1100 | Cần API + DB local |
| `PYTHONPATH=. pytest -q tests/benchmark/` | Task FE-only, không đụng backend |
