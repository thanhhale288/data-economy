# PROVENANCE — Mini gold worksheet (Evol-1 T06)

- Generated at (UTC): 2026-08-25T09:33:25Z
- Firms (`fetch_ok` from T05): 89
- Cohort counts:
- frame_pilot: 62
- listed28: 27
- Cascade JSONL sha256: `a67466aa8014b5a6fefe60182a2c4c778a2d121d8799c9e76c6f9e01649958b1`
- Cascade manifest sha256: `71febd6c727281cab742689ab70ffd90d16af5d1ac6d9e5c950a6761c0f1607a`
- Worksheet sha256: `a737427af7020c188631d4a907b870c7a8a1476921528d6b36b310959ead0b4d`

## Method

1. Take every firm with `fetch_ok=true` from T05 `indicators_raw.jsonl` (no subsample).
2. Copy tier-1 / tier-2 outputs into `pre_*` hint columns.
3. Leave `gold_*` blank for **human** annotation per `docs/annotation-handbook-v1.md`.
4. After humans set `reviewed=true`, run `python -m crawlers.mini_gold eval`.

## Limits

- Pre-labels are **not** gold. Do not treat LLM/rules as ground truth.
- Mini gold on pilot cohort only — not a national estimate.
- T05 HTML page cache may be absent; annotators open live URLs.
