# Epic 3 Task #31 / #38 — GRDP / industrial VA

**Date (spike #31):** 2026-07-25  
**Date (re-gate #38):** 2026-07-26  

## Existing M1 stack (keep)

- IIP Section C — SDMX `nsdp.nso.gov.vn` / fallback CSV → `IIP_C`
- Shipment E07.03 + inventory E07.04 — PX-Web `pxweb.nso.gov.vn` → `SHIPMENT_C` / `INVENTORY_C`

## Task #38 decision — GO for national manufacturing VA; GRDP still deferred

### Wired (national accounts VA)

| Stored code | SDMX file | INDICATOR | Notes |
|-------------|-----------|-----------|-------|
| `VA_C` | `GDPVNM.xml` | `NGDPVA_R_ISIC4_C_XDC` | Constant 2010 prices; `UNIT_MULT=9` (billion VND) |
| `VA_C_NOMINAL` | `GDPVNM.xml` | `NGDPVA_ISIC4_C_XDC` | Current prices; same unit multiplier |

- Official URL: https://nsdp.nso.gov.vn/GSO-chung/SDMXFiles/GSO/GDPVNM.xml
- Prefer `FREQ=Q` when present; expand to monthly via **step-hold** (not linear invention).
- Persist via `fetch_gso_va` → `gso_macro` with `source=GSO` or `GSO_FALLBACK`.
- Fallback fixture: `data/raw/gso_va_fallback.csv` + `gso_va_fallback.PROVENANCE.md`.

This is **national** GDP/VA by ISIC4 Section C — usable as M1 “giá trị gia tăng công nghiệp”.

### Still deferred — province GRDP by industry

No confirmed PX-Web/SDMX table ID for **GRDP by province × manufacturing industry** was found in the Task #38 re-gate. PX-Web National Accounts exposes province GRDP index series without a Section-C industry breakdown suitable for this platform.

Do **not** invent GRDP; do **not** relabel IIP as VA/GRDP.

### Task #47 re-gate (2026-07-28) — NO-GO confirmed

Re-gate closed as **deferred/NO-GO biên bản only** (no crawl). Citation gap unchanged: no usable NSO table ID for tỉnh×ngành CBCT. **Forbidden:** copy/allocate national `VA_C` to provinces. National VA from #38 remains valid.

**Artifact:** `.scratch/epic3-task47-grdp-deferred.md` (+ `.csv` search log). Crawl stays parked under `docs/plan.md` «Chưa làm được…» until a credible table ID + separate crawl task.

### Rejected lookalikes

- GSO digital-economy VA shares of GDP/GRDP — not industry production VA.
- ISIC3 legacy VA keys — superseded by ISIC4 Section C mappings above.

## Task #31 historical note

Phase 1 correctly deferred wiring before `GDPVNM.xml` Section C keys were confirmed.
