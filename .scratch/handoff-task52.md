# Handoff — Task #52 BCTC extract spike (text PDF)

**Status:** DONE (uncommitted — commit/PR khi user yêu cầu)  
**Branch:** `cursor/epic4-phase1-task52-bctc-extract-spike`  
**Date:** 2026-07-29  
**Phase:** Epic 4 Phase 4.1 (DocAI Benchmark P0)  
**Base:** `origin/main` @ `63a85fa` (Epic 4 plan PR #38 merged)  
**Commit / PR:** chưa — user chưa Explicit yêu cầu commit

---

## Delivered

- **Service:** `backend/app/services/bctc_extract.py`
  - Input: path / bytes / file-like digital-text PDF
  - Engine: **pdfplumber** only (camelot **không** cần cho fixture spike)
  - Map → `operating_revenue`, `profit_before_tax`, `employees`, `total_assets`, `total_equity`
  - Output: `{fields, confidence, warnings, source_type: "pdf_text"}`
  - Thiếu / ambiguous → `null` + warning — không bịa
  - Unit detect: nghìn / triệu VND khi có marker; default full VND (CafeF prefill parity)
- **Fixtures (synthetic, no PII):** `tests/benchmark/fixtures/sample_bctc_text.pdf`, `empty_bctc.pdf`, `partial_bctc.pdf`
- **Tests:** `tests/benchmark/test_bctc_extract.py`
- **Docs:** `docs/plan.md` Phase 4.1 #52 [x]; `.scratch/epic4-ai-ml-plan.md` #52 ticked

### Not done (out of scope — next tasks)

- **#53** PaddleOCR scan/ảnh
- **#54** `POST /api/benchmark/extract`
- **#55** FE upload
- **#56** large golden eval
- Epic 3 paused (#19b, #41, #48, #49)

### Field map (rules-first)

| BenchmarkInput | Label aliases (folded VI) | Notes |
|----------------|---------------------------|-------|
| `operating_revenue` | doanh thu thuan / ban hang / hoat dong | Full VND |
| `profit_before_tax` | loi nhuan truoc thue | Full VND |
| `employees` | so lao dong / nhan vien | int headcount; no ×unit |
| `total_assets` | tong tai san | after current_assets aliases |
| `total_equity` | von chu so huu | plan “equity” → schema name |

Reuse context: CafeF HTML aliases in `crawlers/financial/cafef.py` (×1000); prefill `benchmark_service.load_input_from_company`.

### Limits (layouts chưa hỗ trợ)

- Scan/image PDF (cần OCR #53)
- Multi-column HOSE layouts / nested tables → may need camelot later
- Conflicting duplicate labels → null + `ambiguous_field:*`
- Fixture labels ASCII-folded; real Unicode PDFs OK via diacritic fold
- Local `.env` with unknown keys (`shopee_session_cookie`…) breaks Settings import — filter or `extra='ignore'` (pre-existing; not fixed in #52)

---

## Task review — #52 Extract spike (text PDF first)

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 4.1 · `cursor/epic4-phase1-task52-bctc-extract-spike` · working tree · chưa PR

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Pre-flight pdfplumber OK; no PaddleOCR | done | 0.11.4 trong `.venv` |
| Map ≥ revenue, PBT, employees, assets, equity | done | `total_equity` đúng schema |
| fields + confidence/warnings + `source_type=pdf_text` | done | `BctcExtractResult` |
| Thiếu chắc → null + warning | done | empty + partial fixtures |
| Fixture + tests xanh | done | 10 dedicated + suite filter |
| Không API/FE/OCR trong diff | done | service + tests + docs only |
| plan + handoff + STOP | done | |

Deliverable chính:
- Rules-first pdfplumber extract service sẵn cho #54 API wrap

### Làm thế nào
- Waves: W0 deps → W1 explore (schema/CafeF + pdfplumber sample) → W2 implement → W3 pytest → W4 handoff
- Subagents: [Explore BenchmarkInput fields](8871efb5-2520-47f0-bb2e-3229658b8ec2)
- File chính: `backend/app/services/bctc_extract.py`, `tests/benchmark/test_bctc_extract.py`, fixtures PDF
- Trade-off: không camelot (line+table text đủ synthetic); không LLM mapper; ASCII fixtures + Unicode fold
- So với plan: đúng #52 P0 spike

### Còn lại / rủi ro (không làm trong chat này)
- OCR path + số normalize (#53)
- Multipart API (#54) + FE (#55)
- Real HOSE PDF layouts / camelot nếu table extract fail
- Settings `.env` extra keys (local pytest friction)

---

## Testing results — Task #52

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: text-PDF spike xanh; sẵn tái dùng cho OCR fallback + API

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `.venv/bin/python -c "import pdfplumber; print(...)"` | deps | **0.11.4** | OK |
| 2 | `pytest --noconftest tests/benchmark/test_bctc_extract.py` | extract unit | **10 passed** | tránh Settings/.env |
| 3 | `pytest tests/benchmark/ tests/financial/ -k "extract or pdf or bctc_extract"` | related | **12 passed**, 37 deselected | cần filter `.env` session_cookie keys |

### Failures
- None (sau workaround `.env` extra keys)

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| camelot on real HOSE PDF | không cần fixture | optional nếu #53/#56 |
| PaddleOCR | #53 | yes |
| API/FE | #54–#55 | yes |

### CI
- Chưa push/PR

---

## Handoff cleanup
- Đã xóa: `.scratch/handoff-task51.md`
- Giữ: `.scratch/handoff-task52.md` (file này)

---

## Paste prompt — Task #53

```markdown
# Task
Tiếp **Epic 4 Phase 4.1 — DocAI Benchmark**. Chat này chỉ làm **Task #53 — OCR path for scanned reports**.

STOP sau #53. Không làm #54–#64, không reopen Epic 3 paused (#19b, #41, #48, #49).

Lazy-to-complete: Pre-flight → Explore → Implement → Verify → Ship (commit/PR chỉ khi user Explicit yêu cầu).

## Context
Repo: `/Users/hale/Code/AI in Data Economy`

Đọc bắt buộc:
- `docs/plan.md` § Epic 4 Phase 4.1
- `.scratch/epic4-ai-ml-plan.md` § Task #53 + architecture P0 + risks
- `docs/needGit.md` → deferred #16 PaddleOCR (chi tiết `docs/needGit/deferred.md` / full-archive nếu cần)
- `backend/app/services/bctc_extract.py` — **tái dùng** mapper/parse số/`BctcExtractResult`; đừng duplicate
- `tests/benchmark/test_bctc_extract.py` + fixtures text-PDF — regression phải xanh
- Handoff: `.scratch/handoff-task52.md`

**#52 đã có:** digital text PDF → fields + confidence + warnings + `source_type=pdf_text`.  
**#53 chỉ:** fallback OCR cho scan/ảnh → cùng contract; `source_type` kiểu `pdf_ocr` / `image_ocr`; normalize số VN.

Branch: `cursor/epic4-phase1-task53-bctc-ocr-path`  
Base: `main` (sau merge #52) hoặc tip branch #52 nếu chưa merge.

## Pre-flight
1. Xác nhận #52 path: `PYTHONPATH=. pytest -q tests/benchmark/test_bctc_extract.py` (work around `.env` extra keys nếu cần).
2. Cài PaddleOCR (VN) theo needGit — **optional extra** ưu tiên (nặng); pin version; ghi `requirements.txt` hoặc `requirements-ocr.txt` / extras.
3. Smoke: `python -c "from paddleocr import PaddleOCR; print('ok')"`.
4. Không đụng API multipart (#54) / FE (#55). Không cài darts/scrapy/wbgapi.

## Requirements
1. Detect text PDF vs scan/image (ít text extractable → OCR).
2. OCR → text lines → **reuse** label map + `parse_vn_number` từ `bctc_extract` (hoặc shared helper).
3. Normalize dấu phẩy/chấm, đơn vị nghìn/triệu (cùng convention #52).
4. Output cùng shape: `{fields, confidence, warnings, source_type}` — thiếu chắc → null.
5. Fixture scan/synthetic image hoặc PDF raster nhỏ (no PII) + tests OCR path + regression text path.
6. Tick #53 trong plan / epic4 plan; handoff `.scratch/handoff-task53.md`.

## Constraints
- Một chat = #53 only.
- Giữ pdfplumber path cho digital PDF; OCR chỉ fallback.
- Không đổi Digital VA / VDEI / percentile math.
- Không commit model binaries nặng nếu có thể download-on-first-use; không commit BCTC PII.
- LLM mapping không bắt buộc.

## Non-goals
- `POST /extract`, FE upload, golden eval lớn (#54–#56)
- Anomaly / marketplace NLP / narrative LLM

## Waves / Subagents

```
W0 Pre-flight PaddleOCR install + pin
W1 Explore: bctc_extract seams + OCR API surface (parallel OK)
W2 Implement detect → OCR → reuse mapper + fixtures
W3 Verify pytest (text regression + OCR path)
W4 Ship handoff + prompt #54
```

### Acceptance criteria
- [ ] PaddleOCR smoke OK; deps documented
- [ ] Scan/image → fields subset BenchmarkInput; null khi thiếu
- [ ] Text-PDF path #52 không regress
- [ ] `source_type` phân biệt OCR vs pdf_text
- [ ] Không API/FE trong diff
- [ ] plan + handoff #53; STOP

## Deliverable cuối
# Task #53 report — branch, deps, module changes, test results, paste prompt #54
```
