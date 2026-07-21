#!/bin/sh
# Railway / Docker boot: best-effort migrate+seed, ALWAYS start uvicorn (UI+API).
cd /app
export PYTHONPATH=/app

echo "[boot] alembic upgrade head"
if ! alembic upgrade head; then
  echo "[boot] WARN: alembic failed — API may 500 until schema exists"
fi

echo "[boot] ensure demo seed (offline, no live crawl)"
if ! SEED_OFFLINE=1 python - <<'PY'
from backend.app.database import SessionLocal
from backend.app.models import Company
from backend.app.seed import run_seed

db = SessionLocal()
try:
    n = db.query(Company).count()
except Exception as exc:
    print(f"[boot] cannot count companies ({exc!r}) — attempting seed")
    n = 0
finally:
    db.close()

if n == 0:
    print("[boot] empty DB — offline seed (VSIC + companies)")
    run_seed(offline=True)
else:
    print(f"[boot] seed skip ({n} companies already present)")
PY
then
  echo "[boot] WARN: seed failed — continuing to start server anyway"
fi

echo "[boot] frontend dist check"
if [ -f /app/frontend/dist/index.html ]; then
  echo "[boot] frontend dist OK"
else
  echo "[boot] WARN: frontend/dist/index.html missing — UI will 404 at /"
fi

echo "[boot] starting uvicorn on PORT=${PORT:-8000}"
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
