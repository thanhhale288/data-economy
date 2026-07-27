# Epic 3 Task #42 — Session cookie ops smoke

**Generated (UTC):** 2026-07-27T15:52:28Z  
**Branch:** `cursor/epic3-phase2-task42-cookie-ops-smoke`  
**ADR:** `docs/adr/0002-marketplace-live-strategy.md` §2 (ops cookie)  
**Allowlist:** RAL×shopee, VNM×tiktok (`data/raw/marketplace_live_cache/allowlist.json`)

## Verdict

| Check | Result |
|-------|--------|
| `SHOPEE_SESSION_COOKIE` present | **yes** (loaded from parent repo `.env`; not in worktree; **not** logged) |
| `TIKTOK_SESSION_COOKIE` present | **yes** |
| Cookie → `Cookie` header wired | **yes** (`session_cookie_headers` / `marketplace_request_headers`) |
| Live HTTP unlock with cookie (`--no-cache`) | **FAIL** — still anti-bot / 403; `live_ok=0` |
| Cache-on-fail demo path | **PASS** — `live_ok=2` via allowlisted cache (not “fetched this run”) |
| Cache refresh from live parse | **Not done** — no successful live parse; leave snapshots + PROVENANCE as #35 demo artifacts (#41 owns refresh when live OK) |
| Secrets in git / `.scratch` | **None** |

**Conclusion (honest):** Ops prerequisite (cookie in env) is met and headers are applied, but **browser session cookies alone do not unlock** Shopee/TikTok shop HTML for this httpx path on 2026-07-27. Keep ADR-0002 default: allowlist + versioned cache. Do **not** adopt anti-bot SaaS. Partner/official API remains spike-only (see `.scratch/epic3-task42-partner-api-spike.md`).

## Env (presence only)

Cookie values live in `/Users/hale/Code/AI in Data Economy/.env` (gitignored). Worktree has no `.env` copy. Names documented in `.env.example`.

```text
SHOPEE_SESSION_COOKIE: present=yes
TIKTOK_SESSION_COOKIE: present=yes
```

## Runs

### A — Cookie + `--no-cache` (true live HTTP)

| stock_code | live_status | n_live | live_detail |
|------------|-------------|--------|-------------|
| RAL | blocked | 0 | shopee:blocked:Shopee anti-bot / captcha / access denied |
| VNM | blocked | 0 | shopee:blocked:…; tiktok:blocked:HTTP 403 for https://www.tiktok.com/@vinamilk |

**Summary:** `live_ok=0`

### B — Cookie + cache-on-fail (ops default)

| stock_code | live_status | n_live | live_detail |
|------------|-------------|--------|-------------|
| RAL | ok | 3 | shopee:blocked:…; **shopee:cache:hit** |
| VNM | ok | 2 | shopee:blocked:…; tiktok:blocked:HTTP 403…; **tiktok:cache:hit** |

**Summary:** `live_ok=2` (cache-tagged `live`, not fresh scrape)

### C — Control: no cookie + `--no-cache`

| stock_code | live_status | n_live | live_detail |
|------------|-------------|--------|-------------|
| RAL | blocked | 0 | shopee:blocked:Shopee anti-bot / captcha / access denied |
| VNM | blocked | 0 | shopee:blocked:…; tiktok:blocked:TikTok anti-bot / captcha / access denied |

**Summary:** `live_ok=0` — same class of failure as Run A (cookie did not change outcome).

## How to reproduce (ops)

```bash
# From repo root; ensure parent or local .env has cookies (never commit)
export $(grep -E '^(SHOPEE_SESSION_COOKIE|TIKTOK_SESSION_COOKIE)=' .env | xargs)  # or use python-dotenv

# True live (no cache mask)
PYTHONPATH=. python scripts/enrich_marketplace_listings.py --tickers RAL,VNM --no-cache

# Ops default (HTTP then allowlisted cache)
PYTHONPATH=. python scripts/enrich_marketplace_listings.py --tickers RAL,VNM
```

Raw auto reports also under:

- `.scratch/epic3-task42-cookie-ops-smoke-nocache.{md,csv}` (Run A)
- `.scratch/epic3-task42-cookie-ops-smoke.{md,csv}` (Run B — listing-depth stem)

## Implications

1. Demo/CI continue to rely on `prefer-cache` / cache-on-fail for RAL/VNM.
2. Task **#41** (GMV backfill + refresh live-cache) stays **tạm dừng** until a real live parse exists — cookie smoke alone is insufficient.
3. Next credible unlock path = partner/official API **with contract** (spike note), not scraping SaaS.
