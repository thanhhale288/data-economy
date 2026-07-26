# Provenance — marketplace listings fallback

**File:** `data/raw/marketplace_listings_fallback.json`

## Source

| Field | Value |
|-------|--------|
| Primary source | `data/seeds/companies.json` (`provenance` = `seed:companies.json`) |
| Tickers | Full seed allowlist (28), including empty listing arrays for B2B peers |
| Synced | 2026-07-25 (Epic 3 Task #27); DQC curated depth 2026-07-25 (Task #34) |

## Policy

- Figures are **seed / demo micro-level** marketplace listings where present.
  They are **not** live Shopee/TikTok scrapes.
- When a live scrape succeeds, the crawler prefers live items and tags
  `source=live` (persisted on `marketplace_listings.source`). On anti-bot /
  HTTP failure the crawler logs the block, then tries an **allowlisted live
  cache** (`data/raw/marketplace_live_cache/`, ADR-0002 / Task #35) tagged
  `live:cache:…`, then loads seed then this fallback — **never invents**
  `units_sold_est` or `revenue_est`.
- `revenue_est` is set only when both `price` and `units_sold_est` are present
  (`price × units`); otherwise `null`.
- **BMP** / steel / chemicals peers remain without marketplace shops in seed
  and keep `marketplace_listings: []`.

## Task #34 — DQC curated depth (no invented GMV)

| Field | Value |
|-------|--------|
| Ticker | DQC |
| Why | Has Shopee shop URL (`dienquang_officialstore`) but live scrape returns 403 |
| Catalog source | Official e-commerce catalog https://dienquang.com/collections/den-led-bulb (observed 2026-07-25) |
| Platform in seed | `website` (prices from official site — **not** claimed as live Shopee GMV) |
| Fields set | `product_name`, `price`, `product_url` |
| Fields **null** | `units_sold_est`, `revenue_est`, `rating` — no invented sold counts |
| DB `source` | `seed` |

Online revenue for DQC stays **0** until a live Shopee/TikTok scrape supplies
`units_sold_est` (or a future curated row with documented units).

## Live attempt

`fetch_shopee_listings` / `fetch_tiktok_listings` try httpx then optional
Playwright (Epic 3 #28). Unit tests mock HTTP / Playwright. Ops smoke:
`PYTHONPATH=. python scripts/enrich_marketplace_listings.py`.
