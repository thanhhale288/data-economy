# Provenance — companies BCTC fallback

**File:** `data/raw/companies_bctc_fallback.json`  
**Also documented under:** `data/raw/companies/PROVENANCE.md`

## Source

| Field | Value |
|-------|--------|
| Primary source | `data/seeds/companies.json` (`source_url` = `seed:companies.json`) |
| Tickers | Full seed allowlist (28): RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BMP, VHC, ANV, IDI, SBT, QNS, HSG, NKG, POM, TLH, DQC, GEE, TYA, DPR, CSM, AAA, DCM, BFC, CSV |
| Period | Copied verbatim from each seed `financial.period` (annual) |
| Synced | 2026-07-25 (Epic 3 Task #25) |

## Policy

- Figures are **seed / demo micro-level** values for the listed-company sample.
- They are **not** live HOSE XBRL extractions. When a live structured JSON/HTML
  endpoint is available, the crawler prefers that URL and records it in
  `financial_reports.source_url`.
- Missing live fields must remain `null` — never invent or interpolate BCTC numbers.
- **BMP** may have null `employees` / opex fields in seed — keep nulls in this twin.
- **BMP** remains the plastics (VSIC 2220) sample profile — do not “correct”
  to a water-utility company.

## Live attempt

`crawlers.financial.bctc_crawler.fetch_bctc` tries optional `live_urls` first,
then CafeF quarterly HTML. On network/HTTP/parse failure the crawler loads this
fallback (or seed) and sets status=`fallback`.
