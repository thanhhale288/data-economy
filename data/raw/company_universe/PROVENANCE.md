# Company universe (shallow) — provenance

**Status:** Stub only (Epic 3 Task #39 / ADR-0003).  
**Rows file:** `rows.json` — intentionally **`[]`**. Do not invent Section C firms.

## What this directory is

Shallow **firm universe** landing zone for a future sourced ingest
(business registration / GSO enterprise stats / exchange listings). Fields are
identity + VSIC + optional website + provenance — **not** BCTC, Digital VA, or
marketplace listings.

## What this is not

- Not the deep listed sample (`data/seeds/companies.json` → `companies` table).
- Not national coverage. Empty rows ≠ “zero manufacturers in Vietnam.”
- Not a place to copy the ~28 seed demo firms to fake scale.

## Future ingest (spec only — not implemented here)

1. Batched fetch with per-host rate limit and resumable cursor/manifest.
2. Write shallow rows with `UniverseProvenance` (source URL/dataset, record id,
   retrieved_at, VSIC evidence).
3. Promote into deep sample only via `scripts/onboard_company.py` + seed append.
4. Sidecar or inline provenance for every batch (same spirit as
   `gso_*_fallback.PROVENANCE.md` and `marketplace_live_cache/PROVENANCE.md`).

## Related

- `docs/adr/0003-scale-section-c-architecture.md`
- `backend/app/schemas/universe.py`
- `backend/app/services/universe_service.py`
- `docs/economy-knowledge.md` § Scale architecture
