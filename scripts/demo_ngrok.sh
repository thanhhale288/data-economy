#!/usr/bin/env bash
# One-tunnel demo: FastAPI serves UI+API on :8000, ngrok exposes it publicly.
# Machine must stay awake/online while the teacher browses.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v ngrok >/dev/null 2>&1; then
  echo "ngrok not found. Install: brew install ngrok"
  echo "Then: ngrok config add-authtoken <token>  (from https://dashboard.ngrok.com/get-started/your-authtoken)"
  exit 1
fi

if [[ ! -d .venv ]]; then
  echo "Missing .venv — create it first: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH=.
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

echo "[ngrok-demo] build frontend (same-origin /api)"
(
  cd frontend
  VITE_API_URL= npm run build
)

echo "[ngrok-demo] migrate + offline seed if needed"
alembic upgrade head
SEED_OFFLINE=1 python - <<'PY'
from backend.app.database import SessionLocal
from backend.app.models import Company
from backend.app.seed import run_seed

db = SessionLocal()
try:
    n = db.query(Company).count()
except Exception:
    n = 0
finally:
    db.close()
if n == 0:
    run_seed(offline=True)
else:
    print(f"[ngrok-demo] seed skip ({n} companies)")
PY

if [[ ! -f frontend/dist/index.html ]]; then
  echo "ERROR: frontend/dist/index.html missing after build"
  exit 1
fi

if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[ngrok-demo] port 8000 already in use — reusing it (stop old process if it is not this app)"
else
  echo "[ngrok-demo] starting uvicorn on 0.0.0.0:8000"
  uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
  UV_PID=$!
  trap 'kill $UV_PID 2>/dev/null || true' EXIT
  for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/health >/dev/null; then
      break
    fi
    sleep 0.5
  done
fi

if ! curl -sf http://127.0.0.1:8000/health >/dev/null; then
  echo "ERROR: local http://127.0.0.1:8000/health not OK"
  exit 1
fi

echo
echo "=============================================="
echo "  Local OK:  http://127.0.0.1:8000"
echo "  Starting ngrok — copy the https Forwarding URL"
echo "  Keep this Mac awake until the teacher finishes."
echo "  Free ngrok may show a browser warning → Visit Site"
echo "=============================================="
echo
exec ngrok http 8000
