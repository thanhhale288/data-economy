# Epic 3 Task #47 — GRDP tỉnh×ngành re-gate (deferred / NO-GO)

**Date:** 2026-07-28  
**Status:** **NO-GO / deferred** (biên bản only — no crawl)  
**Debt from:** Task #38 (national VA GO; province GRDP left open)  
**Prior spike:** `.scratch/epic3-task31-grdp-spike.md` (§ Task #31 / #38)

---

## Decision

| Scope | Verdict | Action in this task |
|-------|---------|---------------------|
| National manufacturing VA (`VA_C` / `VA_C_NOMINAL`) | **GO** (already shipped #38 → #45 → #46) | **Keep** — do not reopen or remove |
| Province × industry GRDP (tỉnh × ngành CBCT / VSIC Section C) | **NO-GO / deferred** | Biên bản only — **no crawler**, **no invent**, **no copy** |
| Copy national `VA_C` down to provinces | **Forbidden** | Explicit ban (see Hard rules) |

**Crawl of province×industry GRDP remains indefinitely parked** under `docs/plan.md` «Chưa làm được…» until a credible NSO table ID exists **and** the user opens a **separate** crawl task.

---

## Evidence — citation gap (no usable table ID)

Re-checked against prior Task #31/#38 findings and current ingest code. No new confirmed PX-Web or SDMX **table ID** for **GRDP by province × manufacturing industry (Section C / CBCT)** was established in this re-gate.

| Candidate / lookalike | What it is | Usable as tỉnh×ngành CBCT GRDP? |
|-----------------------|------------|----------------------------------|
| SDMX `GDPVNM.xml` `NGDPVA_R_ISIC4_C_XDC` → `VA_C` | **National** accounts VA, ISIC4 Section C, `REF_AREA=VN` | **No** — national only |
| SDMX `GDPVNM.xml` `NGDPVA_ISIC4_C_XDC` → `VA_C_NOMINAL` | Same, current prices | **No** — national only |
| PX-Web `E07.03.px` / `E07.04.px` | Industry shipment / inventory indices (wired) | **No** — not GRDP |
| PX-Web National Accounts province GRDP **index** series (qualitative note from #38 spike) | Province-level index without Section-C industry breakdown suitable for this platform | **No** — missing ngành CBCT cross-cut |
| Digital-economy VA shares of GDP/GRDP | Different concept (digital share, not production VA by province×industry) | **No** — rejected lookalike |
| Invented / allocated national `VA_C` × province weights | Fabrication | **Forbidden** |

**Citation gap (plain):** the repo still has **no** verified NSO URL + table/indicator ID that yields GRDP (or equivalent VA) **by province and by manufacturing industry (Section C)** for ingest into `gso_macro` (or a province table). Until that ID is cited with year/series evidence, crawl stays parked.

See also search log: `.scratch/epic3-task47-grdp-deferred.csv`.

---

## National VA remains OK

Task #38 wired manufacturing VA from `GDPVNM.xml` into `gso_macro` via `fetch_gso_va` (`crawlers/gso/iip_crawler.py`). Later tasks surface it honestly:

- **#45** — Dashboard/API M1 (`GET /api/dashboard/va`) — national only; copy says not province GRDP
- **#46** — Pipeline cleaned/features — auxiliary `va_c`; forecast target stays `iip`

These paths must **not** be used to fabricate provincial series.

---

## Hard rules (binding)

1. **Do not crawl** province×industry GRDP in this or any task until a credible NSO table ID is documented and a **dedicated crawl task** is opened.
2. **Do not invent** province GRDP figures, weights, or table IDs.
3. **Do not copy / allocate** national `VA_C` or `VA_C_NOMINAL` down to provinces (equal split, population share, IIP share, or any other proxy).
4. **Do not relabel** IIP, shipment, inventory, or firm-level Digital VA as province GRDP or as `VA_C`.
5. National `VA_C` / `VA_C_NOMINAL` from #38 remain the correct M1 monetary series.

---

## Reopen condition (crawl only — not this biên bản)

| Condition | Then |
|-----------|------|
| Credible NSO **table ID** (PX-Web and/or SDMX) for **tỉnh × ngành CBCT** (Section C) with parseable series + provenance | Open a **separate** crawl/ingest task (not reopen #47 as “implement crawl”) |
| User explicitly requests crawl after citation | Same — new task + branch |

Until then: keep «Crawl GRDP tỉnh×ngành» under indefinitely parked items in `docs/plan.md`.

---

## Out of scope (this task)

- Implementing any GRDP crawler or schema for provinces
- Wiring tỉnh into dashboard / pipeline / ML
- Tasks #50, #41, #48, #49, #19b

---

## Artifacts / doc sync

| Path | Role |
|------|------|
| `.scratch/epic3-task47-grdp-deferred.md` | This biên bản |
| `.scratch/epic3-task47-grdp-deferred.csv` | ID / lookalike search log |
| `.scratch/epic3-task31-grdp-spike.md` | Prior spike; § Task #47 pointer |
| `docs/plan.md` | #47 `[x]`; crawl row stays parked |
| `.scratch/epic3-phase2-plan.md` | § Task #47 |
| `docs/economy-knowledge.md` §4.4 | Deferred confirmed #47 |
| `CONTEXT.md` / `docs/knowledge.md` | Avoid / glossary pointers |
