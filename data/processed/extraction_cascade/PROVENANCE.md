# PROVENANCE — Extraction cascade v0 (Evol-1 T05)

- Generated at (UTC): 2026-08-24T16:54:18Z
- Cohort sha256: `72cc964c91e36695f380ef848cc4f0bfb1c39a51f8e2c7c76590191f092a7665`
- Firms processed: 128
- Elapsed seconds: 326.8
- Tier2 LLM enabled: False
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
- Frame-pilot URLs only included when `data/raw/extraction_cascade/frame_urls.json` is supplied (from URL-finder); otherwise listed28 only.
