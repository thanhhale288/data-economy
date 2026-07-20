# Handoff — Manufacturing Data Economy (Phase 4)

**Next session focus:** Phase 4 — Web hoàn thiện & Demo. **Start with Task #16 — ML Lab (Module 4)**. Do not reopen Task #13–#15 unless fixing a proven bug. Do not start Benchmark (#18) yet.

**Date:** 2026-07-20  
**Repo:** `/Users/hale/Code/AI in Data Economy`  
**Remote:** `https://github.com/thanhhale288/data-economy`  
**Phase 3 PR:** https://github.com/thanhhale288/data-economy/pull/5 (`cursor/phase3-clean-features-ml`, tip `9aed9c0`) — still OPEN at Task #15 close  
**Task #13:** `cursor/phase4-task13-dashboard` · PR https://github.com/thanhhale288/data-economy/pull/6  
**Task #14:** `cursor/phase4-task14-company-detail` · PR https://github.com/thanhhale288/data-economy/pull/7  
**Task #15:** `cursor/phase4-task15-pipeline-monitor` · (PR after ship; base tip Task #14 `56f0b9a`)

---

## Where things stand

### Done
- **Phase 1 + 2** on `main` (PR #1, PR #2).
- **Phase 3** (#10–#12) on PR #5 — cleaning parquet, features, real ML + `/api/ml/*`.
- **Task #13 Dashboard ngành** — IIP + forecast overlay, Digital VA, VSIC heatmap, OECD peer gaps honest.
- **Task #14 Company detail** — profile + channels + online est., RAL case study, crawl timeline + data-quality score.
- **Task #15 Pipeline monitor** — job last-run + history, `data_cleaning` trigger, quality from `cleaning_report.json` (missing → banner).

### Phase 4 remaining
1. **#16 ML Lab** — compare 3 models, forecast vs actual, feature importance from #12 artifacts.
2. **#17 E2E integration** — after modules land.

Suggested next branch: `cursor/phase4-task16-ml-lab` (from Task #15 tip after merge, or Task #15 tip if prior PRs not merged).

### Do not rewrite
- Cleaning, feature engineering, ML train math — unless proven bug.
- Digital VA formula; no fake MEI_BCI; tickers **BMP** not BWE.
- Leave `.scratch/_local_backup/` untracked.

### Local caveats
- `mei_ip` / OECD peer may be missing — UI shows N/A / series_missing (honest).
- Marketplace live scrape still deferred — estimates seed/fallback; UI discloses.
- Prefer existing design language in `frontend/`.
- Staging Postgres still optional — monitor uses parquet + `pipeline_jobs`.

---

## Read first (Task #16)

| Doc | Why |
|-----|-----|
| `AGENTS.md` / `CONTEXT.md` | Domain bounds |
| `docs/plan.md` | § Tiến độ + Module 4 |
| `.scratch/handoff-task15.md` | What #15 delivered |
| `backend/app/api/ml.py`, `ml/models/`, `data/models/` | Lab data sources |
| `frontend` ML page if any | Current Lab surface |

---

## Constraints / do not

- Do not invent GSO/OECD/CafeF/marketplace/forecast numbers.
- Do not change Digital VA / VDEI without CONTEXT + ADR.
- No commit/push unless user asks (or lazy-to-complete finish of the task).

---

## Paste prompt for the new chat

See end of Task #15 chat response (ready-to-paste block for Task #16).
