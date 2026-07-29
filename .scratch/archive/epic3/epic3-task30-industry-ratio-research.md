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

---

## Task #37 re-gate (2026-07-26) — **NO-GO**, still `None`

**Decision:** Reaffirm Task #30. Do **not** set `SOURCED_INDUSTRY_ECOMMERCE_RATIO`.
No `data/mappings/` ratio file wired. Missing listings remain **0.0 + log**.

### Sources re-checked

| Source | What measured | Year | Usable? | Why / why not |
|--------|---------------|------|---------|---------------|
| GSO/NSO digital-economy VA (press / coverage through 2025) | Digital VA **% of GDP/GRDP** (~14% class); e-commerce as share of *digital VA* (~11–14%), not of manufacturing revenue | 2020–2025 | **No** | Wrong concept (macro VA / GDP). Banned by #30/#37 honesty |
| GSO enterprise PX-Web (e.g. manufacturing turnover tables) | Manufacturing firm turnover / profit by tech class | ongoing | **No** | No e-commerce / online-sales channel breakout |
| VECOM EBI 2025 ([EN PDF](https://esc.vn/wp-content/uploads/2025/07/Bao-cao-EBI-2025-Final-En.pdf)) | (a) Online retail ≈ **12% of total retail** (2024); (b) **Fig. 20**: all-sector survey — e-commerce as % of firm revenue in bins (&lt;15% for **58%** of firms); (c) sample mix Construction 18% / Wholesale 17% / Retail 15% — manufacturing present but not a CBCT-only table | Survey ~2024 / report 2025 | **No** | Retail share ≠ CBCT firm revenue. Fig. 20 is **all industries**, histogram bins only — taking 0.15 would recreate rejected invent |
| MoIT / Cục TMĐT white papers | B2C e-commerce **% of retail**; survey sample may list CBCT as firm count share | 2021–2024 | **No** | Retail market share / sample composition, not manufacturing online÷revenue |
| UNCTAD business e-commerce sales (2024 note, 43 economies) | Business e-commerce sales / turnover | through ~2022 | **No** | **Vietnam not in coverage** |
| OECD ICT usage by businesses | E-commerce turnover shares (mostly OECD/partners) | various | **No** | No VN manufacturing e-commerce % of turnover to cite |
| World Bank *Firm-Level Technology Adoption in Vietnam* | Tech adoption (website, social, sales methods) | pre-COVID survey | **No** | Adoption, not e-commerce revenue / total revenue for CBCT |
| Prior silent `×0.15` | Undocumented invent | n/a | **No** | Explicitly rejected |

### Borderline near-miss (still reject)

**VECOM EBI 2025 Figure 20** talks about e-commerce revenue / total firm revenue, but:

1. Not CBCT-only (multi-sector; construction/wholesale/retail dominate sample).
2. Not a single ratio — bins only; modal cell is “&lt;15%” for 58% of firms.
3. Wiring **0.15** = ceiling of the modal bin for all firms = same invent class as rejected silent `×0.15`.
4. Cannot put a clean manufacturing point estimate + table ID into `data/mappings/` + `PROVENANCE.md`.

### Acceptance criteria for a future GO

Published **manufacturing / VSIC C (CBCT)** figure that is explicitly
**online (e-commerce) sales ÷ manufacturing firm revenue** (or industry online
sales ÷ manufacturing revenue), with **year + table/figure ID** → then
`data/mappings/` + `PROVENANCE.md` + set `SOURCED_INDUSTRY_ECOMMERCE_RATIO`.

### Explicit non-starters

- Digital VA % of GDP/GRDP
- E-commerce % of digital VA
- B2C / online retail % of total retail
- VECOM all-sector revenue-share bins
- Any invented 0.15 (or other silent constant)

### Next re-gate triggers

- New GSO enterprise ICT/e-commerce module by VSIC
- MoIT white paper with CBCT online/total revenue breakout
- VECOM table with **manufacturing-only** online/total revenue mean or median
- Vietnam entry into UNCTAD/NSO business e-commerce sales by industry

### Behavior unchanged

- `SOURCED_INDUSTRY_ECOMMERCE_RATIO = None`
- Missing marketplace listings → `0.0` + log
- Explicit `estimate_online_revenue(..., industry_ratio=)` still allowed only when
  the **caller** documents a citation (tests only today)
