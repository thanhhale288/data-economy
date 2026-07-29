# Wave 2 / Task 7 — Marketplace crawler report

**Branch:** `cursor/phase2-enterprise-digital`  
**Agent:** Subagent C  
**Date:** 2026-07-18  
**Parallel with:** Task 6 (website detector) — did **not** touch `crawlers/companies/**`

## 1. Checklist map (Task 7)

| Checklist item | Status |
|----------------|--------|
| Find Shopee / TikTok shops for 10 DN | **Done** — from seed known URLs (`find_shops_for_company`); Lazada URL pattern kept, no live Lazada scrape |
| Scrape listings: price, units_sold, revenue when both present | **Done** — parsers + `compute_revenue_est`; null when incomplete |
| Persist `digital_presence` + `marketplace_listings` | **Done** — via `run_marketplace_crawl(db)` |
| Rate limit; anti-bot → empty + log + sourced fallback — no invented sales | **Done** — `RateLimiter`; block/HTTP → log + seed/fallback provenance |
| Tests parse/fixture; no network for unit tests | **Done** — 15 tests, `attempt_live=False` / mocked HTTP |
| Keep `ShopMatcher` stub; no full 0.65 QA (Task 8) | **Done** — seed/known URL ⇒ certain `is_match=True` |
| Idempotent upserts | **Done** — presence by `(company_id, url)`; listing by `(company_id, platform, product_name)` |

**Remaining for Task 7:** none.  
**Handed to Task 8:** relocate/improve `ShopMatcher`, fuzzy threshold QA on 10 DN.

## 2. Files changed + ownership

| Path | Action | Notes |
|------|--------|-------|
| `crawlers/marketplace/common.py` | **New** | Rate limit, revenue, seed/fallback loaders, `FetchResult` |
| `crawlers/marketplace/shopee.py` | **New** | Parse + fetch; anti-bot detect |
| `crawlers/marketplace/tiktok.py` | **New** | Parse + fetch; anti-bot detect |
| `crawlers/marketplace/shop_finder.py` | **Rework** | Orchestration; `ShopMatcher` stub kept; `run_marketplace_crawl(db)` signature preserved |
| `crawlers/marketplace/__init__.py` | **Updated** | Public exports |
| `tests/marketplace/**` | **New** | conftest, parse/fetch/persistence + fixtures |
| `data/raw/marketplace_listings_fallback.json` | **New** | Allowlisted `*fallback*` |
| `data/raw/marketplace_listings_fallback.PROVENANCE.md` | **New** | Provenance |
| `.scratch/phase2/wave2-task7-report.md` | **New** | This file |

**Not touched:** `crawlers/companies/**`, `crawlers/financial/**`, `pipeline/cleaning/digital_metrics.py`, `ml/shop_matcher/**`, GSO/OECD, models, alembic, seed.py, pipeline.py, scheduler.py, requirements.txt.

## 3. Test commands + results

```bash
cd "/Users/hale/Code/AI in Data Economy" && source .venv/bin/activate && PYTHONPATH=. python -m pytest tests/marketplace -q
```

**Result:** `15 passed` (2026-07-18).

Coverage:

- Shopee / TikTok JSON parse (price, units, revenue, partial nulls)
- Anti-bot HTML detection
- Live OK / blocked / HTTP error via mocked `httpx`
- Seed/known-URL shop discovery; HPG (no shops) → empty
- Block → seed fallback with provenance; no invented revenue
- Crawl persist shops + listings for 10 tickers; idempotent upsert

## 4. Provenance / fallbacks

| Layer | Source | Tag |
|-------|--------|-----|
| Live (optional) | Shopee/TikTok HTTP when parseable JSON | `provenance=live` |
| Seed | `data/seeds/companies.json` | `seed:companies.json` |
| Fallback file | `data/raw/marketplace_listings_fallback.json` | `fallback:data/raw/marketplace_listings_fallback.json` |

Default crawl **attempts live** then falls back. Unit tests disable live or mock HTTP.  
`MarketplaceListing` has no `source_url` column — provenance is on scrape dicts + logs + PROVENANCE.md (schema change proposed only, not applied).

**BWE:** intentional plastics sample; no marketplace channels in seed — left as-is.

## 5. Shared-file proposals (main agent only)

1. **Optional schema:** add `marketplace_listings.source` or `source_url` for parity with BCTC/GSO provenance columns.
2. **requirements.txt:** no new deps (httpx, rapidfuzz, joblib already present).
3. **`.gitignore`:** `*fallback*` + `*.PROVENANCE.md` already allowlist these files.
4. **Task 8:** move `ShopMatcher` to `ml/shop_matcher/`; thin-wrap from `shop_finder.py`.

## 6. Conflicts / decisions

1. **Live Shopee/TikTok:** heavily anti-bot; production will usually land on seed/fallback. Confirm if Playwright/session cookies are desired later (out of Task 7 scope).
2. **Seed website-platform listings** (e.g. RAL “website” rows in `marketplace_listings`) are still ingested as listings when present in seed — confirm whether Task 9 should exclude `platform=website` from online revenue Σ.
3. **Match policy Wave 2:** seed/known URL ⇒ always link (`is_match=True`). Fuzzy 0.65 QA deferred to Task 8 — do not treat stub scores as production gate.

## 7. Notes for Task 8 (matcher handoff)

- `ShopMatcher` still in `crawlers/marketplace/shop_finder.py` (score + `train` → `data/models/shop_matcher.joblib`).
- Wave 2 linking uses `match_source=seed_known_url`, not `is_match` from fuzzy threshold.
- Seed positive pairs: RAL↔rangdong_official, VNM↔vinamilk_official / @vinamilk, FPT↔fpt_official, MSN↔masan_consumer, PNJ↔pnj_official / @pnj.
- Negatives for QA: HPG/GVR/DGC/REE/BWE have **no** marketplace seed shops — matcher must not invent links.
- Suggested Task 8 seam: `ml/shop_matcher.match(company_name, shop_name) -> {score, is_match}`; `shop_finder` only calls it for **discovered** (non-seed) shops later.
