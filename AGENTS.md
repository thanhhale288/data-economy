# AGENTS.md — Manufacturing Data Economy Platform

Guidance for AI coding agents working in this repository.

## What this project is

Web platform analyzing the **digital economy of Vietnam manufacturing** (VSIC Section C — chế biến, chế tạo): GSO/OECD macro series, listed-company digital presence, marketplace estimates, IIP forecasting, and SingStat-style benchmarks.

Before inventing formulas, industry codes, or sample companies, read **`CONTEXT.md`** and **`docs/proposal-v2.md`**.

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + SQLAlchemy + PostgreSQL 16 |
| Frontend | React + Vite + Recharts |
| Crawlers | httpx / BeautifulSoup / Playwright (GSO, OECD, companies, marketplace) |
| Pipeline | cleaning, features, `schedule` scheduler |
| ML | statsmodels (ARIMA intended), XGBoost, LightGBM, PyTorch LSTM |
| Infra | Docker Compose, Redis |

## Layout

```
backend/     FastAPI API + models + seed
crawlers/    gso/, oecd/, companies/, marketplace/
pipeline/    cleaning/, features/, dags/
ml/          models/, evaluation/
frontend/    React dashboard
data/        mappings/, seeds/, models/, raw/
docs/        proposal-v2.md, agents/, adr/
.scratch/    local issue tracker (specs + tickets)
.agents/     installed agent skills (mattpocock/skills)
```

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db redis
alembic upgrade head
PYTHONPATH=. python -m backend.app.seed
PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

- API docs: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Boundaries

- Do **not** invent OECD/GSO numbers when crawl fails — use explicit fallback and record it; prefer real SDMX over random series.
- Do **not** change Digital VA / VDEI formulas without updating `CONTEXT.md` and preferably an ADR under `docs/adr/`.
- Sample listed companies are fixed in seed data (RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BMP) unless the user expands the set.
- Prefer Vietnamese domain terms from `CONTEXT.md` when talking about economics; keep code identifiers in English.

## Agent skills

### Issue tracker

Local markdown under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default roles: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` + `docs/adr/`. See `docs/agents/domain.md`.

### GitHub workflow

Commits, PRs, CI, milestones, and phase releases: `.cursor/skills/github-workflow/SKILL.md`.  
One-shot labels/milestones/releases/protection: `bash scripts/github-bootstrap.sh`.

### Lazy-to-complete (phase/task loop)

One chat → one task → one branch → waves → PR; handoff + review + testing + next prompt then stop:  
`.cursor/skills/lazy-to-complete-workflow/SKILL.md`. Trigger: paste handoff / next-task prompt.

### Catch-up (“những gì tôi chưa biết”)

Tour Task #13–#18 (what/how/gaps) + terms missing from `docs/knowledge.md`:  
`.cursor/skills/what-i-dont-know/SKILL.md`.
