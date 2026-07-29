# Epic 3 Task #34 — listing depth (no invented GMV)

**Generated (UTC):** 2026-07-25T16:13:07Z
**Counts:** tickers=28, with_shop=6, with_listing=6, with_gmv_listing=5, live_ok=0

## Before → after (seed)

| Metric | Before | After |
|--------|--------|-------|
| Tickers with ≥1 listing | 5 | 6 |
| Tickers with GMV listing (price×units) | 5 | 5 |
| Tickers with marketplace shop URL | 6 | 6 |

- Listing tickers after: RAL, VNM, FPT, MSN, PNJ, DQC
- GMV tickers after: RAL, VNM, FPT, MSN, PNJ

## Sample definitions

| Sample | Meaning | n |
|--------|---------|---|
| Mẫu niêm yết | Seed allowlist | 28 |
| Mẫu có shop TMĐT | digital_presence shopee/tiktok/lazada URL | 6 |
| Mẫu có listing | ≥1 `marketplace_listings` row | 6 |
| Mẫu có GMV listing | listing với cả price và units_sold_est | 5 |

B2B peers without shop keep `marketplace_listings: []` — no invented GMV.

| stock_code | has_shop | n_seed | n_gmv | seed_sources | live_status | n_live | live_detail |
|------------|----------|--------|-------|--------------|-------------|--------|-------------|
| RAL | true | 3 | 3 | seed | error | 0 | shopee:error:network error: 403 Forbidden |
| HPG | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| VNM | true | 2 | 2 | seed | error | 0 | shopee:error:network error: 403 Forbidden; tiktok:error:network error: 403 Forbidden |
| FPT | true | 1 | 1 | seed | error | 0 | shopee:error:network error: 403 Forbidden |
| GVR | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| DGC | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| MSN | true | 1 | 1 | seed | error | 0 | shopee:error:network error: 403 Forbidden |
| PNJ | true | 1 | 1 | seed | error | 0 | shopee:error:network error: 403 Forbidden; tiktok:error:network error: 403 Forbidden |
| REE | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| BMP | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| VHC | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| ANV | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| IDI | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| SBT | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| QNS | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| HSG | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| NKG | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| POM | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| TLH | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| DQC | true | 2 | 0 | seed | error | 0 | shopee:error:network error: 403 Forbidden |
| GEE | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| TYA | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| DPR | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| CSM | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| AAA | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| DCM | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| BFC | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
| CSV | false | 0 | 0 | - | no_shop | 0 | B2B / no marketplace shop — keep listings empty |
