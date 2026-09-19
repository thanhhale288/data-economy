# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`docs/plan.md`** — source of truth: postpone sending the GVHD withdraw; remaining surface work vs still blocked (do not treat this as a “finish the lab by December” sprint; do not pretend the research is complete)
- **`docs/lab/BAN-GIAO.md`** — handoff one-pager **draft**; do not send to GVHD while plan says postponed
- **`docs/lab/KHAO-SAT-DOANH-NGHIEP.md`** — survey question draft (not a sent form)
- **`docs/lab/DAN-Y-BAO-CAO.md`** — report outline (not a 25-page submission)
- **`docs/lab/KHOP-FORM-WEB.md`** — survey↔web join + DT×% on fixtures only
- **`CONTEXT.md`** at the repo root — terms; Digital VA / IIP forecast are leftover demo, not lab KPIs
- **`docs/adr/`** — read ADRs that touch the area you're about to work in

Archived research drafts: `docs/archive/proposal-v*.md`, `docs/archive/evol-1.md` — do not use for current scope.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## Docs (current scope)

| File | Role |
|------|------|
| `docs/plan.md` | Source of truth: postponed send; remaining surface vs blocked |
| `docs/lab/BAN-GIAO.md` | Handoff draft — do not send while postponed |
| `docs/lab/KHAO-SAT-DOANH-NGHIEP.md` | Survey question draft |
| `docs/lab/DAN-Y-BAO-CAO.md` | Report outline (not a 25-page lab report) |
| `docs/lab/KHOP-FORM-WEB.md` | Survey↔web join + DT×% (fixtures only) |

## File structure

Single-context repo:

```
/
├── CONTEXT.md
├── docs/
│   ├── plan.md
│   ├── lab/
│   ├── adr/
│   └── archive/
├── backend/
├── crawlers/
├── pipeline/
├── ml/
├── frontend/
└── data/
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0001 — but worth reopening because…_
