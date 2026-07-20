# Handoff — Manufacturing Data Economy (Phase 4)

**Next session focus:** Phase 4 — Web hoàn thiện & Demo. **Start with Task #17 — Integration testing E2E**. Do not reopen Task #13–#16 unless fixing a proven bug. Do not start Benchmark (#18) yet.

**Date:** 2026-07-20  
**Repo:** `/Users/hale/Code/AI in Data Economy`  
**Remote:** `https://github.com/thanhhale288/data-economy`  
**Phase 3 PR:** https://github.com/thanhhale288/data-economy/pull/5 (`cursor/phase3-clean-features-ml`, tip `9aed9c0`) — still OPEN at Task #16 close  
**Task #13:** `cursor/phase4-task13-dashboard` · PR https://github.com/thanhhale288/data-economy/pull/6  
**Task #14:** `cursor/phase4-task14-company-detail` · PR https://github.com/thanhhale288/data-economy/pull/7  
**Task #15:** `cursor/phase4-task15-pipeline-monitor` · PR https://github.com/thanhhale288/data-economy/pull/8  
**Task #16:** `cursor/phase4-task16-ml-lab` · PR https://github.com/thanhhale288/data-economy/pull/9 (base tip Task #15)

---

## Where things stand

### Done
- **Phase 1 + 2** on `main` (PR #1, PR #2).
- **Phase 3** (#10–#12) on PR #5 — cleaning parquet, features, real ML + `/api/ml/*`.
- **Task #13 Dashboard ngành** — IIP + forecast overlay, Digital VA, VSIC heatmap, OECD peer gaps honest.
- **Task #14 Company detail** — profile + channels + online est., RAL case study, crawl timeline + data-quality score.
- **Task #15 Pipeline monitor** — job last-run + history, `data_cleaning` trigger, quality from `cleaning_report.json`.
- **Task #16 ML Lab** — compare 3 models, forecast vs actual, feature importance from #12 artifacts (missing → banner).

### Phase 4 remaining
1. **#17 E2E integration** — crawl → clean → features → ML → API → FE.

Suggested next branch: `cursor/phase4-task17-e2e` (from Task #16 tip after merge, or Task #16 tip if prior PRs not merged).

### Do not rewrite
- Cleaning, feature engineering, ML train math — unless proven bug.
- Digital VA formula; no fake MEI_BCI; tickers **BMP** not BWE.
- Leave `.scratch/_local_backup/` untracked.

### Local caveats
- `mei_ip` / OECD peer may be missing — UI shows N/A / series_missing (honest).
- Marketplace live scrape still deferred — estimates seed/fallback; UI discloses.
- Prefer existing design language in `frontend/`.
- Local `data/models/` may be stale until train — Lab banners, no invented importance/forecast.
- Staging Postgres still optional — Lab uses registry/predictions + artifact files.

---

## Read first (Task #17)

| Doc | Why |
|-----|-----|
| `AGENTS.md` / `CONTEXT.md` | Domain bounds |
| `docs/plan.md` | § Tiến độ + E2E AC |
| `.scratch/handoff-task16.md` | What #16 delivered |
| Pipeline / ML / Dashboard / Company APIs | Integration surface |
| Existing `tests/` | Patterns for E2E smoke |

---

## Constraints / do not

- Do not invent GSO/OECD/CafeF/marketplace/forecast numbers.
- Do not change Digital VA / VDEI without CONTEXT + ADR.
- No commit/push unless user asks (or lazy-to-complete finish of the task).

---

## Paste prompt for the new chat

See end of Task #16 chat response (ready-to-paste block for Task #17).
