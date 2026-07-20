# Handoff — Manufacturing Data Economy (Phase 5) — IN PROGRESS

**Status:** Phase 5 started. **#19a Demo ops** DONE (uncommitted until user asks). Next = **#19b Proposal Mục 4**.  
**Date:** 2026-07-20  
**Repo:** `/Users/hale/Code/AI in Data Economy`  
**Remote:** `https://github.com/thanhhale288/data-economy`

**Phase 4 tip / base for demo:** `cursor/phase4-task18-benchmark` @ `771158c` (PR #11)  
**Demo ops branch:** `cursor/phase5-task19-demo-ops` (from #18 tip)

---

## Where things stand

### Done this phase
- **#19a Demo ops polish:** bootstrap order fixed, README/ops, FE empty-states, smoke script. Report: `.scratch/demo-ops-report.md`

### Remaining
1. **#19b Proposal Mục 4** — cite seed/API/tests honestly (no invented numbers).
2. Demo slides/presentation if still needed after docs.

### Do not rewrite
- Cleaning / features / ML / Digital VA / benchmark math unless proven bug.
- Ticker **BMP** not BWE.
- Leave `.scratch/_local_backup/` untracked.

### Local caveats
- Prefer **one** DB backend (Postgres via `.env` **or** SQLite). Docker/Colima may be down — SQLite path works for demo.
- Bootstrap sets `OMP_NUM_THREADS=1` (XGBoost OpenMP segfault risk on macOS).
- Stack PRs #5…#11 may still be open vs `main`.

---

## Read first (#19b)

| Doc | Why |
|-----|-----|
| `docs/proposal-v2.md` | Mục 4 update target |
| `docs/ops-demo.md` / README Ops | What is demo-ready |
| `.scratch/handoff-task19-demo-ops.md` | What #19a closed |
| `CONTEXT.md` | Formula locks |

---

## Constraints / do not

- Do not invent numbers in the proposal — cite seed/API/tests/smoke honestly.
- Do not reopen Phase 4 modules unless proven bug.
- One chat = one task (#19b only).
