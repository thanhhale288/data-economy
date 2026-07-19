---
name: github-workflow
description: >-
  Repo GitHub conventions for commits, PRs, CI, milestones, and phase releases
  using git + gh CLI. Use when the user asks to commit, push, open/merge a PR,
  create a release/tag, set up GitHub, or when running git commit / git push /
  gh pr / gh release / gh issue commands for this project.
---

# GitHub workflow (this repo)

Read this skill before any `git commit`, `git push`, `gh pr`, `gh release`, or `gh issue` work.

## Non-negotiables

- Only commit when the user asked to commit (or explicitly asked to finish a GitHub setup that requires push).
- Never commit `.env`, secrets, large raw crawl dumps, `*.db`, or model binaries (`data/models/*.pkl|*.pt`).
- Never invent GSO/OECD/CafeF/marketplace numbers in code or release notes.
- Prefer `gh` for GitHub API actions (PR, issue, release, label, milestone). Use the web UI only if `gh auth` fails.
- Detailed tickets stay in `.scratch/`; GitHub Issues are umbrella/milestone facing only.

## Before commit

1. `git status` / `git diff` / `git log -5 --oneline` (match message style).
2. Stage only relevant files — do not add unrelated WIP, `.scratch/_local_backup/`, or secrets.
3. Commit message: 1–2 sentences, **why** over what; use HEREDOC:

```bash
git commit -m "$(cat <<'EOF'
Short summary of why this change exists.

EOF
)"
```

Style in this repo: full sentences, Phase-aware when applicable  
(e.g. `Complete Phase 2 enterprise digital crawl for demo readiness.`).

## Pull requests

1. Branch: `cursor/phaseN-<slug>` or clear feature slug; base on up-to-date `main` when possible.
2. Push: `git push -u origin HEAD` (request network/`all` permissions as needed).
3. Create PR with `gh pr create` and the repo template (`.github/PULL_REQUEST_TEMPLATE.md`):
   - Summary bullets
   - Link `.scratch/...` status/spec
   - Test plan checkboxes (`PYTHONPATH=. pytest -q`, frontend build if UI)
4. One PR per phase (or coherent slice). Do not open empty PRs.

## After a phase merges to `main`

1. Ensure CI is green on `main`.
2. Create a release (idempotent):

```bash
gh release create "v0.X.0-phaseN" --target main \
  --title "v0.X.0 — Phase N …" \
  --notes "What is live vs fallback; link PR #N."
```

3. Close the phase milestone if open; keep Phase umbrella issue updated or closed.

## CI expectations

Workflow: `.github/workflows/ci.yml`

| Job name (status check) | Command |
|-------------------------|---------|
| Backend tests | `PYTHONPATH=. pytest -q` |
| Frontend build | `cd frontend && npm ci && npm run build` |

Do not merge knowingly broken CI. If fixing CI, prefer a dedicated small PR.

## Bootstrap / one-shot setup

If labels, milestones, umbrella Phase 3 issue, phase releases, or branch protection are missing:

```bash
bash scripts/github-bootstrap.sh
```

Requires working `gh auth`. If auth fails: tell the user to run `gh auth login` or `gh auth refresh -h github.com`, then re-run the script.

## Branch protection (main)

Require PR + status checks named exactly: `Backend tests`, `Frontend build`.  
Script applies this; if API fails (no admin), guide the user to Settings → Branches.

## Local tracker vs GitHub

| Concern | Where |
|---------|--------|
| Specs, wave reports, agent tickets | `.scratch/<feature>/` |
| Phase progress for humans | Milestone + one umbrella Issue |
| Domain / formula locks | `CONTEXT.md` + `docs/adr/` |

Do not migrate every `.scratch` ticket into GitHub Issues.
