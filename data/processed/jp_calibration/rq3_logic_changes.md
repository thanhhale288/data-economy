# RQ3 — logic changes required to run Japan (T08)

T08 rule: reuse the T03 URL-finder; only locale config should change.
Anything below is a *recorded* exception, not a silent fork.

## Must-fix (scoring would collapse without it)

1. **`crawlers/url_finder/domain.py` — Japanese 2nd-level TLDs.**
   `toyota.co.jp` was parsed as eTLD+1 `co.jp` (last two labels). Added
   `.co.jp`, `.or.jp`, `.ne.jp`, `.ac.jp`, `.go.jp`, `.ed.jp`, `.gr.jp`, `.lg.jp`
   to the existing multi-part TLD list. Vietnam `.com.vn` behaviour is unchanged.

## Config-lifting (same scores on Vietnam if `vi.json` matches the old constants)

2. **TLD bonuses** moved from `if locale == "vi"` in `evidence.py` to
   `evidence.tld_bonuses` in the locale JSON. `ja.json` prefers `.co.jp` / `.jp`.
3. **`accept_language`** is read from locale JSON in `SearchClient` and
   `PageFetcher` (was hard-coded `vi-VN`).
4. **`PageFetcher(locale=...)`** is passed from `find_url` so Japan fetches send
   `Accept-Language: ja`.

## Adapter, not a scoring fork

5. **Japan identity loader** (`crawlers/jp_calibration/identity.py`) accepts a
   13-digit 法人番号 as `ticker`/`tax_id`. The Vietnam `load_identity` 10-digit
   MST check is untouched. The finder still receives the same five fields
   (`ticker`, `legal_name`, `tax_id`, `address`, `aliases`).
6. **Forbidden identity keys** gained `company_url` / `homepage_url` so a gBizINFO
   field name cannot leak into the finder table.

## Known non-fixes (transferability evidence)

7. Hypothesis slugs still come from `[a-z0-9]+` after fold — kanji/kana names
   produce no slug unless `aliases` carry romaji/English (filled from NTA
   `enName` / furigana). That is why T08 identity keeps those aliases.
8. Address-token evidence uses a Latin/Vietnamese token regex; Japanese addresses
   rarely contribute `address_tokens`. Not patched.
9. `tax_id_on_page` is a raw substring of the 13-digit number; hyphenated 法人番号
   on pages will miss. Not patched.
10. Search is still DuckDuckGo HTML. If it returns HTTP 202, Japan is
    hypothesis-first — the same limitation as T03.

Scoring (`decide_rules`, `score_html` weights, `classify_error`) was not rewritten
per country.
