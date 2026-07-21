# Frontend Benchmark roadmap

Where Module 5 UI stands after the **BITE expenditure** work on branch `cursor/phase5-benchmark-bite-expenditure`, and what remains for later chats.

Backend peer math and honesty rules stay locked unless a proven bug: `backend/app/services/benchmark_service.py`, `backend/app/schemas/__init__.py`. See [`benchmark-bite-expenditure-ui.md`](./benchmark-bite-expenditure-ui.md).

---

## What this task delivers (expenditure block)

In scope for **this** task / branch:

- Wire and document the SingStat-style **expenditure** ratios from form “Of which” cost fields:
  - `expenditure_related_ratio`
  - `purchase_goods_share`
  - `rental_cost_share`
  - `remuneration_share`
- Keep honesty: null inputs → no ratio; empty peers → N/A percentile + `insufficient_peers` (no invented 50th).
- Surface ratios in compare results alongside existing ROA/ROE/liquidity/worker metrics when inputs exist.
- Guide docs under `docs/guides/` (this file + expenditure UI + optional anti-slop install notes).

**Not** in this task: full SingStat page chrome, industry narrative panel, or a `components/benchmark/*` split.

---

## Next waves (NOT done)

Ship in later chats — one wave per chat if following one-chat-one-task.

### Wave A — Header / breadcrumb + Industry context (before the form)

Mirror BITE information hierarchy without inventing national statistics:

1. **Page header** — product title + short honest subtitle (prototype listed peers, not GSO industry census).
2. **Breadcrumb / path cue** — e.g. Benchmark → VSIC division (from form or prefill), not fake retail category trees.
3. **Industry context block above the form** — peer_scope, expected VSIC 2-digit division, reminder that peers = seeded listed BCTC; link or note to `insufficient_peers` demo.
4. Do **not** invent GSO industry-ratio tables; if no sourced series, show empty/N/A copy only.

Primary file today: `frontend/src/pages/Benchmark.jsx` (+ `frontend/src/index.css` tokens/classes as needed).

### Wave B — Componentize `frontend/src/components/benchmark/*`

Extract from the monolithic page without changing API contracts:

| Suggested module | Responsibility |
|------------------|----------------|
| `BenchmarkForm.jsx` | Fields, prefill buttons, submit payload coercion |
| `BenchmarkResults.jsx` | Metric cards, percentile bars, comparison badges |
| `BenchmarkWarnings.jsx` | `warnings[]` + insufficient_peers empty-state |
| `benchmarkLabels.js` | `METRIC_LABELS`, `COMPARISON_LABELS`, `WARNING_LABELS` |
| `BenchmarkPage.jsx` (or thin `pages/Benchmark.jsx`) | State orchestration + route entry |

Preserve: prefill RAL/REE, demo VSIC `1100`, null → N/A, Vietnamese labels for economics.

### Optional Wave C — Visual polish

After A/B, apply anti-slop skills (Hallmark / minimalist-ui / redesign-existing-projects). See [`anti-ai-slop-skills.md`](./anti-ai-slop-skills.md). Do not change Digital VA or benchmark formulas.

---

## Agent prompt template (next chat)

Copy into a **new** chat. Adjust wave letter only.

```text
Repo: /Users/hale/Code/AI in Data Economy
Branch: create cursor/phase5-benchmark-fe-<wave> from current tip (or continue on cursor/phase5-benchmark-bite-expenditure if still open).

One chat = one task. Read first:
- docs/guides/frontend-benchmark-roadmap.md
- docs/guides/benchmark-bite-expenditure-ui.md
- CONTEXT.md (Benchmark honesty)
- frontend/src/pages/Benchmark.jsx

## Task — Wave A (or B): <short title>

### Do
- Wave A: Add header/breadcrumb + Industry context section ABOVE the benchmark form. Honest copy only (prototype listed peers). No invented GSO numbers.
- OR Wave B: Split Benchmark.jsx into frontend/src/components/benchmark/* per roadmap table; keep pages/Benchmark.jsx as thin entry. No API contract changes.

### Do not
- Edit Digital VA / VDEI formulas or invent peer percentiles.
- Expand seed tickers beyond AGENTS.md list unless asked.
- Commit skills under .agents/skills/ unless user asks.
- Start the other wave in this chat.

### Verify
- Manual: prefill RAL → compare; demo VSIC 1100 → insufficient_peers + N/A percentiles.
- Optional: PYTHONPATH=. pytest -q tests/benchmark/

### Done when
- UI matches the chosen wave; update .scratch handoff if using lazy-to-complete; do not open Wave C unless asked.
```

---

## Related

- Expenditure formulas & field map: [`benchmark-bite-expenditure-ui.md`](./benchmark-bite-expenditure-ui.md)
- Design skills install: [`anti-ai-slop-skills.md`](./anti-ai-slop-skills.md)
- Prior Module 5 ship: Task #18 handoff `.scratch/handoff-task18.md`
