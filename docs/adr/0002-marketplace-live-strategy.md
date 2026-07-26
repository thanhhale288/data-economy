# ADR-0002: Marketplace live strategy (allowlist + cache)

## Status

Accepted — 2026-07-26

## Context

Epic 3 Phase 2 Task #34 live smoke against Shopee/TikTok allowlist shops
returned HTTP **403** / network error for every shop (`live_ok=0`). Playwright
only runs after HTML 200 without structured JSON, so it never rescues a 403.
Demo and CI still need a **stable** marketplace path that does not silent-invent
GMV or units, and keeps `marketplace_listings.source ∈ {live, seed, fallback}`.

## Decision

1. **Default strategy — small allowlist + versioned cache + badge.**  
   Allowlist ticker×platform pairs under
   `data/raw/marketplace_live_cache/allowlist.json` (initially **RAL×shopee**,
   **VNM×tiktok**). Snapshots live beside the allowlist with PROVENANCE.
   Crawl order when `attempt_live`: HTTP live → on block/error, if allowlisted
   cache exists → load + tag `provenance=live:cache:…` → normalized
   `source=live`. Else seed → fallback. Never invent units/GMV.
2. **Optional ops — session cookie after manual login.**  
   Env `SHOPEE_SESSION_COOKIE` / `TIKTOK_SESSION_COOKIE` may add a `Cookie`
   header for occasional live refresh. Ops-only; never commit secrets; not CI
   default. Expired cookie → same block → cache/seed/fallback.
3. **Spike only — partner / official API.**  
   Document interest; do **not** implement a full paid/partner ingest without
   a contract.
4. **Reject as default — anti-bot SaaS** that bypasses captcha/ToS for the
   đồ án demo.

UI/API must surface the badge (`live` | `seed` | `fallback`) on listings so
demo honesty is visible. Cache-tagged live is documented in
`data/raw/marketplace_live_cache/PROVENANCE.md` — not a claim of “fetched this
run” until a real capture replaces the snapshot.

## Consequences

- Stable offline/demo path for RAL/VNM via cache without inventing GMV for
  peers or DQC units.
- `source_health` marketplace can show `ok` when cache-hit `live` rows exist.
- Task #41 (GMV backfill) may refresh allowlisted snapshots from a real live
  parse later; still no invent.
- Digital VA formulas unchanged.
