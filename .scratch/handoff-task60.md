# Handoff — Task #60 Shop matcher v2

**Status:** DONE  
**Branch:** `cursor/epic4-phase3-task60-shop-matcher-v2`  
**Date:** 2026-07-30  
**Phase:** Epic 4 Phase 4.3 (Marketplace NLP)  
**Base:** `origin/main` @ `84ee06b`  
**Commit:** `36915e7`  
**PR:** https://github.com/thanhhale288/data-economy/pull/50  
**Embedding path from #59:** không reuse — Task #59 ship TF-IDF categorizer only; Task #60 pin `sentence-transformers==3.3.1` độc lập.

---

## Delivered

- `ml/shop_matcher/hybrid.py` — `HybridShopMatcher` (default `ShopMatcher`): RapidFuzz + vector cosine + short-prefix rerank
- `ml/shop_matcher/embeddings.py` — ST primary when requested; TF-IDF char_wb fallback (default runtime / CI)
- `ml/shop_matcher/evaluate.py` + `scripts/eval_shop_matcher.py` + `python -m ml.shop_matcher evaluate`
- `ml/shop_matcher/matcher.py` — baseline renamed `FuzzyShopMatcher` (QA compare)
- Artifact `data/models/shop_matcher.joblib` (v2 + TF-IDF vectorizer)
- QA sample `data/seeds/shop_matcher_qa_sample.json`
- Thin call site: `crawlers/marketplace/shop_finder.py` (`match_source=hybrid_threshold`)
- Tests: `tests/shop_matcher/` regression + gate
- `requirements.txt`: `sentence-transformers==3.3.1`

**Not touched:** scrapers (`shopee.py` / `tiktok.py` / …), product categorizer, ML Lab / anomaly / narrative / monitoring, `docs/plan.md`.

### Behavior

| Path | Result |
|------|--------|
| Strong fuzzy ≥ 0.90 | return fuzzy (skip embed — fast discovery) |
| Short prefix `rd_`/`dq_`/`hpg_`/… + matching brand | boost 0.72 |
| Mid-band fuzzy + vector | fuse / rescue near-miss |
| Threshold | **0.65** (CONTEXT) |

Default embedder backend at call sites: **tfidf** (offline). Train/eval CLI: `--backend auto|sentence_transformers|tfidf`.

### QA gate report (sample n=22)

From `PYTHONPATH=. python3 scripts/eval_shop_matcher.py --backend tfidf`:

| Metric | Fuzzy v1 | Hybrid v2 | Δ |
|--------|----------|-----------|---|
| precision | **1.0** (tp=10, fp=0) | **1.0** (tp=13, fp=0) | 0 |
| recall | 0.7143 (fn=4) | **0.9286** (fn=1) | +0.2143 |
| f1 | 0.8333 | **0.963** | +0.1297 |
| gate_pass | — | **true** | |

Rescued hard positives (fuzzy miss → hybrid hit): `rd_lighting_bulb_store` (RAL), `dq_lighting_vn` (DQC), `hpg_steel_official` (HPG). Remaining FN: `led_chieusang_congnghiep` (semantic lighting paraphrase — ST path can help further offline).

---

## Testing results

| # | Command | Result |
|---|---------|--------|
| 1 | `python -c "from rapidfuzz import fuzz; from sentence_transformers import SentenceTransformer; print('ok')"` | ok |
| 2 | `PYTHONPATH=. pytest -q tests/shop_matcher/` | **50 passed** |
| 3 | `PYTHONPATH=. python3 scripts/eval_shop_matcher.py --backend tfidf` | gate_pass true; F1 0.833→0.963 |

---

## Limits / next

- Runtime default TF-IDF (not Hub download on every `ShopMatcher()`); use `--backend auto` / `sentence_transformers` when training with MiniLM for stronger semantic rescue.
- Remaining hard FN `led_chieusang_congnghiep` — candidate for ST mid-band tuning in a follow-up.
- Discovery still gated by Task #36 flag + allowlist; matcher only scores.
