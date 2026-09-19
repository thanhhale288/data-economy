# AGENTS.md — Manufacturing Data Economy Platform

Guidance for AI coding agents working in this repository.

## What this project is

Research platform + web demo (website flags, crawlers, listed-firm tools). **Current human plan:** hand off / withdraw from the GVHD measurement topic — see **`docs/plan.md`**. One-pager to send GVHD: **`docs/lab/BAN-GIAO.md`**. Do not implement a full lab-report sprint unless the user explicitly stays on the topic.

Before inventing formulas, industry codes, or sample companies, read **`docs/plan.md`**, then **`CONTEXT.md`**. Do not follow archived proposals (`docs/archive/proposal-v*.md`, `docs/archive/evol-1.md`) for current scope.

**Do not read `docs/knowledge.md`** — human glossary only (listed in `.cursorignore`). Domain for agents = `docs/plan.md` + `CONTEXT.md` + `docs/adr/`. Digital VA / IIP forecast formulas in `CONTEXT.md` are leftover demo code, not lab-report targets.

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
docs/        plan.md (source of truth), agents/, adr/, archive/
.scratch/    archive/ only (historical handoffs); active backlog = docs/plan.md
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
- Do **not** treat Digital VA / VDEI / IIP forecast as lab-report KPIs (`docs/plan.md`). Do not change leftover demo formulas without updating `CONTEXT.md` and an ADR.
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

Single-context: `docs/plan.md` + root `CONTEXT.md` + `docs/adr/`. See `docs/agents/domain.md`.

### GitHub workflow

Commits, PRs, CI, milestones, and phase releases: `.cursor/skills/github-workflow/SKILL.md`.  
One-shot labels/milestones/releases/protection: `bash scripts/github-bootstrap.sh`.

### Epic → Phase → Task (Git branching)

1 task = 1 branch = 1 PR; phase = checklist/milestone; epic = milestone/release (no long-lived epic branch):  
`.cursor/skills/epic-phase-task-git/SKILL.md`. Naming: `cursor/epicE-phaseP-taskT-slug`.

### Lazy-to-complete (phase/task loop)

One chat → many related tasks via waves/subagents; keep branch/PR per task; close with plain-language summary + testing per task (no auto next-task prompt):  
`.cursor/skills/lazy-to-complete-workflow/SKILL.md`. Trigger: continue phase work / run related tasks in parallel.

### Plain task close (giải thích tự động sau task)

**Mặc định** khi agent hoàn thành bất kỳ task nào — user không cần hỏi thêm. Plain-language summary (jargon explained, no generic bullets):  
`.cursor/skills/plain-task-close/SKILL.md`. Rule: `.cursor/rules/plain-task-close.mdc` (`alwaysApply`). Lazy-to-complete W4 Ship cũng bắt buộc skill này.

### Catch-up (“những gì tôi chưa biết”)

Tour Task #13–#18 (what/how/gaps) + terms from `CONTEXT.md` (not `knowledge.md`):  
`.cursor/skills/what-i-dont-know/SKILL.md`.

### Frontend UI (Hallmark)

When editing `frontend/**` UI/layout/styling: `.agents/skills/hallmark/SKILL.md`  
Rule (globs): `.cursor/rules/frontend-hallmark.mdc`.
