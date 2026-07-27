# Handoff — Task #50 UniverseCoverageNote API + FE

**Status:** DONE (shipped — PR open)  
**Branch:** `cursor/epic3-phase2-task50-universe-coverage-note`  
**Date:** 2026-07-28  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** `d11d701` / https://github.com/thanhhale288/data-economy/pull/35  
**Base:** `origin/main` @ `fa3b083` (PR #34 Task #47 merged)

---

## Delivered

- **API:** `GET /api/universe/coverage` → `UniverseCoverageNote` (contract #39 / ADR-0003)
- **Service:** `universe_service.get_coverage_note(db)` — deep sample = `companies` count; universe = stub `rows.json` (stays `[]`)
- **FE:** `api.getUniverseCoverage`; `SampleHonestyBanner` accepts `coverageNote`; Dashboard + CompanyDetail wire note (fallback static copy nếu API fail)
- **Honesty:** empty stub → `claim=prototype_listed_sample`, `coverage_label=prototype_estimate`, `universe_row_count=0` — không treat ~28 như Section C
- **Tests:** `tests/universe/test_universe_api.py` + e2e FE contract snippets
- **Docs:** `docs/plan.md` #50 `[x]`; `.scratch/epic3-phase2-plan.md` #50 ✓

### Not done (out of scope)

- Commit/push/PR — done (`d11d701` / PR #35)
- #41 / #48 / #49 / #19b (tạm dừng)
- Invent universe rows / crawl toàn quốc / Alembic `company_universe`
- Dashboard redesign

---

## Task review — #50 UniverseCoverageNote API + FE

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task50-universe-coverage-note` · `d11d701` · [#35](https://github.com/thanhhale288/data-economy/pull/35)

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| API trả `UniverseCoverageNote` đúng contract #39 | done | `GET /api/universe/coverage` |
| FE hiển thị nhãn coverage / honesty | done | SampleHonestyBanner + Dashboard/CompanyDetail |
| Stub rỗng → note hợp lệ, không crash / over-claim | done | `prototype_listed_sample`, universe=0 |
| Tests + plan #50 `[x]` + handoff | done | this file |
| Không invent universe / không copy seed | done | `rows.json` vẫn `[]` |

Deliverable chính:
- Coverage honesty surface from ADR-0003 contract without inventing national firm universe

### Làm thế nào
- Waves: W1 explore (2 subagents) → W2 API+FE → W3 pytest + FE build → W4 handoff (no commit)
- Subagents: [Explore universe BE contract](6bde0215-d8a8-48c8-9e32-a3e6f65ec05d), [Explore FE honesty + API](fa849aa2-3b5c-40a2-8d3f-9f4db418143e)
- File chính: `backend/app/api/universe.py`, `universe_service.get_coverage_note`, `SampleHonestyBanner.jsx`, `api.js`, Dashboard/CompanyDetail, tests
- Trade-off: dedicated `/universe/coverage` thay vì nhét vào `DashboardSummary` — giữ tier separation ADR-0003
- So với plan: đúng #50 only; không mở paused tasks

### Còn lại / rủi ro
- Phase 2 **không còn open runnable task** — wave tiếp theo = **phase-close audit** (không tự mở #41/#48/#49/#19b)
- Optional later: #48 khi có nguồn DN Section C → có thể đổi claim sang `universe_shallow_only` khi stub có rows

---

## Testing results — Task #50

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: API+FE surface coverage note trên stub rỗng; contract FE khớp; không invent universe

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=<worktree> pytest -q tests/universe/ tests/e2e/test_api_fe_contract.py` | universe stub+API + FE contract | **11 passed** | includes 2 new API tests |
| 2 | `cd frontend && npm run build` | FE compile | **PASS** | vite build OK |
| 3 | `python3 -c … rows.json` | stub empty | **`[]`** | không invent |

### Failures
_(none)_

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | — | done (`d11d701` / PR #35) |
| Live browser smoke | Không bắt buộc AC | Optional demo |
| Full `pytest tests/` | Scope #50 đủ | CI on PR |

### CI
- PR: https://github.com/thanhhale288/data-economy/pull/35 — checks pending after push

---

## Do not reopen

- Không invent / copy seed vào `data/raw/company_universe/`
- Không treat `companies` count như coverage toàn Section C
- Không mở #41 / #48 / #49 / #19b trong chat này hoặc phase-close trừ khi user reopen tường minh

---

## Next

**Epic 3 Phase 2 — phase-close audit** (mọi open runnable task `#42`–`#47` + `#50` đã DONE; còn lại chỉ tạm dừng có chủ đích).

Base: merge #50 vào `main` (sau commit/PR) hoặc tip `cursor/epic3-phase2-task50-universe-coverage-note`.

---

## Paste prompt (chat mới = Phase 2 close audit only)

```markdown
# Task
Chạy **Epic 3 Phase 2 — phase-close audit** (không mở task roadmap mới; không làm #41/#48/#49/#19b trừ khi user Explicit reopen).

Một chat = **phase-close only**. STOP sau audit + handoff phase.

Lazy-to-complete: Explore → Audit → Verify docs → Ship (commit/PR/milestone chỉ khi user Explicit).

## Plan alignment
Đọc `docs/plan.md` § Epic 3 Phase 2:
- Open runnable wave đã DONE: `#42` `#43` `#45` `#46` `#47` `#50`
- Tạm dừng (không mở): `#41` `#48` `#49` `#19b`
- «Chưa làm được…»: industry-ratio wire (ex-#44), crawl GRDP tỉnh (parked)

## Context
Repo: `/Users/hale/Code/AI in Data Economy` (worktree tip có #50 nếu đã merge/commit)

Đọc bắt buộc:
- `.scratch/handoff-task50.md`
- `.scratch/epic3-phase2-plan.md` + Definition of Done Phase 2
- `docs/plan.md` § Epic 3 Phase 2 (checklist + quyết định 2026-07-27)
- ADR-0002, ADR-0003
- Handoffs gần: #42 #43 #45 #46 #47 #50 (smoke đọc Delivered)

## Git / branch
1. Base: `main` đã merge #50 (hoặc tip Task #50 nếu PR chưa merge)
2. Branch gợi ý (docs-only): `cursor/epic3-phase2-close-audit` — hoặc làm trên main chỉ khi user bảo
3. Không commit trừ khi user yêu cầu

## Requirements
- Đối chiếu Definition of Done Phase 2 vs thực tế shipped
- Ghi rõ: gì DONE / gì deferred / gì tạm dừng / gì «chưa làm được»
- Handoff phase: `.scratch/handoff-epic3-phase2.md` (hoặc path chuẩn repo)
- Cập nhật plan/STATUS nếu thiếu sync
- Prompt phase sau (Epic 3 Phase 3 hoặc milestone) — **có Waves**

## Non-goals
- Implement #41/#48/#49/#19b; invent universe/GRDP/GMV; redesign FE
- Mở task kỹ thuật mới ngoài audit

## Acceptance criteria
- Biên bản close Phase 2 trung thực (không over-claim national coverage)
- Handoff phase + Testing/audit checklist + next-phase prompt
- Không reopen paused tasks

## Waves / Subagents
- **W1 Explore (parallel, read-only):** (a) plan DoD vs handoffs #32–#50 (b) gaps deferred/paused vs code reality
- **W2 Audit write:** handoff phase + plan sync trên branch close-audit
- **W3 Verify:** checklist DoD từng mục; không invent evidence
- **W4 Ship:** review → testing/audit results → next-phase prompt → STOP (commit/PR/milestone chỉ khi Explicit)

## Deliverable
`.scratch/handoff-epic3-phase2.md`, plan sync nếu cần, phase review + audit results, paste prompt phase sau (có Waves).
```
