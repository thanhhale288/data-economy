# Anti-AI-slop skills (Benchmark FE)

Optional design skills for polishing Module 5 (`Benchmark.jsx`) without changing API math or inventing data. Prefer in-place visual upgrades over a greenfield rewrite.

---

## Install commands

```bash
# Hallmark — structural variety, anti-template UI (nutlope)
npx skills add nutlope/hallmark

# Taste-skill style packages (if published under the same skills CLI):
npx skills add <source>/minimalist-ui
npx skills add <source>/redesign-existing-projects
```

Exact package paths for minimalist-ui / redesign-existing-projects depend on how they were published; this repo may already carry local copies (see below).

**Sandbox note:** `npx skills add …` often **fails in restricted sandboxes** (network / npm). Run install on the host with normal network, or skip install and use skills already present under `.agents/skills/`.

---

## Local copies in this repo

Skills may already exist at:

| Skill | Path |
|-------|------|
| Hallmark | `.agents/skills/hallmark/SKILL.md` |
| Minimalist UI | `.agents/skills/minimalist-ui/SKILL.md` |
| Redesign existing projects | `.agents/skills/redesign-existing-projects/SKILL.md` |

**Do not commit** newly installed or regenerated skill trees under `.agents/skills/` unless the user explicitly asks. Treat them as local agent tooling; keep PRs focused on app + `docs/guides/` product docs.

---

## When to use which

| Goal | Skill |
|------|--------|
| Audit Benchmark for generic AI patterns (no edits) | Hallmark `audit` |
| Redesign layout/type/colour inside existing route | Hallmark `redesign` or redesign-existing-projects |
| Flat editorial / warm monochrome, no gradient slop | minimalist-ui |
| Preserve routes + API; only visual layer | All three — refuse formula / seed changes |

Also respect project frontend rules: no purple-on-white AI defaults; dashboard density is OK on Benchmark but avoid fake marketing chrome.

---

## Prompt template — redesign Benchmark

```text
Read and follow:
- .agents/skills/hallmark/SKILL.md (or run hallmark redesign)
- .agents/skills/minimalist-ui/SKILL.md
- .agents/skills/redesign-existing-projects/SKILL.md
- docs/guides/benchmark-bite-expenditure-ui.md
- docs/guides/frontend-benchmark-roadmap.md

Target: frontend/src/pages/Benchmark.jsx + frontend/src/index.css only
(unless Wave B already split to frontend/src/components/benchmark/* — then edit those).

## Goal
hallmark redesign the Benchmark page for SingStat BITE-like clarity:
expenditure block + honesty empty-states (N/A, insufficient_peers).
Keep Vietnamese economic labels. One composition per section; no purple AI gradient.

## Hard constraints
- Do not change benchmark formulas, schemas, or invent percentiles/GSO numbers.
- Do not delete routes or rewrite the whole frontend.
- Prefill RAL/REE and demo VSIC 1100 must still work.
- Do not commit .agents/skills/ unless I ask.

## Done when
Visual hierarchy improved; smoke checklist in benchmark-bite-expenditure-ui.md still passes.
```

---

## Related

- Expenditure UI: [`benchmark-bite-expenditure-ui.md`](./benchmark-bite-expenditure-ui.md)
- FE waves: [`frontend-benchmark-roadmap.md`](./frontend-benchmark-roadmap.md)
