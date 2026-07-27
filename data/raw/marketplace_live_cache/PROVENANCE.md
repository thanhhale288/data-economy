# Marketplace live cache — PROVENANCE

**Task:** Epic 3 Task #35 — marketplace live strategy  
**Policy ADR:** `docs/adr/0002-marketplace-live-strategy.md`

## Source

| File | Platform | Ticker | Origin |
|------|----------|--------|--------|
| `RAL.shopee.json` | shopee | RAL | Same shape as `tests/marketplace/fixtures/shopee_ral_listings.json` — demo shop-items JSON matching `parse_shopee_listings` |
| `VNM.tiktok.json` | tiktok | VNM | Same shape as `tests/marketplace/fixtures/tiktok_vnm_listings.json` — demo products JSON matching `parse_tiktok_listings` |
| `allowlist.json` | — | RAL, VNM | Small allowlist only (not full seed 28) |

These snapshots are **versioned demo artifacts** for a stable offline/demo path when live Shopee/TikTok HTTP returns 403 (Task #34 evidence: `live_ok=0`). They are **not** a claim of a successful live scrape on 2026-07-26.

## Tagging

- Provenance string: `live:cache:data/raw/marketplace_live_cache/<TICKER>.<platform>.json`
- Normalized DB/API `source`: `live` (via `normalize_listing_source` — tags starting with `live`)
- UI may show badge `live` (cache path documented here + ADR)

## Policy

1. Cache hit **only** for ticker×platform in `allowlist.json` with an existing JSON file.
2. On HTTP 403/block/error for non-allowlisted shops → seed → fallback (never invent units/GMV).
3. Revenue = `price × units_sold_est` only when both present — never invent units.
4. Do **not** relabel seed/fallback rows as `live` to fake source_health.
5. Refreshing a snapshot from a real live parse (or ops session cookie) is allowed later; update this file with capture date/URL when that happens.

## Task #42 note (2026-07-27)

Ops session cookies were present and applied as `Cookie` headers. Live HTTP for RAL×shopee / VNM×tiktok still returned anti-bot / 403 (`live_ok=0` with `--no-cache`). **No cache files were overwritten.** See `.scratch/epic3-task42-cookie-ops-smoke.md`.
