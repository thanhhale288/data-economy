# Epic 3 Task #43 — Discovery crawl + fuzzy hygiene

**Generated (UTC):** 2026-07-27T17:07:34Z  
**Branch:** `cursor/epic3-phase2-task43-discovery-crawl`  
**Gate:** Task #36 (`MARKETPLACE_DISCOVERY_ENABLED` OFF default + QA allowlist + 0.65)  
**Related:** Task #42 cookie ops smoke (same anti-bot class on known shop URLs)

## Verdict

| Check | Result |
|-------|--------|
| Code path `search_marketplace_shop_candidates` | **yes** — brand → parse-only candidates; never invents URLs |
| Live Shopee search (rang dong / vinamilk) | **blocked** — anti-bot / captcha |
| Live TikTok search (vinamilk) | **blocked** — anti-bot / captcha |
| Auto-link from search → company | **no** — must promote to QA allowlist + env ON |
| Ops smoke `match_source=qa_discovery` | **PASS** (injected RAL allowlist entry; committed file stays `entries: []`) |
| Discovery default OFF after smoke | **yes** |
| Fuzzy hygiene `dong` ⊂ `rangdong` | **PASS** — DPR ↛ `rangdong_official`; RAL still matches via brand alias |
| Invent shop / GMV | **None** |

**Conclusion (honest):** Live marketplace **shop search** is deferred under anti-bot/ToS (same class as #42 listing fetch). The discovery **candidate path** exists in code and feeds only the #36 QA gate. Until search returns parseable shop URLs, operators continue to add vetted URLs manually to `data/mappings/discovery_allowlist.json`. Do **not** enable discovery by default; do **not** adopt anti-bot SaaS.

## Live search spike

| ticker | channel | query | status | n_candidates | detail |
|--------|---------|-------|--------|--------------|--------|
| RAL | shopee | rang dong | blocked | 0 | Shopee anti-bot / captcha |
| VNM | shopee | vinamilk | blocked | 0 | Shopee anti-bot / captcha |
| VNM | tiktok | vinamilk | blocked | 0 | TikTok anti-bot / captcha |

Raw CSV: `.scratch/epic3-task43-discovery-crawl.csv`

## Ops smoke (gate #36, no live search)

```bash
export MARKETPLACE_DISCOVERY_ENABLED=1
# temporary allowlist entry (tests inject; committed file stays empty):
# {"ticker":"RAL","channel_type":"shopee","url":"https://shopee.vn/rangdong_official"}
# → discover_shops_for_company → match_source=qa_discovery
unset MARKETPLACE_DISCOVERY_ENABLED   # back to default OFF
```

Unit coverage: `tests/shop_matcher/test_matcher.py` (RAL allowlist → `qa_discovery`), `tests/marketplace/test_discovery_search.py`.

## Fuzzy hygiene (Task #43)

| Change | Effect |
|--------|--------|
| `MIN_TOKEN_CONTAINMENT_LEN = 5` | Stops len-4 token containment FP |
| `_COMPANY_NOISE` += `dong` | Strips short place token from rubber legal names |
| Tests | `test_dpr_does_not_match_rangdong_official`, reverse RAL↛dongphu, rubber peers in precision matrix |

## How to reproduce

```bash
# Offline unit path (no network)
PYTHONPATH=. pytest -q tests/marketplace/test_discovery_search.py tests/shop_matcher/

# Live search probe (expect blocked until ToS/ops allow)
PYTHONPATH=. python -c "
from crawlers.marketplace.shop_finder import search_marketplace_shop_candidates
print(search_marketplace_shop_candidates('rang dong', channel='shopee'))
"
```

## Implications

1. Discovery remains **OFF by default**; empty allowlist = no new shops.
2. When live search someday returns candidates: promote via `candidates_to_qa_allowlist_entries` → human QA → allowlist file → env ON.
3. Pipeline `resolve_shop_to_company(..., discovery_gated=True)` refuses assignment when gate OFF / not allowlisted.
4. Listing live-cache path (#35/#42) unchanged; #41 still paused.
