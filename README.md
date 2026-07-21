# Manufacturing Data Economy Platform

[![CI](https://github.com/thanhhale288/data-economy/actions/workflows/ci.yml/badge.svg)](https://github.com/thanhhale288/data-economy/actions/workflows/ci.yml)

Hệ thống web phân tích kinh tế số ngành **Công nghiệp chế biến, chế tạo** (VSIC Section C).

**Docs:** [CONTEXT.md](./CONTEXT.md) · [AGENTS.md](./AGENTS.md) · [Proposal v2](./docs/proposal-v2.md) · [ADR](./docs/adr/) · [Plan](./docs/plan.md) · [Ops / Demo](./docs/ops-demo.md)

## Tính năng

- **Dashboard**: IIP, heatmap đóng góp KTS, so sánh OECD vs GSO
- **Doanh nghiệp**: mẫu niêm yết ~25–30 DN (seed + peer clustering VSIC; case Rạng Đông…)
- **Pipeline**: Crawl GSO/OECD/companies/marketplace tự động
- **ML Lab**: ARIMA, XGBoost, LSTM dự báo IIP
- **Benchmark**: So sánh hiệu quả DN vs ngành (SingStat BITE style)

## Quick Start

```bash
# 1. Cài dependencies Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Postgres (khuyến nghị) — copy .env.example rồi bật Docker
cp .env.example .env
# DATABASE_URL=postgresql://mfg_economy:mfg_economy_pass@localhost:5432/mfg_economy
docker compose up -d db redis
# Redis optional cho hầu hết job; bỏ qua compose nếu dùng SQLite mặc định (không .env)

# 3. Migrate schema (Alembic) rồi seed
alembic upgrade head
PYTHONPATH=. python -m backend.app.seed

# 4. Phase 3 artifacts (đúng thứ tự scheduler: metrics → clean → features → train)
PYTHONPATH=. python -c "
from backend.app.database import SessionLocal
from pipeline.cleaning.digital_metrics import compute_all_digital_metrics
from pipeline.cleaning.run_cleaning import run_data_cleaning
from pipeline.features.engineering import run_feature_engineering
from ml.models.trainer import train_all_models
db = SessionLocal()
print('Metrics:', compute_all_digital_metrics(db))
print('Cleaning:', run_data_cleaning(db))
print('Features:', run_feature_engineering(db))
print('ML:', train_all_models(db))
db.close()
"
# Expect: data/processed/cleaned_macro.parquet, features.parquet (+ features_manifest.json), data/models/*

# 5. Chạy backend
PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000

# 6. Chạy frontend (terminal khác)
cd frontend && npm install && npm run dev
```

Hoặc một lệnh bootstrap (bước 2–4):

```bash
make bootstrap   # hoặc: ./scripts/bootstrap.sh
make api         # terminal 1
make fe          # terminal 2
```

Hoặc chạy toàn bộ bằng Docker:

```bash
docker compose up --build
```

- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Ops (demo)

- **Online:** seed/crawl cần HTTP (NSO/GSO, OECD, CafeF). Khi nguồn lỗi: ghi status/fallback — không bịa số.
- **Offline:** dùng `data/raw/` + fixtures; UI phải hiện fallback/unavailable, không im lặng.
- **Worker:** `PYTHONPATH=. python -m pipeline.dags.scheduler` (crawl nightly + Phase 3 chain).
- **Smoke (API up):** `make api` then `make smoke` — not one-shot with bootstrap. Offline E2E: `make e2e`. UI: manual pass — `.scratch/demo-smoke-checklist.md`.
- **Nhánh:** nếu PR Phase 3–4 (#5…#11) chưa vào `main`, checkout/merge đúng tip trước khi demo — xem [docs/ops-demo.md](./docs/ops-demo.md).

## Cấu trúc

```
backend/     FastAPI + SQLAlchemy
crawlers/    GSO, OECD, companies, marketplace
pipeline/    Cleaning, features, scheduler
ml/          ARIMA, XGBoost, LSTM
frontend/    React dashboard
data/        VSIC mappings, company seeds
docs/        Proposal v2 · ops-demo.md
scripts/     bootstrap.sh
```
