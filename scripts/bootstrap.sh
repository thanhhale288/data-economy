#!/usr/bin/env bash
# Demo bootstrap: Docker DB → migrate → seed → Phase 3 artifacts (correct order).
# Presupposes: Python venv activated + `pip install -r requirements.txt`.
# Does not invent GSO/OECD/CafeF numbers; uses seed + existing crawl/fallback paths.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-.}"
# Mitigate XGBoost OpenMP segfaults on some macOS runners (same as tests/ml/conftest).
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
# shellcheck disable=SC1091
[[ -f .venv/bin/activate ]] && source .venv/bin/activate

echo "=== Manufacturing Data Economy — bootstrap ==="
echo "Repo: $ROOT"
echo ""
echo "Prerequisite: venv + pip install -r requirements.txt (not run by this script)."
echo ""

# --- DATABASE_URL consistency ---
# Recommended path (matches .env.example + docker compose db):
#   DATABASE_URL=postgresql://mfg_economy:mfg_economy_pass@localhost:5432/mfg_economy
# Alternative (no Docker DB): omit .env or set sqlite:///./data/mfg_economy.db
#   (backend/app/config.py default). Redis is optional for most jobs.
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a
  source .env
  set +a
  echo "Loaded .env (DATABASE_URL=${DATABASE_URL:-unset})"
else
  echo "No .env found. Copy .env.example → .env for Postgres, or rely on SQLite default."
  echo "  cp .env.example .env"
fi

DB_URL="${DATABASE_URL:-}"
if [[ -z "$DB_URL" ]]; then
  echo "DATABASE_URL unset → app default is SQLite (./data/mfg_economy.db)."
elif [[ "$DB_URL" == postgresql* ]] || [[ "$DB_URL" == postgres* ]]; then
  echo "DATABASE_URL points at Postgres — ensure docker compose db is up and matches credentials."
elif [[ "$DB_URL" == sqlite* ]]; then
  echo "DATABASE_URL points at SQLite — Docker db/redis not required for seed/pipeline."
else
  echo "WARNING: Unrecognized DATABASE_URL scheme: $DB_URL"
fi
echo "Note: Redis (compose service) is optional for seed, clean, features, and train jobs."
echo ""

# --- Docker: db (+ redis optional) ---
if command -v docker >/dev/null 2>&1; then
  if [[ -n "$DB_URL" ]] && { [[ "$DB_URL" == postgresql* ]] || [[ "$DB_URL" == postgres* ]]; }; then
    echo ">>> docker compose up -d db redis"
    docker compose up -d db redis
    echo "Waiting for Postgres health..."
    for _ in $(seq 1 30); do
      if docker compose exec -T db pg_isready -U mfg_economy >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
  else
    echo "Skipping docker compose (not using Postgres DATABASE_URL)."
    echo "Optional: docker compose up -d db redis  # when switching to Postgres"
  fi
else
  echo "WARNING: docker not found — start Postgres yourself if DATABASE_URL is Postgres."
fi
echo ""

# --- Migrate + seed ---
echo ">>> alembic upgrade head"
alembic upgrade head

echo ">>> PYTHONPATH=. python -m backend.app.seed"
PYTHONPATH=. python -m backend.app.seed
echo ""

# --- Phase 3 order (matches pipeline/dags/scheduler.py after crawls) ---
# 1. digital metrics  2. data cleaning  3. feature engineering  4. train models
echo ">>> Phase 3: metrics → cleaning → features → train"
PYTHONPATH=. python - <<'PY'
from pathlib import Path

from backend.app.database import SessionLocal
from pipeline.cleaning.digital_metrics import compute_all_digital_metrics
from pipeline.cleaning.run_cleaning import run_data_cleaning
from pipeline.features.engineering import run_feature_engineering
from ml.models.trainer import train_all_models

db = SessionLocal()
try:
    n_metrics = compute_all_digital_metrics(db)
    print(f"digital_metrics: {n_metrics}")
    n_clean, clean_detail = run_data_cleaning(db)
    print(f"data_cleaning: {n_clean} — {clean_detail}")
    n_feat = run_feature_engineering(db)
    print(f"feature_engineering: {n_feat}")
    n_train = train_all_models(db)
    print(f"ml_training: {n_train}")
finally:
    db.close()

root = Path(".")
expected = [
    root / "data/processed/cleaned_macro.parquet",
    root / "data/processed/features.parquet",
    root / "data/processed/features_manifest.json",
]
print("")
print("=== Expected artifacts ===")
for p in expected:
    status = "OK" if p.is_file() else "MISSING"
    print(f"  [{status}] {p}")

models = root / "data/models"
if models.is_dir():
    files = sorted(p.name for p in models.iterdir() if p.is_file())
    print(f"  [{'OK' if files else 'EMPTY'}] data/models/ ({len(files)} file(s))")
    for name in files[:12]:
        print(f"           - {name}")
    if len(files) > 12:
        print(f"           ... +{len(files) - 12} more")
else:
    print("  [MISSING] data/models/")
PY

echo ""
echo "Bootstrap complete."
echo "Next: make api   # or: PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000"
echo "      make fe    # or: cd frontend && npm install && npm run dev"
echo "Worker (nightly crawl): PYTHONPATH=. python -m pipeline.dags.scheduler"
echo "Ops: docs/ops-demo.md"
