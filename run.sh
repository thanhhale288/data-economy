#!/bin/bash
# Thin wrappers. Prefer: make bootstrap / ./scripts/bootstrap.sh for full demo setup.
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
export PYTHONPATH=.
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

case "${1:-all}" in
  seed)
    python -m backend.app.seed
    ;;
  metrics)
    python -c "from backend.app.database import SessionLocal; from pipeline.cleaning.digital_metrics import compute_all_digital_metrics; db=SessionLocal(); print(compute_all_digital_metrics(db)); db.close()"
    ;;
  clean)
    python -c "from backend.app.database import SessionLocal; from pipeline.cleaning.run_cleaning import run_data_cleaning; db=SessionLocal(); print(run_data_cleaning(db)); db.close()"
    ;;
  features)
    python -c "from backend.app.database import SessionLocal; from pipeline.features.engineering import run_feature_engineering; db=SessionLocal(); print(run_feature_engineering(db)); db.close()"
    ;;
  train)
    python -c "from backend.app.database import SessionLocal; from ml.models.trainer import train_all_models; db=SessionLocal(); print(train_all_models(db)); db.close()"
    ;;
  api)
    uvicorn backend.app.main:app --reload --port 8000
    ;;
  frontend)
    cd frontend && npm run dev
    ;;
  all)
    echo "Prefer ./scripts/bootstrap.sh (migrate + seed + Phase 3 order)."
    python -m backend.app.seed
    python -c "
from backend.app.database import SessionLocal
from pipeline.cleaning.digital_metrics import compute_all_digital_metrics
from pipeline.cleaning.run_cleaning import run_data_cleaning
from pipeline.features.engineering import run_feature_engineering
from ml.models.trainer import train_all_models
db = SessionLocal()
print('Metrics:', compute_all_digital_metrics(db))
print('Cleaning:', run_data_cleaning(db))
print('Features:', run_feature_engineering(db))
print('ML:', train_all_models(db))
db.close()
"
    echo "Setup complete. Run: ./run.sh api  (and ./run.sh frontend in another terminal)"
    ;;
  *)
    echo "Usage: ./run.sh [seed|metrics|clean|features|train|api|frontend|all]"
    echo "Full demo bootstrap: make bootstrap  # or ./scripts/bootstrap.sh"
    ;;
esac
