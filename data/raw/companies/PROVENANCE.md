# Provenance — `data/raw/companies/`

Structured BCTC fallbacks for the seeded listed-company allowlist (Epic 3 Task #25).

Canonical allowlisted file (git): `../companies_bctc_fallback.json`  
Provenance twin: `../companies_bctc_fallback.PROVENANCE.md`

Entries = one annual row per ticker in `data/seeds/companies.json` (28), fields
copied verbatim including nulls. `source_url` = `seed:companies.json`.

| Note | Detail |
|------|--------|
| BMP | Plastics sample (VSIC 2220); seed may leave `employees` null — keep null |
| Sync | 2026-07-25 from seed; do not invent numbers |

Optional per-ticker files may be added as `{ticker}_bctc_fallback.json` with an
explicit `source_url`. Do not add unsourced invented numbers.
