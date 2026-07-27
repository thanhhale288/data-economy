# ADR-0003: Scale architecture — firm universe vs deep sample vs macro

## Status

Accepted — 2026-07-26

## Context

Epic 3 Phase 2 asks how the platform would later cover **all VSIC Section C**
manufacturers. Today the micro layer is a **listed seed allowlist** of ~28 HOSE/HNX
firms (`data/seeds/companies.json`) with deep BCTC + digital + marketplace fields.
Stuffing a national registry into `companies` would pull shallow rows into Digital
VA, CafeF enrich, marketplace crawl, and VSIC-peer percentiles — and invite
copying the demo seed or inventing BCTC/GMV.

No sourced national firm-level register (business registration / GSO enterprise
microdata) is wired yet; Task #39 must not invent a count or crawl the country.

## Decision

1. **Three tiers (keep separate)**

   | Tier | What it holds | Current home |
   |------|---------------|--------------|
   | **Macro ngành** | IIP, `VA_C` / `VA_C_NOMINAL`, OECD peers | `gso_macro`, `oecd_indicators` |
   | **Universe (shallow)** | Identity + VSIC + optional website + provenance | Stub contract under `data/raw/company_universe/` + `backend.app.schemas.universe` — **not** `companies` |
   | **Deep sample** | BCTC, digital presence, listings, Digital VA | `companies` + related tables; seed allowlist only |

2. **Promotion only.** A universe row becomes deep sample only via explicit
   onboard (`scripts/onboard_company.py` + seed append). Never auto-enrich
   BCTC / marketplace / Digital VA for every universe row.

3. **Metric honesty.** Digital VA and peer percentiles on the listed sample are
   **`prototype_listed_sample`** — not a national Section C standard. Macro
   `VA_C` is official national-accounts VA; do not equate it with Σ Digital VA.

4. **Shallow ingest contract (future).** Batch manifests, per-host rate limits,
   resumable queue status, and row-level provenance (source URL/dataset, record
   id, retrieved_at, VSIC evidence). Spec only in Task #39 — no nationwide crawl.

5. **No production DB migration in this ADR.** Identity keys for unlisted firms
   (tax ID vs enterprise code vs exchange ticker) are unresolved. A Pydantic /
   JSON stub fences the seam without locking a wrong PK. A later task may add
   `company_universe` table once a sourced adapter exists.

## Non-goals (Task #39 / this ADR)

- National crawl or inventing hundreds of BCTC / GMV / listings
- Scaling by copying the demo seed
- Website domain repair (#40), GMV backfill (#41), cookie/partner (#42),
  discovery crawl (#43)
- Choosing a definitive external registry provider without verified access

## Consequences

- Agents and APIs must not treat `companies` row count as “Section C coverage.”
- Future shallow ingest lands in the universe stub path first; deep pipelines
  stay allowlist-scoped.
- `docs/economy-knowledge.md` and `CONTEXT.md` document the three tiers.
- Empty `data/raw/company_universe/rows.json` (`[]`) is intentional — not a bug.

## Alternatives considered

- **Docs-only:** rejected — no compile-time fence against conflating allowlist
  with national universe.
- **Widen `companies` with nullable `stock_code`:** rejected — pollutes deep
  sample pipelines and Digital VA.
- **Alembic table now:** deferred until identity key + authoritative source are
  known.
