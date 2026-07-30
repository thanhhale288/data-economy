# Kế hoạch dự án: Kinh tế số ngành Chế biến, Chế tạo

**Hot plan** (agent đọc file này). Bản đầy đủ lịch sử: [`docs/plan-archive.md`](plan-archive.md).  
Domain ngắn: `CONTEXT.md` · ADR: `docs/adr/` · Epic 4 chi tiết: [`.scratch/epic4-ai-ml-plan.md`](../.scratch/epic4-ai-ml-plan.md).

---

## Tiến độ (cập nhật 2026-07-29)

| Giai đoạn / Epic | Trạng thái | Ghi chú |
| ---------------- | ---------- | ------- |
| Phase 1–5 học kỳ | DONE (trừ #19b) | Checklist đầy đủ → archive §6 |
| Epic 2 Product-first | DONE | #20–#24 |
| Epic 3 Data-first Phase 1–2 | DONE | #25–#51 (trừ paused/deferred) |
| **Epic 4 AI/ML/DL** | **In progress** | Phase 4.1 DocAI — Tasks #53/#54/#55/#56 DONE |

**Handoff hiện tại:** `.scratch/handoff-task55.md`  
**Không đọc:** `docs/knowledge.md` (human glossary; `.cursorignore`).

---

## Modules (shipped)

| Module | Status |
|--------|--------|
| 1 Dashboard | IIP + forecast + VA_C + honesty banner (#51) |
| 2 Company detail | Profile, kênh số, peers, narrative |
| 3 Pipeline monitor | Jobs + source_health |
| 4 ML Lab | ARIMA / XGB / LSTM compare |
| 5 Benchmark | BITE-style; warnings VI (#51) |

---

## Epic 3 — còn mở / deferred

| Việc | Trạng thái | Unblock |
|------|------------|---------|
| #19b Proposal Mục 4 | Paused | Khi viết proposal |
| #41 Enricher BCTC mở rộng | Paused | Sau DocAI Epic 4 nếu cần |
| #48 / #49 | Paused | Xem archive / phase2 plan |
| Crawl GRDP tỉnh×ngành | Deferred NO-GO | Table ID NSO; **cấm** copy `VA_C` quốc gia → tỉnh |
| IIP theo ngành VSIC | Chưa | Có chuỗi IIP ngành |
| Benchmark xu hướng theo năm | Chưa | ≥2 kỳ BCTC đủ field |

---

## Epic 4 — AI / ML / DL (ưu tiên hiện tại)

Chi tiết task: [`.scratch/epic4-ai-ml-plan.md`](../.scratch/epic4-ai-ml-plan.md).

| Phase | Mục tiêu | Status |
|-------|----------|--------|
| **4.0 Plan** | Inventory + roadmap P0–P3 | DONE (PR #38) |
| **4.1 DocAI Benchmark** | Upload BCTC → OCR/table → prefill (user confirm) | **#53/#54/#55/#56 DONE** |
| **4.2 Forecast & anomaly** | Anomaly Lab; LightGBM optional; drift | Chưa |
| **4.3 Marketplace NLP** | Categorizer + shop matcher v2 | Chưa |
| **4.4 Assist UX** | Narrative LLM Benchmark + Forecast | Chưa |

**P0 ý tưởng:** OCR/PDF BCTC → suggest fill Benchmark; AI không auto-submit percentile.

### Phase 4.1 checklist (hot)

- [x] **#52** Extract spike (text PDF / pdfplumber) → `backend/app/services/bctc_extract.py`
- [x] **#53** OCR path (PaddleOCR) — scan/ảnh → `bctc_extract_ocr.py` + router `extract_bctc`
- [x] **#54** `POST /api/benchmark/extract`
- [x] **#55** FE upload + confirm
- [x] **#56** Eval golden + honesty guards

Epic 3 paused/deferred **giữ nguyên** — hạ ưu tiên khi xung đột Epic 4.

---

## Design system FE

**Đã merge:** PR #27 — palette, sidebar, mobile, Benchmark UX.

**Không làm lại:** layout/nav, format tiền, KPI strip + MetricInfoTip, radar/quartile (honesty badge = #51).

| Ưu tiên | Việc | Status |
|--------|------|--------|
| P0–P1 honesty Epic 3 | Banner mẫu ~28, warnings, null≠0, CafeF links… | DONE #51 |
| P1 | Chip URL fail / empty shop discovery | Backlog |
| P2 | Xu hướng Benchmark theo năm; «Ngành nổi bật» IIP | Blocked data |

---

## Agent rules (plan)

1. Cập nhật **file này** khi đóng/mở task — không phình lại architecture §1–4 (đó là archive).
2. Domain/công thức: `CONTEXT.md` + ADR — không mở `docs/knowledge.md`.
3. Một chat = một task; handoff mới ghi `.scratch/handoff-task<N>.md`; handoff cũ → `.scratch/archive/handoffs/` khi prune.
