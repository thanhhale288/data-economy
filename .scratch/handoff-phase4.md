# Handoff — Manufacturing Data Economy (Phase 4)

**Next session focus:** Phase 4 — Web hoàn thiện & Demo. **Start with Task #14 — Company detail (Module 2)**. Do not reopen Task #13 unless fixing a proven bug. Do not start Benchmark (#18) yet.

**Date:** 2026-07-20  
**Repo:** `/Users/hale/Code/AI in Data Economy`  
**Remote:** `https://github.com/thanhhale288/data-economy`  
**Phase 3 PR:** https://github.com/thanhhale288/data-economy/pull/5 (`cursor/phase3-clean-features-ml`, tip `9aed9c0`) — still OPEN at Task #13 start  
**Task #13 branch:** `cursor/phase4-task13-dashboard` · PR https://github.com/thanhhale288/data-economy/pull/6 (base Phase 3)

---

## Where things stand

### Done
- **Phase 1 + 2** on `main` (PR #1, PR #2).
- **Phase 3** (#10–#12) on PR #5 — cleaning parquet, features, real ML + `/api/ml/*`.
- **Task #13 Dashboard ngành** — IIP + forecast overlay, Digital VA summary, VSIC heatmap, OECD peer vs GSO with honest missing state; `tests/dashboard`.

### Phase 4 remaining
1. **#14 Company detail** — RAL case study + 10 firms digital/financial view. *Blocked by:* Phase 2 metrics (done).
2. **#15 Pipeline monitor** — job status, cleaning quality summary; staging DB optional.
3. **#16 ML Lab** — compare 3 models, forecast vs actual, feature importance from #12 artifacts.
4. **#17 E2E integration** — after modules land.

Suggested next branch: `cursor/phase4-task14-company-detail` (from Task #13 tip after merge, or Phase 3 tip if #13 PR not merged yet).

### Do not rewrite
- Cleaning, feature engineering, ML train math — unless proven bug.
- Digital VA formula; no fake MEI_BCI; tickers **BMP** not BWE.
- Leave `.scratch/_local_backup/` untracked.

### Local caveats
- `mei_ip` / OECD peer may be missing — UI shows N/A / empty banner (Task #13).
- Prefer existing design language in `frontend/` (dashboard product UI).

---

## Read first (Task #14)

| Doc | Why |
|-----|-----|
| `AGENTS.md` / `CONTEXT.md` | Tickers, Digital VA, RAL case |
| `docs/plan.md` | § Tiến độ + Giai đoạn 4 |
| `.scratch/handoff-task13.md` | What #13 delivered |
| `frontend/src/pages/Companies.jsx`, `CompanyDetail.jsx` | Current FE |
| `backend/app/api/companies.py` | Company API |

---

## Constraints / do not

- Do not invent GSO/OECD/CafeF/marketplace numbers.
- Do not change Digital VA / VDEI without CONTEXT + ADR.
- No commit/push unless user asks (or lazy-to-complete finish of the task).

---

## Paste prompt for the new chat

See end of Task #13 chat response (ready-to-paste block for Task #14).
