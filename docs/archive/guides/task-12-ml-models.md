# Task 12 — Script hướng dẫn: ML models (IIP forecast)

Thực hiện theo thứ tự. Mỗi bước có lệnh kiểm chứng. Chi tiết handoff: `.scratch/handoff-task12.md`.

## Mục tiêu nghiệm thu

- [ ] Ba tầng model chạy được trên data thật (không invent series): **ARIMA/SARIMAX**, **XGBoost hoặc LightGBM**, **LSTM**
- [ ] Target: GSO **IIP_C** (tháng); features từ Task #11 (`build_features` / `features.parquet`)
- [ ] Metrics: **MAE, RMSE, MAPE** (dùng `ml/evaluation/`); ưu tiên **walk-forward** (plan: train ~đến 2023, test 2024+ khi đủ dữ liệu)
- [ ] Artifact dưới `data/models/` + ghi **model registry** / predictions (schema sẵn trong DB)
- [ ] API endpoints đọc được metrics/forecast (đủ cho Module 4 sau); không bịa số báo cáo
- [ ] Tests không phụ thuộc mạng; không commit binary model lớn nếu `.gitignore` cấm

---

## Bước 0 — Chuẩn bị

```bash
cd "/Users/hale/Code/AI in Data Economy"
git fetch origin && git checkout cursor/phase3-clean-features-ml && git pull
source .venv/bin/activate
PYTHONPATH=. python3 -c "import pandas as pd; df=pd.read_parquet('data/processed/features.parquet'); print(df.shape, list(df.columns)[:12], '...')"
cat data/processed/features_manifest.json
```

Nếu thiếu digital/financial: chạy `compute_all_digital_metrics` rồi `run_feature_engineering` (xem handoff #11).  
Nếu thiếu `mei_ip`: OECD crawl peer EA20 — **không bịa**.

---

## Bước 1 — Đọc scaffold hiện có

**Files:** `ml/models/trainer.py`, `ml/evaluation/metrics.py`, `backend.app.models.ModelRegistry` / `ModelPrediction`, API ML nếu có.

**Việc làm:** liệt kê chỗ đang “giả ARIMA” (EMA), split holdout cố định, LSTM epochs ngắn — thay bằng pipeline thật, giữ API `train_all_models(db)` tương thích scheduler.

---

## Bước 2 — ARIMA / SARIMAX

- Fit trên chuỗi IIP (từ features hoặc GSO); exogenous tùy chọn: `indigo` / `mei_ip` lags **nếu có cột**.
- Không dùng `mei_bci`.
- Walk-forward hoặc expanding window; lưu model + metrics.

```bash
PYTHONPATH=. python3 -c "
from backend.app.database import SessionLocal
from ml.models.trainer import train_arima
db = SessionLocal(); print(train_arima(db)); db.close()
"
```

---

## Bước 3 — XGBoost / LightGBM

- Tabular: mọi cột numeric trừ `period` / target; **loại** cột string provenance (`digital_alignment`, `financial_alignment`) khỏi X.
- Cẩn thận leakage: không đưa future vào feature; lag đã có từ #11.
- Feature importance optional (hữu ích Module 4).

---

## Bước 4 — LSTM

- Sequence trên IIP (± digital nếu có đủ lịch sử tháng thật; broadcast static OK nhưng document).
- Multi-step 3–6 tháng nếu kịp; tối thiểu 1-step honest eval.
- Lưu `.pt` dưới `data/models/` (gitignore).

---

## Bước 5 — Registry + API

- `_register_model` / predictions đã có skeleton — đảm bảo idempotent update.
- Endpoint(s) trả metrics + forecast vs actual (không hard-code số đẹp).

---

## Bước 6 — Tests + scheduler

```bash
PYTHONPATH=. pytest tests/ -q -k 'ml or trainer or evaluation' --tb=short
# hoặc thêm tests/ml/ mới
```

Xác nhận job `ml_training` trong `pipeline/dags/scheduler.py` vẫn gọi `train_all_models` sau `feature_engineering`.

---

## Non-goals

- Không sửa Digital VA / VDEI.
- Không viết lại cleaning/feature eng trừ bug.
- Không làm dashboard Phase 4 trong task này.
- Không invent GSO/OECD/CafeF numbers hoặc metrics giả.

---

## Acceptance checklist (tick khi xong)

- [ ] Ba model train + eval có metrics thật trên holdout/walk-forward
- [ ] Registry + predictions trong DB (hoặc artifact + API đọc được)
- [ ] Tests xanh; scheduler path OK
- [ ] `docs/plan.md` GĐ3 Task #12 đánh dấu `[x]` + commit/PR khi user yêu cầu
