# Demo ops polish

## Branch / PR base

- Branch: `cursor/phase5-task19-demo-ops`
- Base tip: Task #18 `cursor/phase4-task18-benchmark` @ `771158c` (PR #11)
- **Not** bare `main` (Phase 3–4 PRs #5…#11 may still be open)
- Commit/PR: **pending user request** (task constraint: no commit unless asked)

## Bootstrap command

```bash
# Verified path this chat: SQLite (Docker/Colima unavailable)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# no .env → SQLite default; or: export DATABASE_URL=sqlite:///./data/mfg_economy.db
make bootstrap   # metrics → clean → features → train; OMP_NUM_THREADS=1
make api         # terminal 1
make fe          # terminal 2
make smoke       # API must be up
```

Postgres path (when Docker up): `cp .env.example .env` then `make bootstrap`.

## README diff summary

- Quick Start step 4: **includes** `run_data_cleaning` + `run_feature_engineering` before train (was metrics→train only).
- Documents expected artifacts under `data/processed/` and `data/models/`.
- Ops: online HTTP vs offline fixtures/fallback UI; nightly scheduler; branch caveat; links `docs/ops-demo.md`.
- `make bootstrap` / `make api` / `make fe` / `make smoke` / `make e2e`.

## FE empty-state changes

| Page | Change |
|------|--------|
| Dashboard | Bootstrap/train banners when IIP/forecast missing; OECD source/unavailable badge |
| Pipeline | `data_cleaning` never-run + missing `cleaning_report.json` empty-state |
| CompanyDetail | Honest BCTC/metrics/listings empty banners |
| Benchmark | Empty form + API prefill RAL (no hard-coded invented defaults); insufficient_peers UI; zero-peer helper VSIC **1100** |
| ML Lab | Bootstrap wording only (already had empties) |
| `api.js` | Clearer 404/502/503 messages |

## Smoke results (pass/fail per item)

| # | Check | Result |
|---|--------|--------|
| 1 | `GET /health` | PASS |
| 2 | Dashboard IIP + forecast | PASS (114 IIP pts; forecast via arima probe) |
| 3 | Company RAL | PASS |
| 4 | Pipeline trigger + status | PASS |
| 5 | ML mae/rmse/mape keys | PASS (arima, xgboost, lstm) |
| 6 | Benchmark RAL prefill + insufficient_peers (`vsic=1100`) | PASS |
| 7 | Online/fallback notes | NOTES (OECD peer EA20 available; MEI@VNM unavailable; cleaning quality available) |

**Overall:** `11 passed, 0 failed` — `SMOKE OK`

## Online vs fallback observed

- GSO/NSO live OK during bootstrap seed (IIP + PX-Web).
- OECD: INDIGO@VNM + MEI_IP@EA20 OK; MEI_IP@VNM / MEI_BCI / ICT_INVEST **unavailable** (honest, not invented).
- Smoke notes OECD peer `available` (EA20) with ADR-0001 note that VNM MEI is unavailable.

## Remaining debt (Phase 5 docs only?)

- Task **#19b**: proposal Mục 4 with real results (no invented numbers).
- Optional demo slides.
- Merge stack PRs #5…#11 to `main` when ready.
- Commit/push/PR for this branch when user requests (exclude `*.db` / regenerated heavy artifacts unless intentional).

## Verdict: DEMO READY
