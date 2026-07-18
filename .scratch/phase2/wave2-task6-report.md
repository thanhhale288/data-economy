# Wave 2 / Task 6 — Website digital detector report

**Branch:** `cursor/phase2-enterprise-digital`  
**Agent:** Subagent B  
**Date:** 2026-07-18

## 1. Checklist map

| Checklist item | Status |
|----------------|--------|
| Rule-based detect ecommerce / giỏ hàng / checkout trên website DN | **Done** — `analyze_html` + `detect_website` (keywords + cart/checkout link/form signals) |
| Cập nhật `has_ecommerce_site`, `digital_presence.has_checkout` | **Done** — `crawl_company_website` → `enrich_company` wiring |
| Khi HTTP fail / block: không đoán — ghi fail + giữ trạng thái cũ | **Done** — `DetectionResult(ok=False)`; keep prior DB flags; first enrich falls back to seed |
| Tests với HTML fixture (có / không checkout) | **Done** — with / without / empty / shop-no-checkout + HTTP fail stubs |
| Detector chạy được cho cả 10 DN | **Done** conceptually via `run_company_crawl` path; unit tests offline |

**Remaining for Task 6:** optional live spot-check of a few of the 10 sites (not required for merge; see §4).

## 2. Files changed

| Path | Action | Notes |
|------|--------|-------|
| `crawlers/companies/website_detector.py` | **New** | Owns all detection logic + `DetectionResult` |
| `crawlers/companies/listed_companies.py` | Thin wrap only | Import `detect_website`; replace `detect_ecommerce_site` body; `crawl_company_website` returns `ok`; fail-safe wiring in `enrich_company` |
| `tests/companies/test_website_detector.py` | **New** | Offline HTML + mocked HTTP |
| `tests/companies/fixtures/site_with_checkout.html` | **New** | |
| `tests/companies/fixtures/site_without_checkout.html` | **New** | |
| `tests/companies/fixtures/site_empty.html` | **New** | |
| `tests/companies/fixtures/site_shop_no_checkout.html` | **New** | |
| `tests/companies/test_listed_companies.py` | Patch + 1 test | Stub `detect_website`; fail-keeps-previous test |
| `.scratch/phase2/wave2-task6-report.md` | **New** | This file |

**Not touched:** `crawlers/financial/**`, marketplace, `digital_metrics.py`, GSO/OECD, models, alembic, seed, pipeline, scheduler, requirements.txt. BCTC / `upsert_company_metadata` / `ALLOWED_TICKERS` / `run_company_crawl` structure unchanged beyond detector calls.

## 3. Tests + results

```bash
cd "/Users/hale/Code/AI in Data Economy" && source .venv/bin/activate
PYTHONPATH=. python -m pytest tests/companies -q
```

**Result:** `12 passed` (2026-07-18).

Coverage:

- HTML: checkout ecommerce page → both flags true
- HTML: corporate page → both false
- HTML: empty → both false
- HTML: shop/catalog without checkout → ecommerce true, checkout false
- HTTP 200 → analyzes body
- HTTP 403 / ConnectError → `ok=False`, flags false, explicit `detail` (caller keeps previous)
- Crawl enrich / idempotency / BWE plastics (Wave 1) still green
- Detect fail keeps prior `has_ecommerce_site` + `has_checkout`

## 4. Provenance / fail semantics

| Situation | Behavior |
|-----------|----------|
| HTTP 200 | Set flags from HTML rules; `has_ecommerce_site` = live OR seed |
| HTTP non-200 / network error | Log warning; `DetectionResult(ok=False)`; **do not guess** |
| Fail + existing website `digital_presence` | Keep company + presence flags |
| Fail + first enrich (no presence row) | Fall back to seed ecommerce / seed website `has_checkout` |
| No `website_url` | `ok=True`, both flags false, `detail=no_url` |

**Live spot-check (optional, not run in this wave):** run detector against the 10 seed `website_url` values (RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BWE) when network is available; record any block/403 as `ok=False` without overwriting prior DB.

## 5. Conflicts / decisions

1. **Fail vs seed on first crawl:** chose seed fallback when no prior website presence exists (avoids wiping known seed flags on a cold fail). Re-runs with existing presence keep DB state.
2. **ASCII keyword boundaries:** short English tokens (`shop`, `cart`, `product`) use `\b` so `showroom` does not match `shop`.
3. **No requirements.txt change** — uses existing `httpx` + `beautifulsoup4`.

## 6. Wave 3 notes

- Task 8 (shop-matcher) can assume website `has_checkout` / `has_ecommerce_site` are updated only when detect `ok=True`.
- Task 9 (digital metrics) should treat website channel checkout as detector-backed when `crawled_at` is fresh; seed remains provenance on detect fail.
- Main agent: tick Task 6 items in `.scratch/phase2/checklist.md` after acceptance.
