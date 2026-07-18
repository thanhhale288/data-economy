# Wave 1 acceptance (main agent)

**Subagent:** [Wave1 Task5](c0498a2d-3107-4d1e-af3a-3c3c40cf7936)  
**Status:** Accepted for Wave 2 start

## Integrated by main agent
- `.gitignore`: allow `data/raw/companies/**` (PROVENANCE trackable)

## Deferred (no schema change yet)
- Optional `financial_reports.source` enum — `source_url` prefixes sufficient for now
- Live BCTC URL templates — empty until user confirms public structured source

## Wave 2 ownership lock
| Agent | May edit | Must not edit |
|-------|----------|---------------|
| B Task 6 | `crawlers/companies/website_detector.py` (new), `tests/companies/test_website_detector.py` + HTML fixtures; **thin** call-site only in `listed_companies.py` (detector import/wrap) | `crawlers/financial/**`, marketplace, digital_metrics, BCTC/metadata logic in listed_companies |
| C Task 7 | `crawlers/marketplace/**` scrapers (prefer `shopee.py`, `tiktok.py`); `tests/marketplace/**`; may leave ShopMatcher stub in place | `website_detector.py`, `listed_companies.py`, `digital_metrics.py`, `ml/shop_matcher/**`, financial |
