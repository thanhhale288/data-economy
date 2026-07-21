#!/bin/sh
# Railway / Docker boot: schema + seed before serving UI+API.
set -eu
cd /app
export PYTHONPATH=/app

echo "[boot] alembic upgrade head"
alembic upgrade head

echo "[boot] ensure demo seed"
python - <<'PY'
from backend.app.database import SessionLocal
from backend.app.models import Company
from backend.app.seed import run_seed

db = SessionLocal()
try:
    n = db.query(Company).count()
finally:
    db.close()

if n == 0:
    print("[boot] empty DB — running seed (VSIC, companies, GSO/OECD best-effort)")
    run_seed()
else:
    print(f"[boot] seed skip ({n} companies already present)")
PY

echo "[boot] starting uvicorn on PORT=${PORT:-8000}"
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
