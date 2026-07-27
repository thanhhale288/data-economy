# Handoff — Task #51 FE Epic 3 honesty surface (P0)

**Status:** DONE (PR open)  
**Branch:** `cursor/epic3-phase2-task51-fe-honesty`  
**Date:** 2026-07-27  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** `290e611` · PR https://github.com/thanhhale288/data-economy/pull/28  
**Base:** `origin/main` @ `12281cf` (design-system PR #27 merged)

---

## Delivered

- **Dashboard + Company detail:** `SampleHonestyBanner` — Digital VA / số hóa = mẫu ~28, không phải toàn Section C (ADR-0003); badge trên KPI Digital VA / DN mẫu; tip tách ≠ VA_C GSO
- **Benchmark:** render **mọi** `result.warnings` với `WARNING_LABELS` VI (`prototype_listed_sample`, `small_peer_sample`, `insufficient_peers`)
- **Listing chart:** bỏ `revenue_est || 0`; null không vào chart; table vẫn `—`
- **Marketplace:** chú thích ADR-0002 — `live` có thể = cache allowlist
- **BCTC:** `pickPreferredFinancial` ưu tiên CafeF; seed/fallback không gợi CafeF; `source_url` http(s) clickable
- **P1 gọn:** industry-ratio chưa áp (Company detail); Pipeline note CafeF trong `source_health`
- **Docs:** `docs/plan.md` Task #51 [x] + mục Design system backlog

### Not done (out of scope)

- Tasks #40–#50, #45 full VA_C chart
- Redesign KPI/radar/format tiền
- BE `live:cache` subtype (#42)

---

## Task review — #51 FE Epic 3 honesty surface (P0)

### Tiến độ
- Ước lượng hoàn thành AC: **100%** P0 (+ P1 nhẹ)
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task51-fe-honesty` · `290e611` · PR #28

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Banner/badge honesty Dashboard + Company detail | done | `SampleHonestyBanner` + KPI badges |
| Benchmark mọi warnings VI | done | `WARNING_LABELS` + banner list |
| Listing null ≠ 0 / `—` | done | filter null khỏi chart; table unchanged |
| Marketplace live-cache note + BCTC CafeF/seed honesty | done | copy ADR-0002; prefer CafeF; clickable http |
| plan.md #51 [x] + handoff | done | + Design system section |
| Một PR / không ngoài phạm vi | done | FE + plan/handoff only |

Deliverable chính:
- FE honesty surface trên design-system đã merge — không invent số, không đổi công thức

### Làm thế nào
- Waves: W1 explore (subagent) → W2 FE implement → W3 pytest+build → W4 ship
- Subagents: [W1 Explore FE honesty](49f3a574-790e-4ad8-827d-4ca5d53ae260)
- File chính: `frontend/src/SampleHonestyBanner.jsx`, `pages/Dashboard.jsx`, `CompanyDetail.jsx`, `Benchmark.jsx`, `Pipeline.jsx`, `docs/plan.md`
- Trade-off: shared banner component thay vì copy-paste string; chart bỏ hàng null thay vì plot null (Recharts-friendly)
- So với plan: đúng #51 P0; P1 industry-ratio + Pipeline CafeF note khi còn dung lượng

### Còn lại / rủi ro (không làm trong chat này)
- **Task #40** — 9 ticker website domain fail
- **Task #45** — KPI/chart `VA_C` đầy đủ
- **#42** — phân biệt live HTTP vs cache trên API

---

## Testing results — Task #51

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: FE-only; BE warnings/schema sẵn; build xanh; benchmark tests không regress

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. pytest -q tests/benchmark/ tests/universe/` | BE related | **28 passed**, 65 warnings | deprecation only |
| 2 | `cd frontend && npm run build` | FE | **PASS** | vite 5.4.21 |
| 3 | Manual grep `revenue_est \|\| 0` | CompanyDetail | none | coerce removed |

### Failures
- None

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Manual UI với API live (RAL) | Không có server chạy trong chat | Smoke sau merge |
| Full `pytest -q` | FE-only; scoped enough | Optional CI |

---

## Do not reopen
- Không làm #40/#45 trong chat #51 trừ user phá lệ
- Không invent GSO/OECD/CafeF/GMV
- Không redesign KPI/radar

## Next
**Task #40 — Sửa domain website seed** (mặc định) **hoặc Task #45 — Dashboard VA_C** (nếu ưu tiên FE tiếp).

Base: merge PR Task #51 → `main`, rồi branch task mới.

---

## Paste prompt (chat sau)

```markdown
# Task
Hoàn thành **Task #40 — Sửa domain website seed (nợ từ audit #33)** trên `main` đã có Task #51 honesty FE. Một chat = một task. Branch: `cursor/epic3-phase2-task40-website-domains`.

Đang chạy skill lazy-to-complete-workflow — Task #40 only.

## Context
- Audit: `.scratch/epic3-task33-website-url-audit.md` — 9 ticker `website_ok=false`: IDI, SBT (DNS), NKG (timeout), POM, TLH, GEE, DPR, CSV (SSL), DCM (reset).
- Seed: `data/seeds/companies.json` (+ digital presence). Không suy checkout khi chưa fetch được.
- Handoff trước: `.scratch/handoff-task51.md`. ADR-0003 / honesty FE đã ship (#51).

## Requirements
- Tìm domain/URL đúng cho 9 ticker (bằng chứng fetch/DNS/HTTP status).
- Cập nhật seed + presence flags chỉ khi có bằng chứng; không bịa checkout.
- Ghi audit/diff note ngắn trong `.scratch/` nếu cần.
- Cập nhật `docs/plan.md` Task #40 → [x]; handoff `.scratch/handoff-task40.md`.

## Constraints
- Base: `origin/main` (sau merge #51 nếu chưa). Không commit trên `main`.
- Không invent URL; không bật discovery; không đổi Digital VA.
- Không làm #41–#50 / #45 trong chat này.

## Non-goals
- GMV backfill (#41), cookie smoke (#42), VA_C UI (#45), redesign FE.

## Acceptance criteria
- [ ] 9 ticker có URL/domain cập nhật **hoặc** biên bản giữ fail + lý do có chứng cứ
- [ ] Seed/presence consistent; không suy checkout khi chưa verify
- [ ] plan #40 [x]; handoff; 1 PR

## Verification
- `PYTHONPATH=. pytest -q` (seed/companies liên quan)
- Smoke HTTP/DNS cho URL mới (ghi kết quả trong Testing results)

## Waves / Subagents
- **W1 Explore** (`explore`): map audit #33 + seed entries cho 9 ticker + chỗ đọc website_url trên FE/BE.
- **W2 Implement:** sửa seed/presence theo bằng chứng; ghi note.
- **W3 Verify:** pytest + smoke URL; Testing results.
- **W4 Ship:** commit + push + PR; handoff + Task review + Testing results; prompt chat sau → **STOP**.

## Deliverable
PR URL, plan/handoff, Task review + Testing results, prompt chat tiếp theo (có Waves). Không mở task khác cùng chat.
```

*(Nếu user muốn FE tiếp thay vì #40, thay Task #45 — Dashboard/API M1 hiện `VA_C`.)*
