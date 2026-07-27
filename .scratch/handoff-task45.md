# Handoff — Task #45 Dashboard/API M1 hiện VA (nợ từ #38)

**Status:** DONE (shipped — PR open)  
**Branch:** `cursor/epic3-phase2-task45-dashboard-va`  
**Date:** 2026-07-27  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** `f94aecc` / https://github.com/thanhhale288/data-economy/pull/31  
**Base:** `origin/main` @ `e699d9b` (PR #29 #40 + gate quyết định 2026-07-27 + #51)

---

## Delivered

- **API:** `GET /api/dashboard/va?indicator_code=VA_C|VA_C_NOMINAL` — timeseries `{period, value, source, unit, indicator_code}`; empty khi thiếu; reject unknown codes → `[]` (không invent)
- **Summary:** `DashboardSummary` thêm `va_c_*` + optional `va_c_nominal_*` (latest, MoM/YoY, period, unit, source) — null khi absent
- **FE:** metric-strip VA (không phá 4-up KPI grid) + chart VA_C / VA_C_NOMINAL; copy tách Digital VA mẫu; empty banner honest
- **format:** `formatMacroVa` — tỷ VND (values đã billion trong `gso_macro`)
- **Docs:** `docs/plan.md` #45 `[x]`; knowledge note; phase2 plan thứ tự
- **Tests:** dashboard VA fixtures + e2e `api.js` contract `/dashboard/va` + `getVa`

### Not done (out of scope)

- Task #46 cleaning/features VA
- #41 / #43 / #47 / #50
- Commit/push/PR (user chưa Explicit yêu cầu)
- Redesign KPI strip / đổi Digital VA formula

---

## Task review — #45 Dashboard/API M1 hiện VA

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task45-dashboard-va` · `f94aecc` · [#31](https://github.com/thanhhale288/data-economy/pull/31)

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Dashboard + API hiện `VA_C` với nhãn đúng | done | strip + chart + `/dashboard/va` + summary fields |
| Copy tách Digital VA DN | done | tip/badge `≠ Digital VA mẫu`; heatmap title «trong mẫu»; Digital VA label «(mẫu DN)» |
| Không invent khi thiếu | done | null/empty; unknown indicator → `[]`; tests |
| Optional nominal | done | `VA_C_NOMINAL` on summary + dashed chart line |
| Tests/build pass | done | 11 pytest + `npm run build` |
| plan #45 `[x]` + handoff | done | this file |

Deliverable chính:
- Surface layer trên data #38 (`gso_macro`) — không crawl mới, không đổi formula Digital VA

### Làm thế nào
- Waves: W1 explore BE/FE parallel → W2 service/schema/API + FE strip/chart → W3 pytest + FE build → W4 handoff (no commit)
- Subagents: [Explore BE dashboard VA](6b5bfcbf-c2d8-4fd6-9a47-ad3b88a75f37), [Explore FE Dashboard gaps](b4fc3211-dc5b-4c6b-a44b-969642bdf83f)
- File chính: `backend/app/services/dashboard_service.py`, `backend/app/api/dashboard.py`, `backend/app/schemas/__init__.py`, `frontend/src/pages/Dashboard.jsx`, `frontend/src/api.js`, `frontend/src/format.js`, `tests/dashboard/*`
- Trade-off: VA KPI nằm **metric-strip** (không thêm cột 5 vào `.cards-kpi`) để giữ design system 4-up
- So với plan: đúng #45; không đụng #46 pipeline

### Còn lại / rủi ro
- Demo cần seed/crawl đã có `VA_C` trong DB — offline seed không invent VA
- MoM trên chuỗi step-hold quý→tháng thường ~0 trong quý (honest, không nội suy)
- Next open wave: `#46` `#43` `#47` `#50` (#41/#48/#49/#19b vẫn tạm dừng)

---

## Testing results — Task #45

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: API/Dashboard surface `VA_C` honest; FE build OK; không invent từ IIP/Digital VA

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. python -m pytest -q tests/dashboard/ tests/e2e/test_api_fe_contract.py` | dashboard + FE contract | **11 passed** | +4 VA tests; `getVa` in contract |
| 2 | `cd frontend && npm run build` | Vite production build | **PASS** | Dashboard.jsx compiles |

### Failures
- Không

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | Shipped `f94aecc` / PR #31 | — |
| Live DB smoke với seed VA | Unit fixtures đủ AC | Ops bootstrap khi demo |
| Pipeline cleaned VA | #46 | Có |

---

## Do not reopen
- Không làm #46 / #43 / #47 / #50 trong chat #45
- Không invent VA từ IIP hoặc Σ Digital VA
- Không đổi Digital VA formulas / redesign KPI strip lớn

## Next
Gợi ý **Task #46 — Pipeline cleaning/features VA** (wire `VA_C` vào cleaned/features; không đổi forecast target im lặng).

---

## Paste prompt (chat sau)

```markdown
# Task
Hoàn thành **Task #46 — Pipeline cleaning/features VA (nợ từ #38)** — đưa `VA_C` (+ optional nominal) vào cleaned/features + step-hold/provenance; **không** thay target forecast im lặng.

Một chat = **#46 only**. STOP sau #46.

Lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user Explicit yêu cầu).

## Plan alignment
Đọc `docs/plan.md` § Epic 3 Phase 2 — **Quyết định người dùng (2026-07-27)** + **Phase 2 — còn mở**:
- #45 DONE (Dashboard/API M1 surface `VA_C`)
- #41 / #48 / #49 / #19b = tạm dừng — **không** mở
- Wave còn mở: `#43` `#46` `#47` `#50` — chat này chỉ **#46**

## Context
Repo: `/Users/hale/Code/AI in Data Economy` (worktree tip có #45 nếu đã merge/commit)

Đọc bắt buộc:
- `.scratch/handoff-task45.md`, `.scratch/handoff-task38.md`
- `pipeline/cleaning/` (hiện filter IIP_C) + `pipeline/features/`
- `gso_macro` `VA_C` / `VA_C_NOMINAL` từ #38
- Forecast target contract — **không** đổi target im lặng; provenance rõ

## Git / branch
1. Base: `main` đã merge #45 (hoặc tip `cursor/epic3-phase2-task45-dashboard-va` nếu PR chưa merge)
2. Branch: `cursor/epic3-phase2-task46-pipeline-va`
3. Không commit trừ khi user yêu cầu

## Requirements
- Wire `VA_C` vào cleaning output + feature store (đọc từ `gso_macro`, giữ source/unit)
- Step-hold / provenance honest (không invent dynamics)
- Không thay IIP (hoặc target hiện tại) làm forecast target im lặng — ghi rõ nếu chỉ thêm feature phụ

## Non-goals
- #43 discovery, #47 GRDP biên bản, #50 UniverseCoverageNote, #41/#48/#49
- Đổi Digital VA formula; redesign Dashboard (#45 đã xong)

## Acceptance criteria
- Cleaned/features có `VA_C` (và optional nominal) với provenance
- Tests pass; không invent; forecast target không đổi im lặng
- `docs/plan.md` #46 `[x]` + handoff + review + testing + next prompt

## Waves / Subagents
- **W1 Explore (parallel, read-only):** (a) cleaning run path + IIP-only filters (b) features / ML input schema + forecast target
- **W2 Implement:** chỉ Task #46 trên `cursor/epic3-phase2-task46-pipeline-va`
- **W3 Verify:** pytest cleaning/features (+ regression forecast target); ghi Testing results
- **W4 Ship:** handoff → task review → testing → next prompt → STOP (commit/PR chỉ khi user Explicit)

## Deliverable
Handoff `.scratch/handoff-task46.md`, plan sync, Task review + Testing results, paste prompt task kế (có Waves).
```
