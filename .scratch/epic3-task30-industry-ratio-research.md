# Epic 3 Task #30 — Industry-ratio research gate

**Date:** 2026-07-25  
**Decision:** Keep `SOURCED_INDUSTRY_ECOMMERCE_RATIO = None` in
`pipeline/cleaning/digital_metrics.py`.

## Question

Is there a published **manufacturing (VSIC Section C) e-commerce share of firm
revenue** (or equivalent) we can cite to interpolate
`online_revenue = ratio × BCTC_revenue` when marketplace listings are missing?

## Sources checked

| Source | What it measures | Usable as firm online-revenue ratio? |
|--------|------------------|--------------------------------------|
| GSO press release on digital-economy VA share of GDP/GRDP (2020–2024/2025) | Share of **digital economy value-added in GDP**, plus e-commerce as share of *digital VA* (~12–14% of digital VA, not of manufacturing revenue) | **No** — different concept; would invent firm online GMV if applied as × revenue |
| VECOM E-commerce Index reports | Survey / index of e-commerce adoption by locality/firm type | **No** stable manufacturing-only revenue share published as a single ratio for CBCT |
| Existing module constant | Previously rejected silent `×0.15` | Still rejected |

## Conclusion

- No sourced manufacturing e-commerce **revenue share** suitable for
  `SOURCED_INDUSTRY_ECOMMERCE_RATIO`.
- Missing listings → **0.0 + log** (current behavior).
- Callers may still pass an explicit `industry_ratio=` when they have a cited
  figure for a specific study — that path remains tested.
- Do **not** wire GSO digital-economy % of GDP into Digital VA online revenue.

## Follow-up

If VECOM/GSO later publishes Section C online sales / revenue share with a
clear table ID, add `data/mappings/` + `.PROVENANCE.md` and set the constant.
