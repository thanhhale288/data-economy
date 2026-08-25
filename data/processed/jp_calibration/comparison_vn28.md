# T03 Vietnam n=28 vs T08 Japan n≈300

Same URL-finder (rules, hypothesis-first when search is blocked). Japan labels are gBizINFO silver URLs, not hand gold.

| metric | VN listed 28 | JP manufacturing 300 |
|--------|--------------|----------------------|
| n | 28 | 300 |
| hits | 12 | 21 |
| abstain | 10 | 241 |
| wrong | 6 | 38 |
| hit_rate | 42.9% | 7.0% |
| precision_among_decided | 66.7% | 35.6% |
| recall | 42.9% | 7.0% |
| abstain_rate | 35.7% | 80.3% |

- VN search_blocked: True (HTTP 202 duckduckgo_html)
- JP search_blocked: True (HTTP 202 duckduckgo_html)
- identity_sha256: `8542b9f01b7d96e540f286910151185cc88ac1b7d79050472178ff1e867cb860`
- labels_sha256: `01fdbd74832cd402ada914393c0ad5be5f23acd44f44444761fc9b47a903c531`

- sample seed: 20260825; prefectures: ['静岡県', '愛知県', '大阪府']
- nta_join_hits: 299/300; skipped_no_url (gBizINFO profile had no website): 623

## By employment stratum (Japan)

| stratum | n | hits | hit_rate | precision_among_decided | abstain_rate |
|---------|---|------|----------|-------------------------|--------------|
| 0-20 | 56 | 0 | 0.0% | 0.0% | 85.7% |
| 21-50 | 75 | 8 | 10.7% | 50.0% | 78.7% |
| 51-300 | 88 | 5 | 5.7% | 27.8% | 79.5% |
| 301+ | 81 | 8 | 9.9% | 47.1% | 79.0% |

These two samples are **not** the same population: T03 is 28 listed Vietnamese manufacturers already known to have a website; T08 is 300 Japanese 株式会社 with a gBizINFO silver URL, stratified by employment, mostly without a live search engine. Hit-rate drop is expected; it is not a country ranking.
