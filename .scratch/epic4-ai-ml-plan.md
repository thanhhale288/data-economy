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
