# Handoff — Task #66 FE extract warning honesty

**Status:** DONE  
**Branch:** `cursor/epic5-phase1-task66-docai-extract-honesty-ux`  
**Date:** 2026-08-19  
**Phase:** Epic 5 / Phase 5.1 / Task #66  
**Base:** `origin/main` @ `58d2bc2`  
**Commit:** (filled after git commit)  
**PR:** (filled after `gh pr create`)  

---

## Delivered

| Piece | Path |
|-------|------|
| Mapper | `frontend/src/extractWarningCopy.js` — token → câu tiếng Việt |
| Unit test | `frontend/src/extractWarningCopy.test.js` (`node --test`) |
| Banner | `frontend/src/pages/Benchmark.jsx` — list copy, vẫn `banner banner-warn` |
| CSS | `frontend/src/index.css` — `.extract-warning-list` dùng `--space-*` sẵn có |

Không sửa `bctc_extract.py` / OCR / extract math. Không cài PaddleOCR. Không tick `docs/plan.md`.

---

## Giải thích dễ hiểu

### Đã làm
- Upload BCTC xong, banner cảnh báo không còn hiện mã kỹ thuật kiểu `ocr_unavailable, pages_capped:15`.
- Mỗi token thành một câu tiếng Việt: thiếu OCR thì bảo dùng CafeF hoặc PDF chữ; cap trang thì nói chỉ đọc N trang đầu.
- Token lạ vẫn hiện: câu chung + mã gốc (không nuốt im lặng).
- Confirm trước khi compare giữ nguyên; field null vẫn null (không điền 0).

### Hạn chế
- Chỉ đổi copy FE. Scan PDF vẫn form trống nếu server chưa OCR (#69 ops / #85 gated).
- `missing_field:*` liệt kê từng field thiếu — file scan có thể dài; vẫn trung thực.
- Label GitHub `epic:5` / `phase:1` chưa có trên repo nên PR không gắn label đó.

---

## Testing results

```bash
cd frontend && node --test src/extractWarningCopy.test.js
# 6 passed, 0 failed

cd frontend && npm run build
# vite build OK
```

Không chạy RTL e2e (card không bắt buộc). Confirm-before-compare không đổi code path.

---

## Mapper copy (ví dụ)

| Token | Câu VI |
|-------|--------|
| `ocr_unavailable` | Máy chủ chưa có OCR. Dùng nạp CafeF (prefill) hoặc PDF chữ chọn được (selectable text) — bản scan sẽ để form trống. |
| `pages_capped:15` | Chỉ đọc 15 trang đầu của file; các trang sau không được trích. |

---

## Do not reopen

- Không cài PaddleOCR / không bake Docker OCR (#69).
- Không đổi mapper BCTC / alias English (#67).
- Không smoke/e2e Playwright (#68).
- Không tick checklist Epic 5 / `docs/plan.md` trong PR này.
