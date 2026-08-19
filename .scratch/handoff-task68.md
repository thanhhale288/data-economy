# Handoff — Task #68 DocAI extract smoke

**Status:** DONE  
**Branch:** `cursor/epic5-phase1-task68-docai-extract-smoke`  
**Date:** 2026-08-19  
**Phase:** Epic 5 Phase 1 (DocAI harden)  
**Base:** `origin/main` @ `f17bf4c`

---

## Done

- Repeatable smoke module `tests/benchmark/test_docai_extract_smoke.py`:
  - Text PDF fixture `sample_bctc_text.pdf` → `POST /api/benchmark/extract` (FastAPI TestClient) with fields populated and `source_type=pdf_text`.
  - Scan PNG/PDF honesty: `ocr_unavailable` + empty fields when PaddleOCR is missing; does not require the OCR extra.
  - Optional `@pytest.mark.ocr` extra (importorskip) when PaddleOCR is installed.
  - Confirms confirm-before-compare is a **FE gate** (`requireConfirm` / checkbox / `#benchmark-upload-input` / submit «So sánh benchmark») by reading existing `Benchmark.jsx` — file not edited (Task #81).
- Ops commands in `docs/ops-demo.md` (text-PDF pass, scan skip/honesty, FE checkbox before Compare).
- Playwright **not** added. Default CI remains `pytest -q` with no marker filter; existing `tests/e2e/` API TestClient tests still run. No `addopts = -m "not e2e"`.

## Limits

- Did not edit `frontend/src/pages/Benchmark.jsx`.
- Did not change extract mapper / `bctc_extract.py` math / Digital VA / VDEI.
- Did not invent GSO/OECD/CafeF/compare numbers; smoke does not require compare/peers.
- Did not tick `docs/plan.md` or `.scratch/epic5-remain-plan.md`.
- No Playwright browser tests (`DOC_AI_E2E` unused). Manual UI checklist only in ops-demo.
- Did not commit `.env`, secrets, model binaries, or raw company PDFs.

## Testing results

```bash
cd "/Users/hale/Code/AI in Data Economy/.worktrees/t68"
source "/Users/hale/Code/AI in Data Economy/.venv/bin/activate"
PYTHONPATH=. pytest -q tests/benchmark/test_docai_extract_smoke.py
# 5 passed, 2 warnings in 37.90s
# (local venv has PaddleOCR; ocr extra ran instead of skip)

PYTHONPATH=. pytest -q tests/benchmark/ -k extract
# 48 passed, 40 deselected, 2 warnings in 66.30s
```

Playwright: **not added** — no `DOC_AI_E2E=1` run. Default CI will not download browsers.

## Giải thích dễ hiểu

### Đã làm
- Một lệnh pytest chạy fixture PDF chữ qua API extract và kiểm tra form lock confirm trên FE (đọc file, không sửa UI).
- Bản scan không bịa số khi máy chưa có OCR.

### Hạn chế
- Chưa có e2e trình duyệt; so sánh benchmark vẫn cần DB peers nếu làm tay trên UI.
