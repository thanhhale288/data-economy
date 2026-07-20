# Ops — Demo runbook

Short operator notes for local demo. Formulas and series honesty: `CONTEXT.md`. Full Quick Start: [README](../README.md).

## Bootstrap (recommended)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Postgres URL matching docker compose
make bootstrap         # or: ./scripts/bootstrap.sh
make api               # terminal 1
make fe                # terminal 2
```

**Database path (pick one and stay consistent):**

| Path | How |
|------|-----|
| **Postgres (recommended)** | `docker compose up -d db redis` + `.env` from `.env.example` (`DATABASE_URL=postgresql://mfg_economy:…@localhost:5432/mfg_economy`) |
| **SQLite** | No `.env` (or `DATABASE_URL=sqlite:///./data/mfg_economy.db`); skip compose db |

Redis is started by compose but **not required** for seed, cleaning, features, or training. Crawl/seed need the DB you chose.

**Phase 3 order** (same as `pipeline/dags/scheduler.py` after crawls):

1. `compute_all_digital_metrics`
2. `run_data_cleaning` → `data/processed/cleaned_macro.parquet` (+ marketplace parquet / report)
3. `run_feature_engineering` → `data/processed/features.parquet` + `features_manifest.json`
4. `train_all_models` → `data/models/*`

`scripts/bootstrap.sh` sets `OMP_NUM_THREADS=1` by default (XGBoost OpenMP can segfault on some macOS setups otherwise).

Do **not** skip cleaning/features before train. Do **not** invent GSO/OECD/CafeF numbers when crawl fails — use explicit fallback and surface status in the UI.

## Online vs offline

| Mode | What happens |
|------|----------------|
| **Online** | Seed/crawl need HTTP: NSO/GSO, OECD SDMX, CafeF (and marketplace where configured). Failures must record status/detail — no silent fake series. |
| **Offline** | Use `data/raw/` fixtures / sourced fallbacks already in the repo. UI and Pipeline/ML surfaces must show **fallback / unavailable**, not invent values. |

**API smoke** (API must be up — **not** one-shot with bootstrap):

```bash
make api    # terminal 1 — required
make smoke  # terminal 2 — scripts/smoke_demo.sh
```

On macOS, smoke may probe **arima** for forecast while Dashboard prefers **xgboost** (OpenMP crash risk). See `.scratch/demo-smoke-checklist.md`.

**Offline E2E** (pytest fixtures, no live API): `make e2e` → `PYTHONPATH=. pytest -q tests/e2e/`.

**UI:** one manual browser pass — script does not replace visual empty-states (checklist §4).

## Nightly worker

```bash
PYTHONPATH=. python -m pipeline.dags.scheduler
```

Runs crawls then metrics → cleaning → features → train (see `pipeline/dags/scheduler.py`). Compose service `worker` uses the same entrypoint.

## Branch / merge caveat

Phase 4 (#13–#18) may be merged in the **stack** (`cursor/phase4-task18-benchmark`) but not yet on `main`. For demo:

1. `git fetch origin && git checkout cursor/phase5-task19-demo-ops` (or task18 tip), **or**
2. After stack PR merges to `main`, `git checkout main && git pull`.

Bootstrap does not pull branches. See `.scratch/demo-smoke-checklist.md`.
