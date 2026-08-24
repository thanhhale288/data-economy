# PROVENANCE — URL-finder identity (Evol-1 T03)

- Retrieved at (UTC): 2026-08-24T10:11:03Z
- Identity source: public masothue.com HQ pages.
- HQ page URLs in `masothue_hints.json` were resolved from the public web index (masothue listings), then fetched. **No website URL was sent to search.**
- Hint URLs provided: 28
- Firms with HQ tax identity: 28 / 28
- Missing: (none)

## Split

- `identity_28.json` — ticker, legal name, tax_id (MST), address, province, aliases. **No URL fields.**
- `labels_28.json` — gold official website = seed `website_url` (corporate homepage, not shop channel).
- Finder pipeline reads identity only. Evaluator opens labels after predictions are written.

## URL candidates when search is blocked

- DuckDuckGo HTML (and Wikimedia SPARQL) return HTTP 403 from this environment; the finder does **not** retry bot walls.
- Fallback candidates are **domain hypotheses**: slug from legal name / aliases / ticker + locale suffixes (`.com.vn`, `.vn`, `.com`), DNS-filtered, then scored on-page (MST / name). Gold `website_url` is never read by the finder.
- masothue HQ pages in this snapshot do not expose a website field, so they are identity-only.

## Limits

- masothue is a public tax directory, not the official GSO/Cổng ĐKKD frame.
- Address text follows the directory snapshot on retrieve day; may lag mergers.
- Branch MST pages (`0123456789-001`) are dropped; only 10-digit HQ codes are kept.
- GEE seed display name is 'Điện Gia Dụng Gelex'; directory legal name is 'Công ty Cổ phần Điện lực Gelex' (same Gelex Electric listed vehicle).
