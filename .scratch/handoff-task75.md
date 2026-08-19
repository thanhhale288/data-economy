# Handoff — Task #75 Expand NLP labels / shop matcher QA

**Status:** DONE  
**Branch:** `cursor/epic5-phase3-task75-nlp-label-expand`  
**Date:** 2026-08-19  
**Phase:** Epic 5 Phase 5.3 (Marketplace NLP)  
**Base:** `origin/main` @ `f17bf4c`  
**Next:** Task #76 shop matcher ST eval (already in another wave) — remaining FN `led_chieusang_congnghiep`

---

## Delivered

| Piece | Path |
|-------|------|
| Categorizer labels | `data/seeds/product_categorizer_labels.json` (144 → **147**) |
| Shop matcher QA | `data/seeds/shop_matcher_qa_sample.json` (22 → **30**) |
| QA builder sync | `ml/shop_matcher/evaluate.py` `build_default_qa_rows()` |
| Test | `tests/product_categorizer/test_categorizer.py` live-cache provenance |
| Handoff | `.scratch/handoff-task75.md` |

Did **not** persist `data/models/product_categorizer.joblib` (eval used `--no-persist`). Thresholds unchanged: categorizer confidence **0.22** / margin **0.04**; matcher **0.65**. Runtime backend stays **tfidf**.

---

## Precision table (before → after)

Eval: `PYTHONPATH=. python3 scripts/eval_product_categorizer.py --no-persist`

| Metric | Before | After |
|--------|--------|-------|
| n_train | 122 | 123 |
| n_test | 22 | 24 |
| n_classes | 14 | 14 |
| confidence_threshold | 0.22 | 0.22 |
| margin_threshold | 0.04 | 0.04 |
| **precision** | **1.0** | **1.0** |
| recall_labeled | 1.0 | 1.0 |
| fp | 0 | 0 |
| fn | 0 | 0 |
| tn_abstain_correct | 5 | 5 |
| tp | 17 | 19 |
| abstain_rate | 0.227 | 0.208 |
| accuracy_including_abstain | 1.0 | 1.0 |

New test rows both TP at existing thresholds:

| product_name | truth | pred | confidence |
|--------------|-------|------|------------|
| Đèn bàn học LED (price only) | 2740 | 2740 | 0.449 |
| Sữa tươi Vinamilk 1L (TikTok) | 1050 | 1050 | 0.586 |

Honest 1.0: not obtained by lowering confidence/margin.

---

## New categorizer labels (provenance)

Only names already present in seed/fallback/live cache and **absent** from the labels file (normalized compare). VSIC = company seed `vsic_code` (Section C).

| product_name | vsic | split | source |
|--------------|------|-------|--------|
| Đèn bàn học LED (price only) | 2740 | test | `live_cache:RAL.shopee` (`RAL.shopee.json` item `name`) |
| Sữa tươi Vinamilk 1L (TikTok) | 1050 | test | `live_cache:VNM.tiktok` (`VNM.tiktok.json` product `title`) |
| Sữa chua uống probiotic (TikTok) | 1050 | train | `live_cache:VNM.tiktok` |

**Already labeled (skipped):** all 10 seed `marketplace_listings` and the matching fallback copies (`seed:RAL/DQC/VNM/FPT/MSN/PNJ`). Fallback file has **no extra product names** beyond those seed listings.

Live-cache PROVENANCE: demo snapshots (same shape as test fixtures); not a successful 2026 live scrape.

---

## Shop matcher QA (before → after)

Eval: `PYTHONPATH=. python3 scripts/eval_shop_matcher.py --backend tfidf --no-persist`

| Metric | Before (n=22) | After (n=30) |
|--------|----------------|--------------|
| threshold | 0.65 | 0.65 |
| backend | tfidf | tfidf |
| fuzzy precision / recall / f1 | 1.0 / 0.7143 / 0.8333 | 1.0 / 0.7143 / 0.8333 |
| **hybrid precision / recall / f1** | **1.0 / 0.9286 / 0.963** | **1.0 / 0.9286 / 0.963** |
| hybrid fp / fn | 0 / 1 | 0 / 1 |
| gate_pass | true | **true** |
| rescued (hybrid, not fuzzy) | 3 | 3 |

Added **8 seed_negative** pairs. Shop handles already in seed `digital_presence` URLs (`rangdong_official`, `vinamilk_official`, `@vinamilk`, `masan_consumer`, `pnj_official`, `@pnj`, `fpt_official`, `dienquang_officialstore`). No invented shop names.

New pairs are all TN (no extra FP). Gate did **not** drop: same threshold, hybrid still beats fuzzy on F1/recall with fp=0.

Remaining **FN** (unchanged, out of scope): RAL × `led_chieusang_congnghiep` (fuzzy 0.6375, hybrid 0.6375, below 0.65). Task #76 ST eval.

---

## Verify

```bash
cd "/Users/hale/Code/AI in Data Economy/.worktrees/t75"
source "/Users/hale/Code/AI in Data Economy/.venv/bin/activate"
PYTHONPATH=. python3 scripts/eval_product_categorizer.py --no-persist
PYTHONPATH=. python3 scripts/eval_shop_matcher.py --backend tfidf --no-persist
PYTHONPATH=. pytest -q tests/product_categorizer/ tests/shop_matcher/
# 63 passed
```

---

## Boundaries respected

- Did not invent GMV/units/shop names/product names
- Did not retrain-and-commit model binaries
- Did not change Shopee/TikTok scrapers
- Did not tick `docs/plan.md` / epic5 checklist
- Did not edit `frontend/src/pages/Benchmark.jsx`
- Did not change Digital VA / VDEI
- Did not lower categorizer or matcher thresholds

---

## Limits

- **Only 3 unlabeled listing titles** exist in the allowed sources. Seed + fallback product names were already in the label file (including DQC website bulbs).
- No extra listings in `data/raw/companies/` (BCTC fallback only). Live cache allowlist is RAL×shopee and VNM×tiktok only.
- Shop positives already covered every marketplace handle in seed `digital_presence`; expansion is seed-handle **negatives** only.
- Chin-su remains labeled `1020` (`seed:MSN+semantic`) — not retagged to MSN `1071`.
