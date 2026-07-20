# Handoff — Manufacturing Data Economy (Phase 4)

**Next session focus:** Phase 4 last task — **Task #18 — Benchmark Module 5**. Do not reopen Task #13–#17 unless fixing a proven bug.

**Date:** 2026-07-20  
**Repo:** `/Users/hale/Code/AI in Data Economy`  
**Remote:** `https://github.com/thanhhale288/data-economy`  
**Phase 3 PR:** https://github.com/thanhhale288/data-economy/pull/5 (`cursor/phase3-clean-features-ml`, tip `9aed9c0`) — still OPEN at Task #17 close  
**Task #13:** `cursor/phase4-task13-dashboard` · PR https://github.com/thanhhale288/data-economy/pull/6  
**Task #14:** `cursor/phase4-task14-company-detail` · PR https://github.com/thanhhale288/data-economy/pull/7  
**Task #15:** `cursor/phase4-task15-pipeline-monitor` · PR https://github.com/thanhhale288/data-economy/pull/8  
**Task #16:** `cursor/phase4-task16-ml-lab` · PR https://github.com/thanhhale288/data-economy/pull/9  
**Task #17:** `cursor/phase4-task17-e2e` · PR https://github.com/thanhhale288/data-economy/pull/10 (base tip Task #16)

---

## Where things stand

### Done
- **Phase 1 + 2** on `main` (PR #1, PR #2).
- **Phase 3** (#10–#12) on PR #5 — cleaning parquet, features, real ML + `/api/ml/*`.
- **Task #13–#16** Dashboard / Company / Pipeline / ML Lab.
- **Task #17 E2E** — offline crawl→clean→features→ML→API + FE contract/build (`tests/e2e/`).

### Phase 4 remaining
1. **#18 Benchmark Module 5** — form nhập (doanh thu, LN, NV, chi phí) → ROA/ROE/Current/Equity ratio + percentile ngành (SingStat BITE style).

Suggested next branch: `cursor/phase4-task18-benchmark` (from Task #17 tip after merge, or Task #17 tip if prior PRs not merged).

### Do not rewrite
- Cleaning, feature engineering, ML train math — unless proven bug.
- Digital VA formula; no fake MEI_BCI; tickers **BMP** not BWE.
- Leave `.scratch/_local_backup/` untracked.
- Do not invent GSO/OECD/CafeF/marketplace/forecast numbers.

### Local caveats
- `mei_ip` / OECD peer may be missing — UI shows N/A / series_missing (honest).
- Marketplace live scrape still deferred — estimates seed/fallback; UI discloses.
- E2E uses ARIMA only in the chain (XGB covered in `tests/ml/`; OpenMP segfault risk on some runners).
- Staging Postgres still optional.

---

## Read first (Task #18)

| Doc | Why |
|-----|-----|
| `AGENTS.md` / `CONTEXT.md` | Domain bounds + financial ratios |
| `docs/plan.md` | § Tiến độ + Benchmark AC |
| `.scratch/handoff-task17.md` | What #17 delivered |
| `backend/app/api/benchmark.py` + FE Benchmark page | Existing stub surface |
| SingStat BITE-style percentile expectations in plan/proposal | Module 5 UX |

---

## Constraints / do not

- Do not invent GSO/OECD/CafeF/marketplace/forecast numbers.
- Do not change Digital VA / VDEI without CONTEXT + ADR.
- No commit/push unless user asks (or lazy-to-complete finish of the task).
- One chat = Task #18 only.

---

## Paste prompt for the new chat

See end of Task #17 chat response (ready-to-paste block for Task #18).
