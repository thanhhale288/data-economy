# Wave 1 / Task 5 — Company crawler report

**Branch:** `cursor/phase2-enterprise-digital`  
**Agent:** Subagent A  
**Date:** 2026-07-18

## 1. Task done / remaining (checklist map)

| Checklist item | Status |
|----------------|--------|
| Enrich/sync metadata for 10 DN from seed (+ published when available) | **Done** — `upsert_company_metadata` from `companies.json`, fixed ticker order |
| Official website → `companies` / `digital_presence` (`channel_type=website`) | **Done** — upsert single active website row; collapses duplicates |
| Structured BCTC → `financial_reports` (HTML/XBRL/API preferred) | **Done** — JSON + HTML parsers; live optional; seed/fallback upsert |
| Missing fields = null + provenance/fallback — no invented numbers | **Done** — null preserved; `source_url` records provenance |
| Idempotent on exactly 10 tickers | **Done** — `ALLOWED_TICKERS`; upsert by unique keys |
| Tests parser/ingest (fixture) + runnable on 10 DN | **Done** — 11 tests; live stubbed; real seed/fallback path covered |
| Keep detector as-is / thin-wrap — no checkout expansion | **Done** — `detect_ecommerce_site` unchanged semantics |
| Entry point `run_company_crawl(db)` for scheduler/pipeline | **Done** |

**Remaining for Task 5:** none for this wave.  
**Not in scope:** Task 6/7/8/9 (detector expansion, marketplace, matcher, digital metrics).

## 2. Files changed + ownership

| Path | Action | Owner |
|------|--------|-------|
| `crawlers/companies/listed_companies.py` | Rework enrich + keep detector | Task 5 |
| `crawlers/financial/__init__.py` | **New** | Task 5 |
| `crawlers/financial/bctc_crawler.py` | **New** | Task 5 |
| `tests/companies/**` | **New** | Task 5 |
| `tests/financial/**` | **New** | Task 5 |
| `data/raw/companies_bctc_fallback.json` | **New** (allowlisted `*fallback*`) | Task 5 |
| `data/raw/companies_bctc_fallback.PROVENANCE.md` | **New** | Task 5 |
| `data/raw/companies/PROVENANCE.md` | **New** (subdir may be gitignored) | Task 5 |
| `.scratch/phase2/wave1-task5-report.md` | **New** (this file) | Task 5 |

**Not touched:** marketplace, GSO/OECD, models, alembic, seed.py, pipeline.py, scheduler.py, requirements.txt, `digital_metrics.py`.

## 3. Test commands + results

```bash
PYTHONPATH=. pytest tests/companies tests/financial -q
```

**Result:** `11 passed` (2026-07-18).

Coverage:

- JSON / HTML BCTC parse (including null fields)
- Financial upsert idempotency `(company_id, period, report_type)`
- Live success + network fail → seed/fallback provenance
- Unknown ticker → empty / no invented revenue
- Crawl enrich 10 companies + website presence + BWE plastics sample
- Crawl idempotent (10 companies, 10 website rows, 10 financial rows)

## 4. Provenance / fallback used

| Layer | Source | `financial_reports.source_url` |
|-------|--------|--------------------------------|
| Live (optional) | Caller-supplied `live_urls` JSON/HTML | Actual HTTP URL |
| Fallback file | `data/raw/companies_bctc_fallback.json` | `seed:companies.json` (copied from seed) or `fallback:data/raw/companies_bctc_fallback.json` |
| Seed | `data/seeds/companies.json` | `seed:companies.json` |

Default `DEFAULT_LIVE_URL_TEMPLATES` is **empty** — no fragile third-party scrape wired without a verified public structured endpoint. Live is tested via fixtures/mocks.

**BWE:** left as intentional plastics sample (VSIC 2220 / Bình Minh profile). Not “corrected” to water utility.

## 5. Shared-file proposals for main agent

1. **`.gitignore`:** allow `data/raw/companies/` (or at least `data/raw/companies/PROVENANCE.md`). Today only `data/raw/*fallback*` and `data/raw/*.PROVENANCE.md` are un-ignored; the subdirectory PROVENANCE may not be tracked.
2. **Optional schema (proposal only — do not apply in Task 5):** add `financial_reports.source` enum-like string (`LIVE` / `SEED` / `FALLBACK`) alongside existing `source_url` for parity with GSO/OECD. Current design uses `source_url` prefixes (`seed:`, `fallback:`, `http…`) — sufficient for Wave 1.
3. **Seed sync:** when companies already exist from `seed.py`, crawl updates metadata + upserts BCTC; seed still owns initial insert of marketplace listings (Task 7).
4. **Task 6 call-site:** replace body of `detect_ecommerce_site` with import from new `website_detector.py` without changing `run_company_crawl` signature.

## 6. Conflicts / decisions needing user confirmation

1. **Live BCTC endpoint:** no production HOSE/CafeF/SSI URL is wired. Confirm preferred public structured source before enabling live templates.
2. **Website `has_checkout`:** still driven by the existing inline detector (HTTP fail → false). Task 6 may change fail semantics (“keep previous or false + log”). Confirm before Task 6 overwrites.
3. **Seed vs live website URL:** for FPT/MSN, seed `digital_presence.website` can differ from `website_url` (e.g. shop vs corporate). Crawl prefers seed website channel URL when present — confirm this is desired.

## 7. Blockers for Wave 2

- **None hard.** Wave 2 (Task 6 detector ∥ Task 7 marketplace) can start.
- Soft dependency: Task 6 should thin-wrap `detect_ecommerce_site` only; Task 7 should not edit `listed_companies.py` except via main-agent integration if a hook is needed.
- Soft: track `companies_bctc_fallback.json` in git (already allowlisted by name pattern).
