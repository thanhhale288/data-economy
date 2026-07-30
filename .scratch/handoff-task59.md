# Handoff — Task #59 Product categorizer seed

**Status:** DONE  
**Branch:** `cursor/epic4-phase3-task59-product-categorizer`  
**Date:** 2026-07-30  
**Phase:** Epic 4 Phase 4.3 (Marketplace NLP)  
**Base:** `origin/main`  
**Embedding path for #60:** **không ship** — TF-IDF + LogisticRegression đủ precision gate trên labeled sample; `sentence-transformers` chưa pin vào `requirements.txt`.

---

## Delivered

- `ml/product_categorizer/` — offline classifier `product_name` → VSIC 4-digit (Section C whitelist)
- `data/seeds/product_categorizer_labels.json` — labeled sample (seed marketplace names + paraphrases + unknown/OOV)
- Artifact `data/models/product_categorizer.joblib`
- `scripts/eval_product_categorizer.py` — train + precision report
- Tests `tests/product_categorizer/` (happy + OOV/unknown abstain)

### Behavior

| Case | Result |
|------|--------|
| Confident VSIC in whitelist | `vsic_code` + confidence |
| Top class `__UNKNOWN__` | `null` + `reason=unknown_class` |
| Low confidence / tight margin | `null` + `low_confidence` / `ambiguous_margin` |
| Empty/short input | `null` + `empty_or_short_input` |
| Code outside whitelist | never returned |

Defaults: `confidence_threshold=0.22`, `margin_threshold=0.04`. Backend: `sklearn` TF-IDF (`char_wb` 3–5) + `LogisticRegression`.

### Precision report (test split)

From `PYTHONPATH=. python3 scripts/eval_product_categorizer.py`:

| Metric | Value |
|--------|-------|
| n (test) | 22 |
| precision | **1.0** (tp=17, fp=0) |
| recall_labeled | **1.0** (fn=0) |
| tn_abstain_correct (unknown OOV) | 5 |
| accuracy_including_abstain | 1.0 |
| embedding_path | **false** |

Train: 122 rows, 14 classes (13 VSIC 4-digit + `__UNKNOWN__`).

Note: MSN seed listing `Nước mắm Chin-su` labeled **1020** (chế biến thủy sản) — semantic product→VSIC, not company `vsic_code` 1071.

---

## Scope boundaries respected

- **Không sửa** `ml/shop_matcher/**`, crawlers, `ml/models/**`, frontend, DocAI, `docs/plan.md`
- **Không** thêm `sentence-transformers` (để #60 quyết định hybrid embedding)

---

## Giải thích dễ hiểu

### Đã làm được gì
- Đưa tên sản phẩm marketplace → mã ngành VSIC 4 số (Section C), hoặc bỏ trống nếu không chắc — không bịa mã.
- Có file nhãn nhỏ + báo cáo precision = 100% trên tập test.
- Chạy offline (train/infer), không cần API/FE.

### Hạn chế
- Sample nhỏ (seed + paraphrase); chưa gắn API marketplace.
- Chưa dùng embedding; #60 (shop matcher v2) sẽ cần `sentence-transformers` riêng.
- Ngưỡng tin cậy tối ưu trên sample này — production cần mở rộng nhãn.

---

## Testing results — Task #59

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: happy seed products đúng VSIC; OOV/unknown → null; precision test = 1.0; không đụng shop_matcher

### Lệnh đã chạy

| # | Command | Result |
|---|---------|--------|
| 1 | `python3 -c "import sklearn; print('ok')"` | **ok** (1.5.2) |
| 2 | `PYTHONPATH=. pytest -q tests/product_categorizer/` | **8 passed** |
| 3 | `PYTHONPATH=. python3 scripts/eval_product_categorizer.py` | precision **1.0**, embedding_path **false** |
