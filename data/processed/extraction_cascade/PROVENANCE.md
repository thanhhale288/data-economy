# PROVENANCE — Extraction cascade v0 (Evol-1 T05)

- Generated at (UTC): 2026-08-25T01:16:01Z
- Cohort sha256: `559219276da8401be60d3665792de2637400252d561bcfe60c19d5ea127a1e44`
- Firms processed: 128
- Elapsed seconds: 674.6
- Tier2 LLM enabled: True
- Local LLM pin model: `qwen3:8b`
- Schema sha256: `a5518b7954fdea60da54241200372a429871fef0bbd92d962a2b51bfa49df807`
- Prompt sha256: `8b38d69903b744714d648ad66b583880cf7a4bad2f52c19ec99e202d792eeef4`

## Method

1. Fetch company homepage (httpx). Fail → skip indicators (do not invent).
2. Tier 1: locale JSON rules (cart, payment markers, marketplace/social hrefs).
3. Tier 2: pinned Ollama JSON schema extractor from T04 (optional).
4. Compare tiers field-by-field → agree / conflict / abstain / skip.

## Limits

- Not a national estimate; pilot cohort only.
- Does **not** crawl marketplace product listings (anti-bot / out of scope).
- Frame-pilot URLs only included when `data/raw/extraction_cascade/frame_urls.json` is supplied (URL-finder and/or domain hypothesis); otherwise listed28 only.
- Domain-hypothesis frame URLs are silver candidates — many fail DNS/HTTP; fetch_ok=false rows are skipped, never invented.
