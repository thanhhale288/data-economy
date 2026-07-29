# Wave 3 / Task 8 — Shop-matcher report

**Branch:** `cursor/phase2-enterprise-digital`  
**Agent:** Subagent D  
**Date:** 2026-07-18  
**Blocked by:** Task 7 (done)

## 1. Checklist map (Task 8)

| Checklist item | Status |
|----------------|--------|
| Matcher shop name ↔ tên DN (fuzzy; threshold **0.65**) | **Done** — `ml/shop_matcher/ShopMatcher` |
| QA precision > 90% on 10 DN (manual table) | **Done** — 100% on 19 labeled pairs; see `shop-matcher-qa.md` |
| Only link when `is_match`; below threshold → no company | **Done** — `evaluate_discovered_shop`; seed short-circuits documented |
| Tests positive/negative pairs | **Done** — `tests/shop_matcher/` |
| `shop_finder` only calls matcher; scrape logic untouched | **Done** — no edits to `shopee.py` / `tiktok.py` / `common.py` |

## 2. Files changed

| Path | Action | Notes |
|------|--------|-------|
| `ml/shop_matcher/__init__.py` | **New** | Public exports |
| `ml/shop_matcher/matcher.py` | **New** | `ShopMatcher`, brand aliases, threshold 0.65, `train`/`load` |
| `crawlers/marketplace/shop_finder.py` | **Updated** | Removed class body; import from `ml.shop_matcher`; `evaluate_discovered_shop` |
| `tests/shop_matcher/**` | **New** | Positive/negative + precision + finder re-export |
| `.scratch/phase2/shop-matcher-qa.md` | **New** | Manual QA table |
| `.scratch/phase2/wave3-task8-report.md` | **New** | This file |
| `.scratch/phase2/checklist.md` | **Updated** | Task 8 tick |

**Not touched:** `crawlers/companies/**`, `crawlers/financial/**`, `shopee.py`, `tiktok.py`, `common.py`, `digital_metrics.py`, GSO/OECD, models, alembic, seed, pipeline, scheduler, requirements.

## 3. API

```python
from ml.shop_matcher import ShopMatcher, DEFAULT_THRESHOLD  # 0.65

m = ShopMatcher()
m.match_score(company_name, shop_name) -> float
m.is_match(company_name, shop_name, threshold=0.65) -> bool
m.match(company_name, shop_name) -> {"score": float, "is_match": bool}
```

`crawlers.marketplace.shop_finder.ShopMatcher` re-exports the same class (backwards compatible).

### Seed vs discovered

- **Seed known URL:** `find_shops_for_company` short-circuits `is_match=True` / `match_source=seed_known_url` (still stores `fuzzy_score`).
- **Discovered:** must go through `evaluate_discovered_shop` → returns `None` below 0.65.

## 4. Algorithm (brief)

1. Normalize VN diacritics (`đ→d`), strip legal/shop noise tokens.
2. Brand aliases for seed DN where legal name ≠ handle (Vinamilk, PNJ, Rạng Đông, …).
3. Strong score from brand/token containment in shop handle.
4. Else blended RapidFuzz (ratio / token_sort / partial) — **not** max(partial) alone (avoids GVR↔vinamilk false positives).

## 5. Tests

```bash
source .venv/bin/activate && PYTHONPATH=. python -m pytest tests/shop_matcher tests/marketplace -q
```

**Result:** `46 passed` (2026-07-18).

## 6. QA precision

See [shop-matcher-qa.md](./shop-matcher-qa.md).

- Labeled pairs: TP=7, FP=0, TN=12, FN=0 → **precision 100%** (target > 90%).
- Seed positives: RAL, VNM×2, FPT, MSN, PNJ×2 all ≥ 0.65.
- Negatives: HPG/GVR/DGC/REE/BWE wrong pairs all < 0.65; matcher does not invent shops for those tickers.

## 7. Shared-file proposals (main agent only)

1. None required for Task 8 — `rapidfuzz` / `joblib` already in requirements.
2. Optional later: persist `match_source` on `digital_presence` if schema allows (proposed only).

## 8. Handoff to Task 9

- Verified marketplace `digital_presence` rows remain seed-linked for RAL/VNM/FPT/MSN/PNJ.
- Fuzzy gate ready for any future discovery path via `evaluate_discovered_shop`.
- Digital metrics can sum listings for linked companies without changing Digital VA formula.
