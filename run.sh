#!/bin/bash
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
export PYTHONPATH=.

case "${1:-all}" in
  seed)
    python -m backend.app.seed
    ;;
  metrics)
    python -c "from backend.app.database import SessionLocal; from pipeline.cleaning.digital_metrics import compute_all_digital_metrics; db=SessionLocal(); print(compute_all_digital_metrics(db)); db.close()"
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
    python -m backend.app.seed
    python -c "from backend.app.database import SessionLocal; from pipeline.cleaning.digital_metrics import compute_all_digital_metrics; from ml.models.trainer import train_arima, train_xgboost, train_lstm; db=SessionLocal(); compute_all_digital_metrics(db); train_arima(db); train_xgboost(db); train_lstm(db); db.close()"
    echo "Setup complete. Run: ./run.sh api  (and ./run.sh frontend in another terminal)"
    ;;
  *)
    echo "Usage: ./run.sh [seed|metrics|train|api|frontend|all]"
    ;;
esac
