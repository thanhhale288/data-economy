# AGENTS.md — Manufacturing Data Economy Platform

Guidance for AI coding agents working in this repository.

## What this project is

Research platform + web demo for measuring **e-commerce participation** of Vietnam manufacturing firms (VSIC Section C) from web data (OBEC-style), with GSO/OECD macro context and listed-company case studies.

Before inventing formulas, industry codes, or sample companies, read **`CONTEXT.md`**, **`docs/proposal-v4.md`**, and the active backlog **`docs/evol-1.md`**. Legacy proposal: `docs/archive/proposal-v2.md` (do not use for current scope).

**Do not read `docs/knowledge.md`** — human glossary only (listed in `.cursorignore`). Domain for agents = `CONTEXT.md` + `docs/adr/` + `docs/economy-knowledge.md` when formulas need depth.

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
docs/        proposal-v4.md, evol-1.md, agents/, adr/, archive/
.scratch/    archive/ only (historical handoffs); active backlog = docs/evol-1.md
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
- Sample listed companies live in `data/seeds/companies.json` (allowlist derived from seed; Epic 2 ~25–30 with VSIC peer clusters). Expand via seed + `scripts/onboard_company.py`, not ad-hoc DB rows.
- Prefer Vietnamese domain terms from `CONTEXT.md` when talking about economics; keep code identifiers in English.
- Do **not** read `docs/knowledge.md` (human glossary; `.cursorignore`).
- Do **not** bulk-read `.scratch/archive/` — open one archived handoff only if the user asks for that task.

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

### Epic → Phase → Task (Git branching)

1 task = 1 branch = 1 PR; phase = checklist/milestone; epic = milestone/release (no long-lived epic branch):  
`.cursor/skills/epic-phase-task-git/SKILL.md`. Naming: `cursor/epicE-phaseP-taskT-slug`.

### Lazy-to-complete (phase/task loop)

One chat → many related tasks via waves/subagents; keep branch/PR per task; close with plain-language summary + testing per task (no auto next-task prompt):  
`.cursor/skills/lazy-to-complete-workflow/SKILL.md`. Trigger: continue phase work / run related tasks in parallel.

### Catch-up (“những gì tôi chưa biết”)

Tour Task #13–#18 (what/how/gaps) + terms from `CONTEXT.md` (not `knowledge.md`):  
`.cursor/skills/what-i-dont-know/SKILL.md`.

### Frontend UI (Hallmark)

When editing `frontend/**` UI/layout/styling: `.agents/skills/hallmark/SKILL.md`  
Rule (globs): `.cursor/rules/frontend-hallmark.mdc`.
