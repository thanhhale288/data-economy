# Handoff — Task #53 OCR path for scanned reports

**Status:** DONE (uncommitted — commit/PR khi user yêu cầu)  
**Branch:** `cursor/epic4-phase1-task53-bctc-ocr-path`  
**Date:** 2026-07-29  
**Phase:** Epic 4 Phase 4.1 (DocAI Benchmark P0)  
**Base:** tip `cursor/epic4-phase1-task52-bctc-extract-spike` @ `7f32c42` (#52 chưa merge `main`)  
**Commit / PR:** *(chưa — user chưa yêu cầu)*

---

## Delivered

- **Shared mapper:** `extract_fields_from_lines` in `backend/app/services/bctc_extract.py` (reuse label map + `parse_vn_number` + unit scale)
- **Router:** `extract_bctc` / `extract_bctc_dict` — detect image vs PDF text vs sparse → OCR
- **OCR module:** `backend/app/services/bctc_extract_ocr.py` (lazy PaddleOCR; pypdfium2 rasterize)
- **`source_type`:** `pdf_text` | `pdf_ocr` | `image_ocr`
- **Deps:** `requirements-ocr.txt` (`paddlepaddle==3.3.0`, `paddleocr==3.7.0`); note in `requirements.txt`
- **Fixtures (synthetic, no PII):** `sample_bctc_scan.png`, `sample_bctc_scan.pdf`, `empty_bctc_scan.png`
- **Tests:** `tests/benchmark/test_bctc_extract_ocr.py` + regression `test_bctc_extract.py`
- **Docs:** `docs/plan.md` #53 [x]; `.scratch/epic4-ai-ml-plan.md` #53 ticked

### Detect rules

| Input | Path | `source_type` |
|-------|------|---------------|
| `.png`/`.jpg`/… | PaddleOCR | `image_ocr` |
| PDF, `len(norm text) ≥ 50` | pdfplumber only | `pdf_text` |
| PDF, sparse/empty text | rasterize + OCR | `pdf_ocr` |
| `extract_bctc_pdf` (direct) | never OCR | always `pdf_text` |

### OCR install / smoke

```bash
pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
pip install paddleocr==3.7.0
# or: pip install -r requirements-ocr.txt  (paddle wheel may still need paddle.org.cn index)
PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True python -c "from paddleocr import PaddleOCR; print('ok')"
```

### Not done (out of scope)

- **#54** `POST /api/benchmark/extract`
- **#55** FE upload
- **#56** large golden eval
- Epic 3 paused (#19b, #41, #48, #49)

---

## Giải thích dễ hiểu

### Đã làm được gì
- Báo cáo scan/ảnh giờ cũng đọc được số giống PDF chữ (doanh thu, lãi trước thuế, lao động, tài sản, vốn CSH).
- PDF có chữ sẵn vẫn dùng đường cũ (pdfplumber) — không ép OCR.
- Thiếu chắc / OCR kém → để trống + cảnh báo, không bịa số.
- Cài OCR là optional (nặng); CI có thể bỏ qua test OCR.

### Hạn chế / chưa làm được
- Chưa có API upload / form Benchmark (#54–#55).
- Model OCR tải lần đầu vào `~/.paddlex` (không commit).
- Layout BCTC phức tạp / chữ mờ vẫn có thể sai — cần confirm người dùng ở task sau.
- Branch #53 đang stack trên #52 (PR #39 chưa merge `main`).

### Ghi chú một dòng
- Task kế trên roadmap: #54 — API extract endpoint.

---

## Testing results — Task #53

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: text-PDF #52 không regress; OCR image/PDF scan map đúng golden synthetic; `source_type` phân biệt rõ

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `pytest --noconftest tests/benchmark/test_bctc_extract.py` | #52 regression | **10 passed** | trước implement |
| 2 | `python -c "from paddleocr import PaddleOCR; …"` | smoke | **ok** | need `all` FS for `~/.paddlex` |
| 3 | `pytest --noconftest tests/benchmark/test_bctc_extract.py tests/benchmark/test_bctc_extract_ocr.py` | text+OCR | **17 passed** | ~35s (model warm) |

### Failures
- None

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| OCR tests without paddleocr | `importorskip` / `-m "not ocr"` | CI default OK |
| API/FE | #54–#55 | yes |
| Real HOSE scan PII | cấm commit | #56 golden |

### CI
- Chưa push/PR (user chưa yêu cầu commit)

---

## Handoff cleanup
- Đã xóa: `.scratch/handoff-task52.md`
- Giữ: `.scratch/handoff-task53.md` (file này)
