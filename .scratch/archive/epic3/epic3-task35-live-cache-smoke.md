# Epic 3 Task #35 — live-cache smoke (allowlist demo path)

**Generated (UTC):** 2026-07-26T08:55:04Z
**Counts:** tickers=3, with_shop=3, with_listing=3, with_gmv_listing=3, live_ok=2

Prefer-cache on RAL/VNM/FPT: RAL+VNM cache hit → `live_ok=2`; FPT no allowlist cache → HTTP 403, no invent.

## Sample definitions

| Sample | Meaning | n |
|--------|---------|---|
| Mẫu niêm yết | Seed allowlist | 3 |
| Mẫu có shop TMĐT | digital_presence shopee/tiktok/lazada URL | 3 |
| Mẫu có listing | ≥1 `marketplace_listings` row | 3 |
| Mẫu có GMV listing | listing với cả price và units_sold_est | 3 |

B2B peers without shop keep `marketplace_listings: []` — no invented GMV.

| stock_code | has_shop | n_seed | n_gmv | seed_sources | live_status | n_live | live_detail |
|------------|----------|--------|-------|--------------|-------------|--------|-------------|
| RAL | true | 3 | 3 | seed | ok | 3 | shopee:cache:hit |
| VNM | true | 2 | 2 | seed | ok | 2 | shopee:error:network error: 403 Forbidden; tiktok:cache:hit |
| FPT | true | 1 | 1 | seed | error | 0 | shopee:error:network error: 403 Forbidden |
