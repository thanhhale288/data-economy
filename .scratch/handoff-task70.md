# Handoff — Task #70 Golden set extract (de-identified)

**Status:** DONE  
**Branch:** `cursor/epic5-phase1-task70-extract-golden-realish`  
**Date:** 2026-08-19  
**Base:** `origin/main` @ `5a30cce`  
**Không tick:** `docs/plan.md` / checklist epic5  
**Không đọc:** `docs/knowledge.md`

---

## Delivered

Thêm **5** case golden synthetic (de-identified), tổng **9** case (> 3). Không commit BCTC doanh nghiệp thật, không PII, không ticker seed (RAL/HPG/VNM/FPT). Không sửa mapper aliases, không hạ `DEFAULT_FIELD_CONFIDENCE_THRESHOLD`.

| id | Fixture | Ý nghĩa |
|----|---------|---------|
| `hose_like_trieu` | `hose_like_trieu.pdf` | Layout HOSE-like: issuer **Cong ty Co phan Mau Sang Che**, fake ticker MSC, `Don vi: Trieu dong`, mã số dòng + số năm nay |
| `en_sales_layout` | `en_sales_layout.pdf` | English aliases sẵn có (`Revenue from sales`, `Total equity`, …), đơn vị VND (không nhân triệu) |
| `partial_revenue_assets` | `partial_revenue_assets.pdf` | Chỉ doanh thu + tổng tài sản; LNTT / CSH / lao động = null + `missing_field` |
| `hose_notes_noise` | `hose_notes_noise.pdf` | Trang 1 đủ 5 field; trang thuyết minh có số (GVHB, doanh thu tài chính, tài sản ngắn hạn) — mapper không bịa EXTRACT_FIELDS |
| `hose_nghin_dong` | `hose_nghin_dong.pdf` | `Don vi: Nghin dong` (×1000); employees không scale |

Issuer giả: Mau Sang / Den / Xanh / Vang / Tim Che. Số làm tròn, ghi rõ **synthetic, not a filing** trên PDF.

Generator (không thêm reportlab): `tests/benchmark/write_synthetic_text_pdf.py` (Helvetica ASCII; label gõ không dấu vì Type1 không có glyph tiếng Việt — mapper `_fold` cùng cách). Fixture đã commit để eval chạy offline.

Golden cũ giữ nguyên: `text_full`, `text_partial`, `text_empty`, `text_full_en`.

---

## Eval JSON summary

`PYTHONPATH=. python3 scripts/eval_benchmark_extract.py`

```json
{
  "cases": 9,
  "fields": ["operating_revenue", "profit_before_tax", "employees", "total_assets", "total_equity"],
  "overall": {
    "correct": 45,
    "total": 45,
    "accuracy": 1.0,
    "expected_present": 33,
    "predicted_present": 33,
    "coverage_against_expected": 1.0,
    "coverage_all_slots": 0.7333333333333333
  }
}
```

Per-field (accuracy / coverage vs expected-present):

- `operating_revenue`: 1.0 / 1.0 (present 8/9)
- `profit_before_tax`: 1.0 / 1.0 (present 6/9)
- `employees`: 1.0 / 1.0 (present 6/9)
- `total_assets`: 1.0 / 1.0 (present 7/9)
- `total_equity`: 1.0 / 1.0 (present 6/9)

**Cách đọc accuracy 1.0:** `expected_fields` = output thật của extract trên layout synthetic này (kể cả null). Không phải “mọi BCTC HOSE thật sẽ đạt 1.0”. Coverage all-slots **0.73** vì partial/empty **cố ý** để slot trống — không bịa field.

Case warnings đáng chú ý:

- `hose_like_trieu`: `unit_detected_million_vnd`
- `hose_nghin_dong`: `unit_detected_thousand_vnd`
- `partial_revenue_assets`: `missing_field:profit_before_tax|employees|total_equity`
- `hose_notes_noise`: không warning — số trang notes không map vào EXTRACT_FIELDS (`current_assets` alias nuốt “Tai san ngan han” rồi bỏ vì field đó không nằm whitelist)

---

## Limitations

- PDF tự viết, ASCII-folded, một cột số (năm nay). **Không** phải filing HOSE/CafeF.
- Chưa cover bảng 2 cột năm nay/năm trước: mapper lấy amount **phải nhất** ≥ 100 — trên BCTC thật có thể lấy nhầm năm trước. Không tune alias để giả 1.0.
- Không thêm case scan/OCR; `text_empty` vẫn `pdf_ocr` + `ocr_unavailable` khi thiếu PaddleOCR.
- Helvetica không nhúng Unicode tiếng Việt có dấu.
- Không hạ threshold 0.75.

---

## Testing results

- Overall: **PASS**
- `PYTHONPATH=. python3 scripts/eval_benchmark_extract.py` → 9 cases, accuracy 1.0, coverage_against_expected 1.0, coverage_all_slots 0.733…
- `PYTHONPATH=. pytest -q tests/benchmark/ -k 'extract or golden'` → **39 passed, 4 skipped, 37 deselected**
