# Handoff — Task #76 Shop matcher ST mid-band eval

**Status:** DONE
**Branch:** `cursor/epic5-phase3-task76-shop-matcher-st-eval`
**Date:** 2026-08-19
**Phase:** Epic 5 Phase 5.3 (Marketplace NLP)
**Base:** `origin/main` @ `5a30cce`
**PR:** (chưa push)

---

## Đã làm được gì

- Chạy eval **thật** (không persist joblib) cho fuzzy baseline, hybrid TF-IDF, hybrid sentence-transformers trên `data/seeds/shop_matcher_qa_sample.json` (n=22, threshold 0.65).
- Optional env `SHOP_MATCHER_BACKEND` (default **tfidf**) trong `HybridShopMatcher.__init__` qua `resolve_embedder_backend()`. Mọi `ShopMatcher()` runtime (`shop_finder`, pipeline cleaner) đọc env này; **không** bật ST production.
- Tests CI: default/invalid env → tfidf; explicit `embedder_backend="tfidf"` thắng env ST; **không** construct ST matcher (không download Hub).
- Không ghi `data/models/shop_matcher.joblib` bằng artifact ST. Không sửa scraper Shopee/TikTok. Không tick `docs/plan.md`.

Files:

- `ml/shop_matcher/hybrid.py` — `SHOP_MATCHER_BACKEND`, default tfidf
- `ml/shop_matcher/__init__.py` — export resolver
- `tests/shop_matcher/test_hybrid_v2.py` — env default / skip Hub
- `.scratch/handoff-task76.md` — bảng số eval

---

## Bảng so sánh (QA sample n=22, threshold 0.65)

Lệnh:

```
PYTHONPATH=. python3 scripts/eval_shop_matcher.py --backend tfidf --no-persist
PYTHONPATH=. python3 scripts/eval_shop_matcher.py --backend sentence_transformers --no-persist
```

ST dùng cache local MiniLM (`paraphrase-multilingual-MiniLM-L12-v2`); không commit model.

| Matcher | Precision | Recall | F1 | TP/FP/FN | `led_chieusang_congnghiep` (RAL, label=1) | Gate vs fuzzy |
|---------|-----------|--------|----|----------|-------------------------------------------|---------------|
| Fuzzy v1 | 1.0000 | 0.7143 | 0.8333 | 10 / 0 / 4 | **Không** (score 0.6375) | — |
| Hybrid TF-IDF | 1.0000 | 0.9286 | 0.9630 | 13 / 0 / 1 | **Không** (hybrid 0.6375, vector 0.3374) | **pass** (`gate_pass=true`) |
| Hybrid ST | 0.9333 | 1.0000 | 0.9655 | 14 / 1 / 0 | **Có** (hybrid 0.8088, vector 0.7426) | **fail** (`gate_pass=false`) |

ST **không** vượt gate: F1 nhỉnh hơn TF-IDF (0.9655 vs 0.9630) nhưng precision giảm và thêm 1 FP (`DQC` ↔ `led_chieusang_congnghiep`, hybrid 0.6775). Rescue FN lighting đi kèm FP cùng handle cho Điện Quang.

TF-IDF vẫn rescue 3 hard positives prefix: `rd_lighting_bulb_store`, `dq_lighting_vn`, `hpg_steel_official`. FN còn lại trên TF-IDF: `led_chieusang_congnghiep`.

**Runtime default vẫn tfidf.** User không bật ST production trong chat này; ST cũng không pass gate precision/FP nên không đổi default.

---

## Giải thích dễ hiểu

Matcher hiện tại: RapidFuzz + vector. CI/production dùng TF-IDF (offline). ST (MiniLM) hiểu paraphrase «chiếu sáng / LED» nên bắt được shop `led_chieusang_congnghiep` của Rạng Đông — nhưng cũng kéo Điện Quang lên trên ngưỡng 0.65 (false positive). Vì vậy không bật ST mặc định.

Muốn thử ST lúc runtime (ops local): `SHOP_MATCHER_BACKEND=sentence_transformers`. Unset / rỗng / giá trị lạ → tfidf.

---

## Hạn chế

- ST eval phụ thuộc model Hub (đã có cache máy local). CI **không** chạy eval ST và **không** download Hub.
- Artifact `data/models/shop_matcher.joblib` không bị overwrite (`--no-persist`).
- Discovery marketplace vẫn gated (flag + allowlist); matcher chỉ score.
- Không đổi Digital VA / VDEI / số GMV.

---

## Testing results

```
cd /Users/hale/Code/AI in Data Economy/.worktrees/t76
source /Users/hale/Code/AI in Data Economy/.venv/bin/activate
PYTHONPATH=. pytest -q tests/shop_matcher/
# 54 passed, 1 warning in 4.58s

PYTHONPATH=. python3 scripts/eval_shop_matcher.py --backend tfidf --no-persist
# backend=tfidf, gate_pass=true, hybrid F1=0.963

PYTHONPATH=. python3 scripts/eval_shop_matcher.py --backend sentence_transformers --no-persist
# backend=sentence_transformers, gate_pass=false, hybrid F1=0.9655
# rescued led_chieusang_congnghiep; FP DQC↔led_chieusang_congnghiep
```

CI default tests stay tfidf/offline (existing + 4 env tests; no ST `HybridShopMatcher()` construction).
