# Demo / ops targets. Prefer: make bootstrap
# Prerequisite for bootstrap/api/smoke: venv + pip install -r requirements.txt

.PHONY: bootstrap api fe smoke e2e ngrok help

help:
	@echo "Targets:"
	@echo "  make bootstrap  — Docker db, alembic, seed, Phase 3 pipeline (metrics→clean→features→train)"
	@echo "  make api        — FastAPI on :8000"
	@echo "  make fe         — Vite frontend on :5173"
	@echo "  make ngrok      — Build UI into API + expose :8000 via ngrok (teacher demo)"
	@echo "  make smoke      — API demo smoke (scripts/smoke_demo.sh; needs API up)"
	@echo "  make e2e       — Offline E2E pytest (tests/e2e)"

bootstrap:
	@chmod +x scripts/bootstrap.sh
	./scripts/bootstrap.sh

api:
	PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000

fe:
	cd frontend && npm install && npm run dev

smoke:
	@chmod +x scripts/smoke_demo.sh
	./scripts/smoke_demo.sh

e2e:
	PYTHONPATH=. pytest -q tests/e2e/

ngrok:
	@chmod +x scripts/demo_ngrok.sh
	./scripts/demo_ngrok.sh
