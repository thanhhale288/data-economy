# Epic 3 Task #34 — listing depth (no invented GMV)

**Generated (UTC):** 2026-07-27T15:52:27Z
**Counts:** tickers=2, with_shop=2, with_listing=2, with_gmv_listing=2, live_ok=0

## Sample definitions

| Sample | Meaning | n |
|--------|---------|---|
| Mẫu niêm yết | Seed allowlist | 2 |
| Mẫu có shop TMĐT | digital_presence shopee/tiktok/lazada URL | 2 |
| Mẫu có listing | ≥1 `marketplace_listings` row | 2 |
| Mẫu có GMV listing | listing với cả price và units_sold_est | 2 |

B2B peers without shop keep `marketplace_listings: []` — no invented GMV.

| stock_code | has_shop | n_seed | n_gmv | seed_sources | live_status | n_live | live_detail |
|------------|----------|--------|-------|--------------|-------------|--------|-------------|
| RAL | true | 3 | 3 | seed | blocked | 0 | shopee:blocked:Shopee anti-bot / captcha / access denied |
| VNM | true | 2 | 2 | seed | blocked | 0 | shopee:blocked:Shopee anti-bot / captcha / access denied; tiktok:blocked:HTTP 403 for https://www.tiktok.com/@vinamilk |
