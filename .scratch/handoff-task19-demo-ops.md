# Handoff — Task #19a Demo ops polish

**Status:** DONE (code ready; **not committed** — user asked no commit unless requested)  
**Date:** 2026-07-20  
**Branch:** `cursor/phase5-task19-demo-ops`  
**Base:** tip Task #18 `771158c` (`cursor/phase4-task18-benchmark`, PR #11)  
**Repo:** `/Users/hale/Code/AI in Data Economy`

---

## Delivered

- `make bootstrap` / `scripts/bootstrap.sh`: Docker (Postgres path) or SQLite; alembic → seed → **metrics → clean → features → train**; prints artifact paths; `OMP_NUM_THREADS=1` (macOS XGB)
- README Quick Start step 4 includes clean + features; Ops section + `docs/ops-demo.md`
- FE empty/provenance: Dashboard, Pipeline, CompanyDetail, Benchmark (API prefill, no hard-coded invented form numbers), ML Lab wording, `api.js` status mapping
- `scripts/smoke_demo.sh` + `.scratch/demo-smoke-checklist.md`; `make smoke` → API smoke; `make e2e` → pytest e2e
- Zero-peer demo VSIC = **1100** (not 3290 — division 32 has PNJ)

## Verify (this chat)

- Bootstrap: SQLite fresh DB → artifacts OK (metrics 10, clean 206, features 111, train 3)
- Smoke: **11 passed, 0 failed**
- Scoped pytest: **30 passed** (`tests/e2e` + benchmark + dashboard + pipeline monitor + ml api)
- `cd frontend && npm run build` → ok

## Do not reopen / do not

- Do not invent GSO/OECD/CafeF/marketplace/forecast/percentiles
- Do not change Digital VA / VDEI
- Do not reopen #13–#18 unless proven bug
- Do not commit `*.db` / heavy model dumps unless asked
- Leave `.scratch/_local_backup/` untracked
- Ticker **BMP** not BWE

## Next

**Task #19b — Proposal Mục 4** cập nhật kết quả thực tế (không invent số).  
Optional: commit + push + PR for #19a when user requests.

## Paste prompt for the new chat

See end of Task #19a chat response.
