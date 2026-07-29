# Epic 3 Task #35 — Marketplace live strategy

**Date:** 2026-07-26  
**ADR:** [`docs/adr/0002-marketplace-live-strategy.md`](../docs/adr/0002-marketplace-live-strategy.md)  
**Evidence (#34):** Shopee/TikTok allowlist shops → HTTP 403; `live_ok=0`.

## Recommendation table

| Option | Cost | ToS risk | Demo stability | Choose |
|--------|------|----------|----------------|--------|
| (1) Allowlist + cache snapshot + badge `live\|seed\|fallback` | Low | Low | High (offline) | **Default** |
| (2) Session cookie after manual login | Medium (ops, expiry) | Medium | Medium | **Optional ops** |
| (3) Partner / official API | High without contract | Low if contracted | N/A until contract | Spike note only |
| (4) Anti-bot SaaS | Medium–high $ | High | High technically | **Reject** as default |

## Chosen

1. **Default:** (1) — `data/raw/marketplace_live_cache/` allowlist RAL×shopee, VNM×tiktok; crawl HTTP → cache → seed → fallback; Company detail badge Nguồn.
2. **Optional:** (2) — env `SHOPEE_SESSION_COOKIE` / `TIKTOK_SESSION_COOKIE` wired as Cookie header; never in repo.

## Demo path

```bash
PYTHONPATH=. python scripts/enrich_marketplace_listings.py --prefer-cache --tickers RAL,VNM
```

Expect `live_ok≥1` via cache hit without inventing GMV for non-allowlisted peers.
