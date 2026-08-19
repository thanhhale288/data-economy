# Handoff — Task #74 Categorizer API + cột FE

**Status:** DONE  
**Branch:** `cursor/epic5-phase3-task74-categorizer-api-fe`  
**Date:** 2026-08-19  
**Phase:** Epic 5 Phase 5.3 (Marketplace NLP)  
**Base:** `origin/main` @ `3772afe`  
**PR:** (chưa push)

---

## Đã làm được gì

- `POST /api/ml/categorize` trên ML router hiện có (`/ml`). Body `{ "product_name" }`. Response `{ product_name, vsic_code, confidence, reason }`.
- Service mỏng `backend/app/services/product_categorizer_service.py` wrap `ProductCategorizer.predict()` — **không train** trong request. Artifact load một lần (`lru_cache` singleton). Whitelist Section C giữ nguyên.
- Abstain trung thực: `vsic_code` = null + `reason` (`empty_or_short_input`, `model_not_loaded`, `unknown_class`, …). Không bịa mã VSIC.
- CompanyDetail: cột **VSIC dự đoán** trên bảng listing. Có mã → text; abstain / API fail / thiếu tên → **—** với `title` = reason hoặc «chưa phân loại».
- `api.categorizeProduct(productName)` POST `/ml/categorize`. Fetch từng listing; AbortController khi unmount. Không ghi prediction vào DB.

Files:

- `backend/app/services/product_categorizer_service.py` — singleton + predict
- `backend/app/api/ml.py` — `POST /categorize`
- `backend/app/schemas/__init__.py` — `CategorizeRequest` / `CategorizeResponse`
- `tests/ml/test_categorize_api.py` — happy path + OOV/short/empty
- `frontend/src/api.js` — `categorizeProduct`
- `frontend/src/pages/CompanyDetail.jsx` — cột VSIC dự đoán

---

## Giải thích dễ hiểu

Classifier TF-IDF+LR đã có sẵn (offline). Task này **chỉ mở API + hiện cột** trên chi tiết doanh nghiệp.

- Tên sản phẩm khớp mẫu (ví dụ «Bóng LED Rạng Đông 9W») → mã VSIC 4 số Section C (2740 = thiết bị điện chiếu sáng).
- Tên lạ / ngắn / API lỗi → ô **—**, không bịa ngành. Tooltip nói vì sao (abstain reason) hoặc «chưa phân loại».

---

## Hạn chế

- Prediction **không** lưu DB — mỗi lần mở trang gọi lại API.
- Fetch từng listing (mẫu nhỏ); không batch endpoint.
- Chất lượng vẫn phụ thuộc nhãn seed + artifact `data/models/product_categorizer.joblib`. Không mở rộng nhãn (Task #75).
- Không sửa `ml/shop_matcher`, Digital VA, hay số marketplace.
- Không tick `docs/plan.md` / checklist Epic 5.

---

## Testing results

```bash
source /Users/hale/Code/AI in Data Economy/.venv/bin/activate
cd .worktrees/t74
PYTHONPATH=. pytest -q tests/product_categorizer/ tests/ml/ -k 'categor' --maxfail=20
# 12 passed, 57 deselected, 6 warnings in 4.20s
# (8 unit tests product_categorizer + 4 API tests)

cd frontend && npm run build
# vite v5.4.21 — ✓ built in 1.74s
```

API cases:

- `Bóng LED Rạng Đông 9W` → `vsic_code=2740`, `reason=null`
- `Vé máy bay nội địa` / junk → `vsic_code=null` + reason
- `""` / `"ab"` / whitespace → `empty_or_short_input`

Worktree không có `frontend/node_modules`; build dùng install của checkout gốc (không commit symlink).

---

## Hallmark

Component-scope trên CompanyDetail có sẵn: **không** redesign trang, **không** theme mới, **không** 8-state demo, **không** inline hex mới (Bar `#367ea2` giữ nguyên), **không** font mới. Cột dùng table hiện có + `.muted-text` + `title` tooltip.

---

## Do not reopen

- Không tick `docs/plan.md` / `.scratch/epic5-remain-plan.md` trong PR này.
- Không train model trong request.
- Không persist VSIC dự đoán.
- Không sửa shop_matcher / Digital VA formulas.
