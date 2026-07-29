# Manufacturing Data Economy Platform

[![CI](https://github.com/thanhhale288/data-economy/actions/workflows/ci.yml/badge.svg)](https://github.com/thanhhale288/data-economy/actions/workflows/ci.yml)

Web app phân tích **kinh tế số ngành chế biến, chế tạo Việt Nam** (VSIC Section C): macro GSO/OECD, mẫu DN niêm yết, kênh bán số / marketplace, dự báo IIP, và benchmark kiểu SingStat BITE.

> Mẫu DN sâu ≈ **28 ticker seed** — không phải toàn quốc Section C. UI có banner honesty (Epic 3). Công thức / thuật ngữ: [`CONTEXT.md`](./CONTEXT.md).

## Chạy local (nhanh nhất)

```bash
cp .env.example .env
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db redis
make bootstrap          # migrate + seed + metrics → clean → features → train
make api                # http://localhost:8000/docs
make fe                 # terminal khác → http://localhost:5173
```

Hoặc full Docker: `docker compose up --build`.

**Smoke:** `make api` rồi `make smoke`. E2E offline: `make e2e`.

## Modules

| Module | Nội dung |
|--------|----------|
| **Dashboard** | IIP, VA_C quốc gia, forecast overlay, heatmap VSIC, OECD peer vs GSO |
| **Doanh nghiệp** | Profile, kênh số, peers, narrative; case Rạng Đông (RAL) |
| **Pipeline** | Trạng thái crawl / clean / train + `source_health` |
| **ML Lab** | So sánh ARIMA · XGBoost · LSTM (MAE/RMSE/MAPE) |
| **Benchmark** | Form BITE → ROA/ROE/… + percentile peer VSIC; warnings tiếng Việt |

## Stack

FastAPI + SQLAlchemy + PostgreSQL 16 · React + Vite + Recharts · httpx / Playwright crawlers · statsmodels / XGBoost / PyTorch · Docker Compose + Redis.

## Cấu trúc repo

```
backend/      API, models, seed
crawlers/     gso/, oecd/, companies/, marketplace/
pipeline/     cleaning/, features/, dags/
ml/           models/, evaluation/, shop_matcher/
frontend/     React dashboard
data/         mappings/, seeds/, raw/ (fallback + provenance), models/
docs/         plan (hot), plan-archive, ADR, ops-demo, proposal-v2
.scratch/     handoff + Epic 4 plan (artifact cũ → archive/)
```

## Docs (đọc theo nhu cầu)

| File | Dùng khi |
|------|----------|
| [`CONTEXT.md`](./CONTEXT.md) | Thuật ngữ + công thức (nguồn domain) |
| [`docs/plan.md`](./docs/plan.md) | Tiến độ / task mở (hot) |
| [`docs/ops-demo.md`](./docs/ops-demo.md) | Demo, onboard DN, crawl ops |
| [`docs/proposal-v2.md`](./docs/proposal-v2.md) | Proposal Mục 4 |
| [`docs/adr/`](./docs/adr/) | Quyết định (OECD, marketplace live, scale) |
| [`AGENTS.md`](./AGENTS.md) | Quy tắc cho AI agent |
| [`.scratch/epic4-ai-ml-plan.md`](./.scratch/epic4-ai-ml-plan.md) | Roadmap Epic 4 (AI/ML/DL) |

Lịch sử checklist dài: [`docs/plan-archive.md`](./docs/plan-archive.md). Glossary người đọc: `docs/knowledge.md` (không dùng cho agent context).

## Quy tắc dữ liệu

- Crawl fail → **fallback có provenance**, không bịa số GSO/OECD/CafeF/marketplace.
- Digital VA / VDEI đổi → cập nhật `CONTEXT.md` (+ ADR nếu cần).
- Thêm DN → `data/seeds/companies.json` + `scripts/onboard_company.py`, không insert DB ad-hoc.
- Marketplace live có thể là **cache allowlist** (ADR-0002) khi HTTP bị chặn.
- GRDP tỉnh×ngành: **NO-GO** cho đến khi có table ID NSO — cấm copy `VA_C` quốc gia xuống tỉnh.

## Trạng thái dự án

| Epic | Status |
|------|--------|
| Phase 1–5 học kỳ + Epic 2–3 | DONE (một số item paused/deferred — xem plan) |
| **Epic 4 — AI / ML / DL** | Đang plan (DocAI Benchmark P0, anomaly, NLP, assist) |

## Dev / agent

- Branch/PR: 1 task = 1 branch = 1 PR — [`.cursor/skills/epic-phase-task-git/SKILL.md`](./.cursor/skills/epic-phase-task-git/SKILL.md)
- CI: `pytest` + frontend build (`.github/workflows/ci.yml`)
- Handoff hiện tại: `.scratch/handoff-task51.md`
