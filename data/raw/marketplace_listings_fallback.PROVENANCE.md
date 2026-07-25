# Provenance — marketplace listings fallback

**File:** `data/raw/marketplace_listings_fallback.json`

## Source

| Field | Value |
|-------|--------|
| Primary source | `data/seeds/companies.json` (`provenance` = `seed:companies.json`) |
| Tickers | Full seed allowlist (28), including empty listing arrays for B2B peers |
| Synced | 2026-07-25 (Epic 3 Task #27) |

## Policy

- Figures are **seed / demo micro-level** marketplace listings where present.
  They are **not** live Shopee/TikTok scrapes.
- When a live scrape succeeds, the crawler prefers live items and tags
  `source=live` (persisted on `marketplace_listings.source`). On anti-bot /
  HTTP failure the crawler logs the block, returns empty live listings, then
  loads seed then this fallback — **never invents** `units_sold_est` or
  `revenue_est`.
- `revenue_est` is set only when both `price` and `units_sold_est` are present
  (`price × units`); otherwise `null`.
- DQC has a seed Shopee shop URL without invented listing GMV — online revenue
  stays 0 until live/seed listings exist.
- **BMP** / steel / chemicals peers remain without marketplace shops in seed.

## Live attempt

`fetch_shopee_listings` / `fetch_tiktok_listings` try httpx then optional
Playwright (Epic 3 #28). Unit tests mock HTTP / Playwright.
