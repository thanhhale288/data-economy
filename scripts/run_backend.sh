#!/bin/bash
# Run backend với env vars cần thiết để tránh segfault
cd "$(dirname "$0")/.."
source .venv/bin/activate

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export PYTHONPATH=.

uvicorn backend.app.main:app --port 8000 "$@"
