# Handoff — Manufacturing Data Economy (Phase 4)

**Next session focus:** Phase 4 — Web hoàn thiện & Demo. **Start with Task #15 — Pipeline monitor (Module 3)**. Do not reopen Task #13–#14 unless fixing a proven bug. Do not start Benchmark (#18) yet.

**Date:** 2026-07-20  
**Repo:** `/Users/hale/Code/AI in Data Economy`  
**Remote:** `https://github.com/thanhhale288/data-economy`  
**Phase 3 PR:** https://github.com/thanhhale288/data-economy/pull/5 (`cursor/phase3-clean-features-ml`, tip `9aed9c0`) — still OPEN at Task #14 close (gh auth local may be stale)  
**Task #13:** `cursor/phase4-task13-dashboard` · PR https://github.com/thanhhale288/data-economy/pull/6  
**Task #14:** `cursor/phase4-task14-company-detail` (base tip Task #13 `0e211cc`)

---

## Where things stand

### Done
- **Phase 1 + 2** on `main` (PR #1, PR #2).
- **Phase 3** (#10–#12) on PR #5 — cleaning parquet, features, real ML + `/api/ml/*`.
- **Task #13 Dashboard ngành** — IIP + forecast overlay, Digital VA, VSIC heatmap, OECD peer gaps honest.
- **Task #14 Company detail** — profile + channels + online est., RAL case study, crawl timeline + data-quality score.

### Phase 4 remaining
1. **#15 Pipeline monitor** — job status, cleaning quality summary; staging DB optional.
2. **#16 ML Lab** — compare 3 models, forecast vs actual, feature importance from #12 artifacts.
3. **#17 E2E integration** — after modules land.

Suggested next branch: `cursor/phase4-task15-pipeline-monitor` (from Task #14 tip after merge, or Task #14 tip if prior PRs not merged).

### Do not rewrite
- Cleaning, feature engineering, ML train math — unless proven bug.
- Digital VA formula; no fake MEI_BCI; tickers **BMP** not BWE.
- Leave `.scratch/_local_backup/` untracked.

### Local caveats
- `mei_ip` / OECD peer may be missing — UI shows N/A (Task #13).
- Marketplace live scrape still deferred — estimates seed/fallback; UI discloses.
- Prefer existing design language in `frontend/`.

---

## Read first (Task #15)

| Doc | Why |
|-----|-----|
| `AGENTS.md` / `CONTEXT.md` | Domain bounds |
| `docs/plan.md` | § Tiến độ + Module 3 |
| `.scratch/handoff-task14.md` | What #14 delivered |
| `backend/app/api/pipeline.py`, `frontend` Pipeline page if any | Current monitor surface |
| `data/processed/cleaning_report.json` | Quality summary source |

---

## Constraints / do not

- Do not invent GSO/OECD/CafeF/marketplace numbers.
- Do not change Digital VA / VDEI without CONTEXT + ADR.
- No commit/push unless user asks (or lazy-to-complete finish of the task).

---

## Paste prompt for the new chat

See end of Task #14 chat response (ready-to-paste block for Task #15).
