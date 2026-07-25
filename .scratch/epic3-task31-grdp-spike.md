# Epic 3 Task #31 — GRDP / industrial VA spike

**Date:** 2026-07-25  
**Decision:** GRDP / industrial VA crawl remains **deferred**.

## Existing M1 stack (keep)

- IIP Section C — SDMX `nsdp.nso.gov.vn` / fallback CSV
- Shipment E07.03 + inventory E07.04 — PX-Web `pxweb.nso.gov.vn`

## GRDP / VA

No confirmed NSO table ID + series code for manufacturing GRDP/VA was wired in
this epic. GSO publishes digital-economy VA shares of GDP/GRDP, which is **not**
the same as industry GRDP for Section C production accounts.

Until a concrete PX-Web/SDMX table is confirmed, Dashboard M1 continues to use
IIP (+ shipment/inventory) as the production proxy — do not invent GRDP series.
