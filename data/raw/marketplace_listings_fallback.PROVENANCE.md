# Provenance — marketplace listings fallback

**File:** `data/raw/marketplace_listings_fallback.json`

## Source

| Field | Value |
|-------|--------|
| Primary source | `data/seeds/companies.json` (`provenance` = `seed:companies.json`) |
| Tickers | RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BMP |
| Extracted | 2026-07-18 |

## Policy

- These figures are **seed / demo micro-level** marketplace listings for the fixed
  10-company sample. They are **not** live Shopee/TikTok scrapes.
- When a live scrape succeeds, the crawler prefers live items and tags
  `provenance=live`. On anti-bot / HTTP failure the crawler logs the block,
  returns empty live listings, then loads seed then this fallback — **never
  invents** `units_sold_est` or `revenue_est`.
- `revenue_est` is set only when both `price` and `units_sold_est` are present
  (`price × units`); otherwise `null`.
- **BMP** remains the intentional plastics (VSIC 2220) sample — no marketplace
  shops in seed.

## Live attempt

`crawlers.marketplace.shopee.fetch_shopee_listings` and
`crawlers.marketplace.tiktok.fetch_tiktok_listings` rate-limit HTTP calls.
Default production path attempts live when `run_marketplace_crawl(db)` is
invoked; unit tests set `attempt_live=False` or mock the HTTP client.
