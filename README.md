# Manufacturing Data Economy Platform

[![CI](https://github.com/thanhhale288/data-economy/actions/workflows/ci.yml/badge.svg)](https://github.com/thanhhale288/data-economy/actions/workflows/ci.yml)

Hệ thống web phân tích kinh tế số ngành **Công nghiệp chế biến, chế tạo** (VSIC Section C).

**Docs:** [CONTEXT.md](./CONTEXT.md) · [AGENTS.md](./AGENTS.md) · [Proposal v2](./docs/proposal-v2.md) · [ADR](./docs/adr/) · [Plan](./docs/plan.md)

## Tính năng

- **Dashboard**: IIP, heatmap đóng góp KTS, so sánh OECD vs GSO
- **Doanh nghiệp**: 10 DN niêm yết mẫu (Rạng Đông, Hòa Phát, Vinamilk...)
- **Pipeline**: Crawl GSO/OECD/companies/marketplace tự động
- **ML Lab**: ARIMA, XGBoost, LSTM dự báo IIP
- **Benchmark**: So sánh hiệu quả DN vs ngành (SingStat BITE style)

## Quick Start

```bash
# 1. Cài dependencies Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Khởi động PostgreSQL (Docker) — hoặc dùng SQLite mặc định trong .env.example
docker compose up -d db redis
# export DATABASE_URL=postgresql://mfg_economy:mfg_economy_pass@localhost:5432/mfg_economy

# 3. Migrate schema (Alembic) rồi seed
alembic upgrade head
PYTHONPATH=. python -m backend.app.seed

# 4. Chạy pipeline tính metrics + train models
PYTHONPATH=. python -c "
from backend.app.database import SessionLocal
from pipeline.cleaning.digital_metrics import compute_all_digital_metrics
from ml.models.trainer import train_all_models
db = SessionLocal()
print('Metrics:', compute_all_digital_metrics(db))
print('ML:', train_all_models(db))
db.close()
"

# 5. Chạy backend
PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000

# 6. Chạy frontend (terminal khác)
cd frontend && npm install && npm run dev
```

Hoặc chạy toàn bộ bằng Docker:

```bash
docker compose up --build
```

- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Cấu trúc

```
backend/     FastAPI + SQLAlchemy
crawlers/    GSO, OECD, companies, marketplace
pipeline/    Cleaning, features, scheduler
ml/          ARIMA, XGBoost, LSTM
frontend/    React dashboard
data/        VSIC mappings, company seeds
docs/        Proposal v2
```
