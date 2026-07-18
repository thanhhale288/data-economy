# Provenance — companies BCTC fallback

**File:** `data/raw/companies_bctc_fallback.json`  
**Also documented under:** `data/raw/companies/PROVENANCE.md`

## Source

| Field | Value |
|-------|--------|
| Primary source | `data/seeds/companies.json` (`source_url` = `seed:companies.json`) |
| Tickers | RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BMP |
| Period | 2024-12-31 (annual) as recorded in seed |
| Extracted | 2026-07-18 |

## Policy

- These figures are **seed / demo micro-level** values for the fixed 10-company sample.
- They are **not** live HOSE XBRL extractions numbers. When a live structured JSON/HTML
  endpoint becomes available, the crawler prefers that URL and records it in
  `financial_reports.source_url`.
- Missing live fields must remain `null` — never invent or interpolate BCTC numbers.
- **BMP** is an intentional plastics (VSIC 2220) sample profile — do not “correct”
  to a water-utility company.

## Live attempt

`crawlers.financial.bctc_crawler.fetch_bctc` tries optional `live_urls` first.
Default templates are empty (no unreliable scrape). On network/HTTP/parse failure
the crawler loads this fallback (or seed) and sets status=`fallback`.
