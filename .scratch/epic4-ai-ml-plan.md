# Epic 4 — AI / ML / DL pivot plan

**Branch:** `epic4-plan`  
**Status:** planning (docs only — chưa implement)  
**Date:** 2026-07-29  
**Base:** `origin/main`

## 1. Motivation

Epics 1–3 đã dựng nền **data + forecast v1** (crawl → clean → features → ARIMA/XGBoost/LSTM → API/FE). Trọng tâm sản phẩm tiếp theo chuyển sang **ứng dụng ML/DL/AI** trên data đã có, thay vì tiếp tục mở rộng thu thập vô hạn.

Epic 3 backlog còn lại (tạm dừng / deferred) **không bị xóa** — chỉ hạ ưu tiên khi xung đột với Epic 4.

## 2. Vị trí trên ML pipeline (8 stage)

Tham chiếu pipeline chuẩn: Business → Collect → Prepare → Features → Train → Evaluate → Deploy → Monitor.

| Stage | Trạng thái project | Ghi chú |
|-------|--------------------|---------|
| 01 Business Understanding | **Done** | VSIC Section C, IIP/VA/Digital VA, Benchmark BITE |
| 02 Data Collection | **Done (nền)** | GSO/OECD/CafeF/marketplace; Epic 3 còn paused/deferred |
| 03 Data Preparation | **Done** | Cleaning parquet + provenance |
| 04 Feature Engineering | **Done v1** | `features.parquet`; VA_C đã vào features (#46) |
| 05 Model Training | **Done v1** | ARIMA, XGBoost, LSTM; shop matcher fuzzy |
| 06 Model Evaluation | **Done v1** | MAE/RMSE/MAPE, walk-forward, ML Lab |
| 07 Deployment | **Partial** | `/api/ml/*` + ML Lab nội bộ; chưa MLOps production |
| 08 Monitoring & Feedback | **Partial** | Pipeline monitor có; drift / auto-retrain / feedback loop chưa |

**Kết luận:** đang ở **cuối stage 6 → đầu stage 7**. Epic 4 = productize AI (DocAI, anomaly, assist) + siết stage 7–8.

## 3. Inventory — đã có / chưa có

### Đã có

- `ml/models/{arima,xgboost,lstm}_model.py` + `trainer.py`
- `ml/evaluation/{metrics,walk_forward}.py`
- `ml/shop_matcher/matcher.py` (RapidFuzz, threshold 0.65)
- Backend `/api/ml/*`, FE `MLLab.jsx`, Dashboard forecast overlay
- Benchmark Module 5: form thủ công + prefill CafeF HTML (`GET /api/benchmark/prefill/{ticker}`)

### Chưa có (gap Epic 4)

- Upload PDF/ảnh BCTC, OCR, table extract
- LLM/rules mapping dòng BCTC → `BenchmarkInput`
- Anomaly detection (Isolation Forest / LSTM AE)
- Product categorizer (tên SP → VSIC)
- Shop matcher TF-IDF/classifier đầy đủ
- LightGBM train path (deps only)
- Narrative LLM (benchmark / forecast)
- Model drift monitoring + feedback từ user edits

## 4. Ý tưởng AI (ưu tiên)

### P0 — Document AI cho Benchmark (ý tưởng user)

**Pain:** nhập tay DT/LN/NV/BS/chi phí; prefill chỉ DN đã có BCTC trong DB.

**Flow:**

1. User upload PDF/ảnh BCTC trên Benchmark FE
2. `POST /api/benchmark/extract` (multipart)
3. Pipeline 2 tầng:
   - Digital PDF → `pdfplumber` / camelot (đã ghi `docs/needGit.md`)
   - Scan/ảnh → PaddleOCR (VN)
4. Mapping rules (+ LLM-assist) → `BenchmarkInput` + confidence/field
5. FE prefill form; **user confirm/edit** → `POST /compare` như hiện tại

**Guardrails:** không auto-submit; thiếu chắc → `null` + lý do; không bịa số.

### P1 — ML đã hứa proposal nhưng chưa ship

| Capability | Module | Ghi chú |
|------------|--------|---------|
| Anomaly / trend detector | Dashboard / ML Lab | Isolation Forest hoặc LSTM AE trên IIP (+ optional ratios) |
| Product categorizer | Marketplace | Tên SP → VSIC 4-digit |
| Shop matcher v2 | Entity resolution | Fuzzy + TF-IDF/embedding hybrid |
| LightGBM (+ so sánh XGB) | ML Lab | Dep có sẵn, chưa train path |
| Forecast feature hygiene | Forecast | Giữ IIP target; VA_C đã wire — không đổi target im lặng |

### P2 — AI trợ lý domain (demo cao)

| Idea | Mô tả |
|------|--------|
| Benchmark narrative (LLM) | Giải thích percentile/ROA/ROE tiếng Việt từ `BenchmarkResult` only |
| Forecast narrative | Tóm tắt horizon + feature importance XGB |
| Peer similarity | Embedding financial + digital ngoài VSIC 2-digit |
| Website digital-signal classifier | Brochure vs commerce-ready từ HTML crawl |
| BCTC consistency check | OCR/CafeF vs lịch sử cùng ticker; flag lệch |

### P3 — Sau / nghiên cứu

- RAG trên docs GSO/OECD + knowledge nội bộ
- Energy intensity (chỉ khi có nguồn số thật)
- GRU / multimodal AR; auto-retrain policy đầy đủ

## 5. Phases Epic 4 (map 8-stage pipeline)

| Phase | Stages | Mục tiêu | Acceptance |
|-------|--------|----------|------------|
| **4.0 Plan** (PR này) | 01 | Roadmap + inventory | Docs merge `main` |
| **4.1 DocAI Benchmark** | 02–07 | Upload → extract → confirm → compare | Field accuracy trên golden set; không auto-finalize |
| **4.2 Forecast & anomaly** | 04–08 | Anomaly Lab panel; LightGBM optional; drift hooks | Metrics + honesty khi thiếu series |
| **4.3 Marketplace NLP** | 04–06 | Product categorizer + matcher v2 | Labeled sample nhỏ; precision gate |
| **4.4 Assist UX** | 07–08 | Narrative LLM Benchmark + Forecast | Chỉ cite số từ API; feedback edits lưu signal |

Task numbering sẽ gắn `cursor/epic4-phaseP-taskT-slug` khi mở implement (không mở task code trong PR plan này).

## 6. Architecture sketch — P0 DocAI

```text
Benchmark FE (upload)
    → POST /api/benchmark/extract
        → detect PDF text vs image
        → pdfplumber|camelot  OR  PaddleOCR
        → field mapper (rules + optional LLM)
        → { fields, confidence, warnings }
    → user edits form
    → POST /api/benchmark/compare  (existing)
```

Tech refs: `docs/needGit.md` (camelot, PaddleOCR, pdfplumber).

## 7. Rủi ro

| Risk | Mitigation |
|------|------------|
| PDF HOSE / layout phức tạp | Ưu tiên CafeF/HTML + digital PDF trước; scan phase sau |
| OCR sai số | Confidence + human confirm; golden-set eval |
| LLM bịa field | Chỉ map từ text đã extract; schema whitelist |
| Chi phí / deps nặng OCR | Optional extra; demo path text-PDF trước |
| PII trong upload | Không log raw file production; retention ngắn |

## 8. Ngoài phạm vi Epic 4.0 (PR này)

- Không implement OCR/API/FE
- Không đổi Digital VA / VDEI formulas
- Không reopen Epic 3 paused tasks (#41, #48, #49, #19b) trừ khi user yêu cầu
- Không commit model binaries / secrets

## 9. Next after merge

1. Mở milestone **Epic 4** trên GitHub (optional)
2. Chat mới: Task #52 (hoặc số tiếp theo) — spike DocAI text-PDF → `BenchmarkInput`
3. Branch: `cursor/epic4-phase1-task52-bctc-extract-spike`

## 10. Task breakdown (để theo dõi)

Quy ước branch mỗi task: `cursor/epic4-phaseP-taskT-slug`

**Trước mỗi task (bắt buộc):** đọc mục *Pre-flight* của task → kiểm tra import / `pip show` → cài thiếu theo `docs/needGit.md` → ghi deps mới vào `requirements.txt` (hoặc extra optional) nếu chưa có → rồi mới code. Không cài darts/scrapy/wbgapi trừ khi task ghi rõ.

### Phase 4.1 — DocAI Benchmark (P0)

- [x] **Task #52 — Extract spike (text PDF first)** ✅ DONE  
  **Delivered:** `backend/app/services/bctc_extract.py` (pdfplumber rules-first; `source_type=pdf_text`; null+warnings khi thiếu; map `total_equity`). Fixtures `tests/benchmark/fixtures/*.pdf` + `tests/benchmark/test_bctc_extract.py`. **Không** camelot / PaddleOCR / API / FE.  
  **Pre-flight (repo/lib):**
  1. `python -c "import pdfplumber; print(pdfplumber.__version__)"` — phải OK (`pdfplumber` đã trong `requirements.txt`).
  2. Nếu bảng PDF sample fail với pdfplumber: cân nhắc cài **camelot** (`pip install camelot-py[cv]`) hoặc **tabula-py** — ghi optional; chỉ khi fixture cần.
  3. Không cài PaddleOCR ở task này.
  **Output:** service đọc PDF text + map field cơ bản (`operating_revenue`, `profit_before_tax`, `employees`, `total_assets`, `equity`) + test fixture nhỏ.

- [x] **Task #53 — OCR path for scanned reports** ✅ DONE  
  **Delivered:** OCR fallback via optional PaddleOCR (`requirements-ocr.txt`); router `extract_bctc` (`pdf_text` | `pdf_ocr` | `image_ocr`); shared `extract_fields_from_lines`; fixtures `sample_bctc_scan.png/.pdf`, `empty_bctc_scan.png`; tests `test_bctc_extract_ocr.py` (`pytest.mark.ocr` + importorskip). **Không** API/FE.  
  **Pre-flight (repo/lib):**
  1. Xác nhận Task #52 path text-PDF vẫn chạy.
  2. Cài **PaddleOCR** (VN): theo `docs/needGit.md` #16 — ưu tiên extra/optional deps (nặng); `pip install paddlepaddle paddleocr` (hoặc pin version đã chọn trong task notes).
  3. Smoke: `python -c "from paddleocr import PaddleOCR; print('ok')"`.
  4. Giữ camelot/pdfplumber cho digital PDF; OCR chỉ fallback scan/ảnh.
  **Output:** fallback OCR cho file scan/image, normalize số (dấu phẩy/chấm, đơn vị nghìn/triệu).

- [ ] **Task #54 — API extract endpoint + response contract**  
  **Pre-flight (repo/lib):**
  1. Không cần lib mới — tái dùng extract service từ #52/#53.
  2. Kiểm tra FastAPI multipart đã có (`python-multipart` nếu thiếu khi upload file).
  3. Xác nhận deps DocAI đã pin trong `requirements.txt` / optional extras trước khi merge API.
  **Output:** `POST /api/benchmark/extract` trả `{fields, confidence, warnings, source_type}`; không ghi DB.

- [ ] **Task #55 — FE prefill + human confirm UX**  
  **Pre-flight (repo/lib):**
  1. Không cài repo needGit mới — chỉ FE (`frontend/`) + contract #54.
  2. Smoke API extract local trước khi gắn upload UI.
  **Output:** Benchmark upload file, prefill form, highlight confidence thấp, user edit trước `POST /compare`.

- [ ] **Task #56 — Eval + honesty guardrails**  
  **Pre-flight (repo/lib):**
  1. Có thể cài **great-expectations** (`pip install great-expectations`) nếu muốn schema validate extract output — optional; pytest + golden set đủ cho MVP.
  2. Không bắt buộc Prefect/darts.
  **Output:** golden set metrics (field accuracy), rule `confidence<threshold => null`, warning rõ ràng.

### Phase 4.2 — Forecast & anomaly

- [ ] **Task #57 — Anomaly detector v1**  
  **Pre-flight (repo/lib):**
  1. `sklearn` + `torch` đã trong `requirements.txt` — Isolation Forest / LSTM AE không cần lib mới.
  2. `python -c "import sklearn, torch; print('ok')"`.
  3. Không cài darts trừ khi quyết định đổi API so sánh model (mặc định: không).
  **Output:** pipeline + API kết quả anomaly (IIP/VA), baseline threshold, test không invent alert.

- [ ] **Task #58 — ML Lab anomaly panel + model compare refresh**  
  **Pre-flight (repo/lib):**
  1. Wire **LightGBM** đã có deps: `python -c "import lightgbm; print(lightgbm.__version__)"`.
  2. Nếu chưa có train path: implement trên `lightgbm` hiện có — không thêm darts (Task 16 đã bỏ).
  3. FE: không cần package needGit mới.
  **Output:** hiển thị anomaly timeline + compare ARIMA/XGB/LSTM/(LightGBM nếu có).

### Phase 4.3 — Marketplace NLP

- [ ] **Task #59 — Product categorizer seed model**  
  **Pre-flight (repo/lib):**
  1. Baseline: `scikit-learn` (TF-IDF + classifier) — đã có.
  2. Nếu dùng embedding: cài **sentence-transformers** (`pip install sentence-transformers`) — needGit #10; pin version vào `requirements.txt`.
  3. Smoke: `python -c "from sentence_transformers import SentenceTransformer"` (chỉ khi chọn path embedding).
  **Output:** classifier tên sản phẩm -> VSIC 4-digit với labeled sample nhỏ + precision report.

- [ ] **Task #60 — Shop matcher v2 (fuzzy + vector/rerank)**  
  **Pre-flight (repo/lib):**
  1. Giữ **RapidFuzz** (`rapidfuzz` đã có).
  2. Bắt buộc có **sentence-transformers** (hoặc tái dùng model #59) cho hybrid fuzzy + vector.
  3. `python -c "from rapidfuzz import fuzz; from sentence_transformers import SentenceTransformer; print('ok')"`.
  4. Không thay bằng Scrapy / Playwright ở task này (matcher only).
  **Output:** cải thiện precision/recall so với matcher hiện tại, thêm QA gate report.

### Phase 4.4 — Assist UX

- [ ] **Task #61 — Benchmark narrative assistant**  
  **Pre-flight (repo/lib):**
  1. Không bắt buộc repo needGit — LLM qua API (env key) hoặc template rules-first.
  2. Optional: agency-agents ML persona chọn lọc nếu muốn hỗ trợ agent chat — không cài full roster (`docs/needGit.md` #7).
  3. Guardrail: chỉ cite số từ `BenchmarkResult` API.
  **Output:** giải thích percentile/ROA/ROE bằng tiếng Việt từ API numbers only.

- [ ] **Task #62 — Forecast narrative assistant**  
  **Pre-flight (repo/lib):**
  1. Như #61 — không cần sentence-transformers/OCR mới.
  2. Xác nhận artifact feature importance XGB (và LGBM nếu #58 đã ship) đọc được từ disk/API.
  **Output:** tóm tắt dự báo, sai số và driver chính (feature importance), không bịa nguyên nhân.

### Phase 4.5 — Monitoring & feedback loop

- [ ] **Task #63 — ML monitoring contract**  
  **Pre-flight (repo/lib):**
  1. Optional: **great-expectations** cho validate IIP/schema trước/sau train — needGit #13.
  2. Mặc định: schema + counters bằng SQLAlchemy/API hiện có; chỉ cài GE nếu contract cần expectation suites.
  3. **Prefect** chưa bắt buộc — giữ `schedule` trừ khi job monitor phức tạp hơn nightly.
  **Output:** schema theo dõi model quality/drift + dashboard counters.

- [ ] **Task #64 — Feedback-to-training loop**  
  **Pre-flight (repo/lib):**
  1. Nếu orchestration vượt `schedule` (OCR batch + retrain + ingest feedback): cân nhắc **Prefect** (`pip install prefect`) — needGit #12.
  2. Không cài scrapy/wbgapi/graphify cho task này.
  3. Xác nhận không lưu raw PDF/secret trong training signal.
  **Output:** lưu chỉnh sửa user sau prefill thành training signal (an toàn, không chứa secret docs).
