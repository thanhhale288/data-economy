# Handoff — Task #69 OCR ops note (lazy-load vs Docker bake)

**Status:** DONE  
**Branch:** `cursor/epic5-phase1-task69-ocr-ops-note`  
**PR:** https://github.com/thanhhale288/data-economy/pull/63  
**Commit:** `c85e4d8`  
**Date:** 2026-08-19  
**Phase:** Epic 5 / Phase 5.1 / Task #69  
**Base:** `origin/main` @ `3772afe`

---

## Đã làm được gì

- Ghi rõ quyết định ops: **mặc định lazy-load PaddleOCR**; **không** bake `requirements-ocr.txt` vào Docker image.
- `docs/ops-demo.md` — mục **PaddleOCR extra (Epic 5 Task #69)**: cài extra (kèm paddle index URL), env `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK`, lần đầu chậm + `~/.paddlex` không commit, thiếu extra → `ocr_unavailable` / banner FE #66, workaround CafeF hoặc PDF chữ, pytest `-m "not ocr"` / `importorskip`.

Không sửa extract formulas, không cài PaddleOCR, không đụng `backend/Dockerfile`, không commit model.

---

## Hạn chế

- Docker image **không** bake OCR (đúng card; user không yêu cầu bake trong chat này). Scan PDF trên máy/container chưa extra vẫn form trống + banner #66.
- Không chạy `pip install -r requirements-ocr.txt` trong task này — lần init engine / download `~/.paddlex` chưa được đo trên máy này.
- Không tick `docs/plan.md` / checklist Epic 5.

---

## Testing results

Docs review only (card: không bắt buộc pytest; không cài paddle).

- `docs/ops-demo.md` có mục PaddleOCR sau LightGBM train (#71); Dockerfile vẫn chỉ `pip install -r requirements.txt`.
- `requirements-ocr.txt` vẫn optional; `bctc_extract_ocr.py` vẫn lazy `_ocr_engine()` + `paddleocr_available()`.
- FE copy `ocr_unavailable` không đổi (Task #66).

Không chạy `PYTHONPATH=. pytest` / không chạy paddle smoke.

---

## Do not reopen

Ops note + quyết định lazy-load đã ghi. Không bake Dockerfile, không cài paddle, không commit `~/.paddlex`, không đổi mapper BCTC trong task này.
