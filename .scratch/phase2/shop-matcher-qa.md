# Shop-matcher manual QA — 10 DN (Task 8)

**Branch:** `cursor/phase2-enterprise-digital`  
**Date:** 2026-07-18  
**Threshold:** **0.65** (CONTEXT.md)  
**Matcher:** `ml.shop_matcher.ShopMatcher`

## Policy

| Source | Linking rule |
|--------|----------------|
| Seed / known URL (`find_shops_for_company`) | Candidate from seed; **must** pass fuzzy `is_match` at ≥ **0.65**. Tag `match_source=seed_known_url` when linked. Below threshold → do not assign company. |
| Discovered non-seed shop (`evaluate_discovered_shop`) | Link **only** when `is_match` at ≥ 0.65; below threshold → do not assign company. |

HPG / GVR / DGC / REE / BWE have **no** marketplace seed shops — matcher must not invent links (discovery empty; wrong-pair scores stay below threshold).

## Per-DN summary

| Ticker | Company | Seed marketplace shops | Fuzzy score(s) | ≥ 0.65? | Notes |
|--------|---------|------------------------|----------------|---------|-------|
| RAL | CTCP Bóng đèn Rạng Đông | `rangdong_official` | 1.000 | Yes | Positive |
| HPG | Tập đoàn Hòa Phát | — | — | — | No seed shop; do not invent |
| VNM | CTCP Sữa Việt Nam | `vinamilk_official`, `@vinamilk` | 1.000, 1.000 | Yes | Brand alias Vinamilk |
| FPT | Tập đoàn FPT | `fpt_official` | 1.000 | Yes | Positive |
| GVR | Tập đoàn CN Cao su VN | — | — | — | No seed shop |
| DGC | CTCP Hóa chất Đức Giang | — | — | — | No seed shop |
| MSN | Tập đoàn Masan | `masan_consumer` | 1.000 | Yes | Positive |
| PNJ | CTCP Vàng bạc Đá quý Phú Nhuận | `pnj_official`, `@pnj` | 1.000, 1.000 | Yes | Brand alias PNJ |
| REE | CTCP Cơ điện lạnh | — | — | — | No seed shop |
| BWE | CTCP Nhựa Bình Minh | — | — | — | No seed shop |

## Labeled pair table (manual QA)

### True positives (seed positives — expect match)

| # | Ticker | Shop handle | Label | Score | Pred ≥0.65 | Correct? |
|---|--------|-------------|-------|-------|------------|----------|
| 1 | RAL | `rangdong_official` | positive | 1.000 | True | ✓ |
| 2 | VNM | `vinamilk_official` | positive | 1.000 | True | ✓ |
| 3 | VNM | `@vinamilk` | positive | 1.000 | True | ✓ |
| 4 | FPT | `fpt_official` | positive | 1.000 | True | ✓ |
| 5 | MSN | `masan_consumer` | positive | 1.000 | True | ✓ |
| 6 | PNJ | `pnj_official` | positive | 1.000 | True | ✓ |
| 7 | PNJ | `@pnj` | positive | 1.000 | True | ✓ |

### True negatives (wrong pairs — expect below threshold)

| # | Ticker | Shop handle (foreign) | Label | Score | Pred ≥0.65 | Correct? |
|---|--------|----------------------|-------|-------|------------|----------|
| 8 | HPG | `rangdong_official` | negative | 0.189 | False | ✓ |
| 9 | HPG | `vinamilk_official` | negative | 0.155 | False | ✓ |
| 10 | GVR | `vinamilk_official` | negative | 0.567 | False | ✓ |
| 11 | GVR | `rangdong_official` | negative | 0.318 | False | ✓ |
| 12 | DGC | `masan_consumer` | negative | 0.425 | False | ✓ |
| 13 | REE | `fpt_official` | negative | 0.425 | False | ✓ |
| 14 | BWE | `pnj_official` | negative | 0.425 | False | ✓ |
| 15 | MSN | `rangdong_official` | negative | 0.425 | False | ✓ |
| 16 | RAL | `fpt_official` | negative | 0.000 | False | ✓ |
| 17 | VNM | `masan_consumer` | negative | 0.533 | False | ✓ |
| 18 | FPT | `vinamilk_official` | negative | 0.000 | False | ✓ |
| 19 | PNJ | `rangdong_official` | negative | 0.346 | False | ✓ |

## Precision

On the 19 labeled pairs above:

| Metric | Value |
|--------|-------|
| TP | 7 |
| FP | 0 |
| TN | 12 |
| FN | 0 |
| **Precision** = TP / (TP+FP) | **100%** (> 90% target) |
| Recall = TP / (TP+FN) | 100% |

Cross-matrix check (7 seed shops × 10 DN = 70 cells): TP=7, FP=0, precision **100%** (see `tests/shop_matcher/test_matcher.py::test_cross_matrix_precision_over_90`).

## Note on brand-aligned non-seed handles

`HPG` ↔ `hoaphat_official` scores high (~1.0) because the brand aligns — that is correct matcher behaviour. Linking still requires a discovered URL; seed has none for HPG, so crawl does not invent a shop.
