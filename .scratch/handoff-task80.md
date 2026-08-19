# Handoff — Task #80 Chip URL website fail

**Status:** DONE  
**Branch:** `cursor/epic5-phase5-task80-website-url-fail-chip`  
**Base:** `origin/main` @ `5a30cce`  
**Date:** 2026-08-19

## What shipped

Honesty chip when a listed-company website cannot be verified. Status comes from **seed provenance / Task #40 audit**, not a live HTTP probe and not a fabricated status code.

- **Seed (GEE):** `website_verify_status: fail`, `website_verify_reason: ssl_unverified`, nested `digital_channels.website_verify` with `source: epic3_task40_audit`. Official URL stays `https://gelex-electric.com`.
- **API:** optional `CompanyOut.website_verify_status` (`ok|fail|unknown`) and `website_verify_reason` (e.g. `ssl_unverified`). Filled from stored JSON, then documented GEE fallback if the URL still matches the audit host.
- **Quality notes:** fail/unknown append honesty text that forbids inferring TMĐT/checkout from SSL/fetch fail.
- **FE:** `websiteVerifyChip.js` maps status → Vietnamese chip. List (Website column) + CompanyDetail header website chip use existing `badge-warning` / `badge-info` / `metric-chip`. OK tickers stay clean (no chip). Channel-name listing skips the nested provenance object.

## How GEE is flagged

1. Seed provenance `fail` / `ssl_unverified`.
2. If DB was not re-seeded: ticker `GEE` + URL `gelex-electric.com` still maps to the Task #40 audit record.
3. UI label: **chưa verify (SSL)** — not “không có TMĐT”, not checkout no.

## Limitations

- GEE SSL still fails (`CERTIFICATE_VERIFY_FAILED` on the documented official URL). SSL verify stays **on**; no `verify=False`.
- Checkout on that fetch remains **unknown**. Seed `has_checkout=false` / `has_ecommerce_site=false` is storage default, not a measured “no ecommerce” conclusion.
- No `last_http_status` column; no live HTTP status invented.
- Other tickers without provenance are not tagged fail (27/28 were OK in the #40 audit; this task does not re-probe).

## Testing

```
PYTHONPATH=. pytest -q tests/companies/ -k 'website or quality or company'
# 37 passed, 15 deselected

PYTHONPATH=. pytest -q tests/companies/test_website_verify.py
# 8 passed

node --test frontend/src/websiteVerifyChip.test.js
# 5 passed

cd frontend && npm run build
# vite build OK
```

