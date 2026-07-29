# Demo smoke checklist — Task #19a

Reproducible acceptance on a fresh machine. **Three steps** — bootstrap, API, smoke — then one browser pass for UI.

> **Branch:** checkout tip Phase 4+ (`cursor/phase4-task18-benchmark` or `cursor/phase5-task19-demo-ops`). Plain `main` may lack Phase 3–4 until the stack PR merges.

---

## 1. Bootstrap (one command)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Postgres (recommended): cp .env.example .env && docker compose up -d db redis
# SQLite (no Docker): omit .env or export DATABASE_URL=sqlite:///./data/mfg_economy.db
make bootstrap
```

`make bootstrap` runs: `alembic upgrade head` → seed → **metrics → clean → features → train** (Phase 3 order).  
Sets `OMP_NUM_THREADS=1` (XGBoost OpenMP segfault risk on some macOS).  
Expect: `data/processed/cleaned_macro.parquet`, `features.parquet`, `data/models/*`.

Manual equivalent: see `scripts/bootstrap.sh` or [docs/ops-demo.md](../docs/ops-demo.md).

---

## 2. Start API (required before smoke)

Smoke is **not** one-shot with bootstrap — the API must be running:

```bash
# terminal 1
make api          # http://localhost:8000

# terminal 2 (optional UI)
make fe           # http://localhost:5173
```

---

## 3. Automated API smoke

```bash
# terminal 3 (or same machine, API up)
make smoke
# or: API_BASE=http://localhost:8000 bash scripts/smoke_demo.sh
```

Exits **non-zero** if `/health` is down or hard API contracts break.  
Soft states (empty IIP, untrained ML) are **NOTE**, not fail.

**macOS XGB note:** if preferred forecast model is `xgboost` and `arima` is registered, smoke probes **arima** (avoids OpenMP worker crash). Dashboard UI may still prefer `xgboost` — forecast chart can differ from smoke; use ML Lab or `POST /api/ml/forecast` with `arima` if XGB crashes during demo.

---

## 4. Manual UI (one browser pass before demo)

Script does **not** replace visual checks. Open http://localhost:5173 and tick:

| # | Page | What to verify |
|---|------|----------------|
| 1 | — | `make smoke` exited 0 |
| 2 | **Dashboard** | IIP chart + forecast line **or** honest empty/untrained banners (not blank) |
| 3 | **Companies → RAL** | Profile loads; missing BCTC/metrics show banners |
| 4 | **Pipeline** | Job list; `data_cleaning` status or “chưa chạy” empty-state |
| 5 | **ML Lab** | MAE/RMSE/MAPE chips from registry **or** “chưa train” message |
| 6 | **Benchmark** | RAL prefill from API; VSIC **1100** → insufficient_peers / N/A percentile (no fake 50) |
| 7 | Narration | OECD peer vs GSO fallback / unavailable badges where applicable |

---

## Checklist order (API ↔ UI)

| # | Check | Automated | Manual |
|---|--------|-----------|--------|
| 1 | `GET /health` | Yes — fail if down | — |
| 2 | Dashboard IIP + forecast or empty | Yes — summary, iip, forecast | Dashboard visuals |
| 3 | Company RAL | Yes — `GET /api/companies/RAL` | RAL page |
| 4 | Pipeline trigger + status | Yes — trigger + status + jobs | Pipeline UI |
| 5 | ML MAE/RMSE/MAPE | Yes — `/api/ml/models` keys | ML Lab chips |
| 6 | Benchmark prefill + insufficient_peers | Yes — RAL prefill; `vsic=1100` | Benchmark form |
| 7 | Online vs fallback | Yes — OECD + quality notes | Demo narration |

---

## API paths

| Surface | Path |
|---------|------|
| Health | `GET /health` |
| Dashboard | `GET /api/dashboard/summary`, `/iip`, `/oecd-vs-gso` |
| Company | `GET /api/companies/RAL` |
| Pipeline | `POST /api/pipeline/trigger`, `GET /api/pipeline/status`, `/jobs`, `/quality` |
| ML | `GET /api/ml/models`, `POST /api/ml/forecast` |
| Benchmark | `GET /api/benchmark/prefill/RAL`, `POST /api/benchmark/compare` |

---

## Operator tick boxes

- [ ] `make bootstrap` OK (artifacts printed)
- [ ] `make api` running
- [ ] `make smoke` exits 0
- [ ] UI pass: Dashboard, RAL, Pipeline, ML Lab, Benchmark
- [ ] Fallback/unavailable noted for audience
