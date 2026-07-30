# Handoff — Task #56 Eval + honesty guardrails for DocAI extract

**Status:** DONE (uncommitted — commit/PR khi user yêu cầu)  
**Branch:** `cursor/epic4-phase1-task56-docai-eval-guardrails`  
**Date:** 2026-07-30  
**Phase:** Epic 4 Phase 4.1 (DocAI Benchmark)  
**Base:** `origin/main` tip `080cf12` (đã gồm #54/#55 theo remote snapshot)  
**Commit / PR:** *(chưa — user chưa yêu cầu)*

---

## Delivered

- Added confidence guardrail in `backend/app/services/bctc_extract.py`:
  - `DEFAULT_FIELD_CONFIDENCE_THRESHOLD = 0.75`
  - `confidence < threshold` => field forced `null`
  - warning emitted: `low_confidence_field:<field>:<conf><threshold`
- Added lightweight eval service `backend/app/services/bctc_extract_eval.py`:
  - load golden cases from JSON
  - compute overall + per-field `accuracy` and `coverage`
  - include per-case breakdown (`source_type`, warnings, slot counts)
- Added golden set file: `tests/benchmark/golden/extract_golden_cases.json`
  - 3 synthetic cases: full text / partial text / empty text
  - target fields: `operating_revenue`, `profit_before_tax`, `employees`, `total_assets`, `total_equity`
- Added tests `tests/benchmark/test_bctc_extract_eval.py`:
  - baseline metrics from golden set
  - guardrail test proving low-confidence field is nulled
- Added eval runner script: `scripts/eval_benchmark_extract.py`

---

## Baseline eval report (Task #56)

From `PYTHONPATH=. python3 scripts/eval_benchmark_extract.py`:

- Cases: `3`
- Slots: `15` (`3 cases x 5 fields`)
- Overall accuracy: `1.0` (`15/15` slots match golden)
- Coverage vs expected-present values: `1.0` (`6/6`)
- Coverage across all slots: `0.4` (`6/15`)
- Per-field accuracy: all `1.0`
- Per-field coverage (vs expected-present): all `1.0`

Interpretation:
- Current extractor matches the small golden set exactly.
- Coverage all slots is intentionally <1 because partial/empty docs should keep missing values as `null` (honesty-first behavior, no invention).

---

## Verify results

### Commands run

1) `PYTHONPATH=. pytest -q tests/benchmark/ -k "extract or eval"`  
Result: **17 passed, 4 skipped, 21 deselected**

2) `PYTHONPATH=. python3 scripts/eval_benchmark_extract.py`  
Result: **PASS**, JSON baseline printed.

### Environment note

- Needed to install missing dependency `pdfplumber` locally to run extraction tests.
- Install command executed: `python3 -m pip install pdfplumber` (outside sandbox due FS permissions).

---

## Scope boundaries respected

- No FE/UI flow rewrite (#55 untouched).
- No API contract change for #54 (response shape unchanged).
- No work for #57+.
