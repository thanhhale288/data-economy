# Wave 4 / Task 9 — Digital metrics report

**Branch:** `cursor/phase2-enterprise-digital`  
**Agent:** Subagent E  
**Date:** 2026-07-18  
**Blocked by:** Task 6, 8, 3 (done)

## 1. Checklist map (Task 9)

| Checklist item | Status |
|----------------|--------|
| `online_revenue_est` from Σ(price × units_sold) / `revenue_est` | **Done** — marketplace platforms only |
| Industry-ratio when missing listings — sourced or 0 + log | **Done** — undocumented `×0.15` **REJECTED**; explicit `industry_ratio=` only; else 0.0 + log |
| Adoption / channel diversity from active verified presence | **Done** — `is_active` website + marketplace |
| Digital VA per CONTEXT — formula unchanged | **Done** — verified algebraically |
| Persist `digital_metrics` (+ `industry_share_pct`) | **Done** — upsert by `(company_id, period)` |
| Tests with fixed fixtures | **Done** — `tests/digital_metrics/` 15 passed |

**Nghiệm thu:** Metrics computed from Phase 2 listing/presence data; Digital VA matches CONTEXT.

## 2. Files changed

| Path | Action | Notes |
|------|--------|-------|
| `pipeline/cleaning/digital_metrics.py` | **Updated** | Listing Σ, exclude website platform, sourced-ratio gate, clearer VA expansion |
| `tests/digital_metrics/**` | **New** | Unit + persistence fixtures |
| `.scratch/phase2/wave4-task9-report.md` | **New** | This file |
| `.scratch/phase2/checklist.md` | **Updated** | Task 9 tick |

**Not touched:** `crawlers/**`, `ml/shop_matcher/**`, GSO/OECD, models/migrations, seed, `pipeline.py` / scheduler, requirements.

## 3. Formula verification (CONTEXT)

CONTEXT:

```
Digital_VA = (Online_revenue × Gross_margin) + (Cost_savings × Adoption_score) - Digital_investment
```

Implementation (`compute_digital_va`):

| Term | Binding | Source |
|------|---------|--------|
| Online_revenue | `online_revenue` arg | From listings / optional sourced ratio |
| Gross_margin | BCTC `gross_margin`, else **0.25** | Existing default (unchanged) |
| Cost_savings | `Online_revenue × 0.05` | Existing proxy (unchanged) |
| Adoption_score | weighted active channels | Unchanged weights |
| Digital_investment | `Online_revenue × 0.02` | Existing proxy (unchanged) |

Algebra identical to prior helper (prior inlined `0.05 × adoption` into one variable; now matches CONTEXT naming). **No ADR** — constants/structure not changed.

**REJECTED (considered, not applied):** changing Cost_savings / Digital_investment rates or default margin without ADR.

## 4. Online revenue provenance

| Priority | Rule |
|----------|------|
| 1 | Σ over `platform ∈ {shopee, tiktok, lazada}`: `price × units_sold_est` when both present, else `revenue_est` |
| 2 | If no usable marketplace listings: `industry_ratio × latest BCTC revenue` **only** when ratio passed explicitly or `SOURCED_INDUSTRY_ECOMMERCE_RATIO` is set |
| 3 | Else **0.0** + info log |

### platform=website seed rows

RAL seed includes a `platform=website` listing (downlight, 351M). **Excluded** from `online_revenue_est`. Website commerce is represented via `digital_presence` / `has_ecommerce_site` in adoption, not as marketplace GMV. Aligns with Wave 2 Task 7 note §6.

### Industry-ratio fallback

| Item | Decision |
|------|----------|
| Old `revenue × adoption × 0.15` | **REJECTED** — no GSO/VECOM/OECD source (silent invent) |
| Module default `SOURCED_INDUSTRY_ECOMMERCE_RATIO` | `None` until a sourced ratio is committed |
| Explicit call | `estimate_online_revenue(company, industry_ratio=…)` allowed for tests / future GSO M3 wiring |

**Proposed (main agent only):** commit a sourced manufacturing e-commerce share under `data/mappings/` (e.g. VECOM / GSO) and set `SOURCED_INDUSTRY_ECOMMERCE_RATIO` — do **not** invent one in Task 9.

## 5. Adoption / diversity

- **Adoption:** sum of channel weights for `digital_presence` with `is_active=True` (+0.1 if `has_ecommerce_site`, capped at 1.0). Weights unchanged: website 0.35, shopee 0.30, tiktok 0.20, lazada 0.15.
- **Channel diversity:** `len(unique active channels) / 4.0`.

## 6. Persistence

`compute_all_digital_metrics(db)` loads companies with presence/listings/financials, writes/updates `digital_metrics` for period `2024-12-31`, sets `industry_share_pct` by VSIC 2-digit peer group. Idempotent upsert.

## 7. Tests

```bash
source .venv/bin/activate && PYTHONPATH=. python -m pytest tests/digital_metrics -q
```

**Result:** `15 passed` (2026-07-18).

Regression:

```bash
PYTHONPATH=. python -m pytest tests/companies tests/financial tests/marketplace tests/shop_matcher tests/digital_metrics -q
```

**Result:** `80 passed` (2026-07-18).

Coverage highlights:

- price×units vs revenue_est fallback
- website platform excluded from Σ
- no silent invent when listings empty
- explicit industry_ratio path
- Digital VA algebra vs CONTEXT
- persist + idempotent upsert + industry_share

## 8. Shared-file proposals (main agent only)

1. Optional: wire sourced industry e-commerce ratio (`data/mappings/` + module constant) when GSO M3 / VECOM figure is approved.
2. No schema / seed / scheduler changes required for Task 9.
