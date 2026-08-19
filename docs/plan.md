# Kế hoạch dự án: Kinh tế số ngành Chế biến, Chế tạo

**Hot plan** (agent đọc file này). Bản đầy đủ lịch sử: [`docs/plan-archive.md`](plan-archive.md).  
Domain ngắn: `CONTEXT.md` · ADR: `docs/adr/` · Epic 4 chi tiết: [`.scratch/epic4-ai-ml-plan.md`](../.scratch/epic4-ai-ml-plan.md) · **Epic 5 task cards:** [`.scratch/epic5-remain-plan.md`](../.scratch/epic5-remain-plan.md).

---

## Tiến độ (cập nhật 2026-08-19)

| Giai đoạn / Epic | Trạng thái | Ghi chú |
| ---------------- | ---------- | ------- |
| Phase 1–5 học kỳ | DONE (trừ #19b) | Checklist đầy đủ → archive §6 |
| Epic 2 Product-first | DONE | #20–#24 |
| Epic 3 Data-first Phase 1–2 | DONE | #25–#51 (trừ paused/deferred) |
| Epic 4 AI/ML/DL | DONE (ship) | #52–#64 + PR #57 cap 15 trang; gap → Epic 5 |
| **Epic 5 Productize gaps** | **Plan (#65)** | Task #66–#81 runnable; #82–#94 gated |

**Handoff / playbook agent:** [`.scratch/epic5-remain-plan.md`](../.scratch/epic5-remain-plan.md)  
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

## Epic 4 — AI / ML / DL (đã ship)

Chi tiết lịch sử: [`.scratch/epic4-ai-ml-plan.md`](../.scratch/epic4-ai-ml-plan.md). Gap còn lại **không** làm trên epic4 — chuyển Epic 5.

| Phase | Mục tiêu | Status |
|-------|----------|--------|
| **4.0 Plan** | Inventory + roadmap P0–P3 | DONE |
| **4.1 DocAI Benchmark** | Upload → extract → confirm | DONE #52–#56 + PR #57 (15 trang) |
| **4.2 Forecast & anomaly** | Isolation Forest + LightGBM code + ML Lab | DONE #57–#58 (LightGBM chưa train — #71) |
| **4.3 Marketplace NLP** | Categorizer offline + matcher v2 | DONE #59–#60 |
| **4.4 Assist UX** | Narrative Benchmark + Forecast | DONE #61–#62 |
| **4.5 Monitoring** | Contract + JSONL feedback | DONE #63–#64 (chưa retrain — #79) |

## Epic 5 — Productize remaining gaps (ưu tiên hiện tại)

Playbook từng task (đã có gì / làm gì / prompt agent): [`.scratch/epic5-remain-plan.md`](../.scratch/epic5-remain-plan.md).

**Cách chạy:** chat mới → dán **Prompt agent** của đúng 1 task → branch `cursor/epic5-phaseP-taskT-slug` từ `main`. Một chat = một task = một PR. Gated #82–#94 chỉ khi user gọi đúng số.

| Phase | Task | Status |
|-------|------|--------|
| 5.0 Plan | #65 | DONE (file epic5) |
| 5.1 DocAI harden | #66–#70 | Chưa |
| 5.2 Forecast / anomaly | #71–#73 | Chưa |
| 5.3 Marketplace NLP | #74–#76 | Chưa |
| 5.4 Narrative / feedback | #77–#79 | Chưa |
| 5.5 FE leftover | #80–#81 | Chưa |
| 5.6 Gated | #82–#94 | Đóng băng |

Gợi ý bắt đầu: **#66** FE honesty OCR. Epic 3 paused/deferred **giữ nguyên**.

---

## Design system FE

**Đã merge:** PR #27 — palette, sidebar, mobile, Benchmark UX.  
**FE Hallmark pass:** đã merge `main`. Handoff: `.scratch/handoff-epic4-fe-hallmark-pass.md`. Không đổi math/API DocAI. Wave A Benchmark = Epic 5 **#81**.

**Không làm lại:** layout/nav IA, format tiền, KPI strip + MetricInfoTip, radar/quartile (honesty badge = #51).

| Ưu tiên | Việc | Status |
|--------|------|--------|
| P0–P1 honesty Epic 3 | Banner mẫu ~28, warnings, null≠0, CafeF links… | DONE #51 |
| P1 | Chip URL fail / empty shop discovery | Epic 5 **#80** |
| P1 | FE Hallmark full pass (anti-slop) | DONE (`main`) |
| P2 | Xu hướng Benchmark theo năm; «Ngành nổi bật» IIP | Blocked data |

---

## Agent rules (plan)

1. Cập nhật **file này** khi đóng/mở task — không phình lại architecture §1–4 (đó là archive).
2. Domain/công thức: `CONTEXT.md` + ADR — không mở `docs/knowledge.md`.
3. Một chat = một task; handoff mới ghi `.scratch/handoff-task<N>.md`; handoff cũ → `.scratch/archive/handoffs/` khi prune.
