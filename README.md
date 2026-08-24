# Manufacturing Data Economy Platform

[![CI](https://github.com/thanhhale288/data-economy/actions/workflows/ci.yml/badge.svg)](https://github.com/thanhhale288/data-economy/actions/workflows/ci.yml)

Nền tảng đo **mức tham gia thương mại điện tử** của doanh nghiệp ngành chế biến, chế tạo Việt Nam (VSIC Section C) từ dữ liệu web — theo hướng thống kê thực nghiệm OBEC. Web demo tái sử dụng hạ tầng crawl + dashboard hiện có; macro GSO/OECD và 28 DN niêm yết phục vụ bối cảnh / case study.

> **Backlog hiện tại:** [`docs/evol-1.md`](./docs/evol-1.md) · **Proposal:** [`docs/proposal-v4.md`](./docs/proposal-v4.md)

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

## Stack

FastAPI + SQLAlchemy + PostgreSQL 16 · React + Vite + Recharts · httpx / Playwright crawlers · LLM local (open-weights) · Docker Compose + Redis.

## Cấu trúc repo

```
backend/      API, models, seed
crawlers/     gso/, oecd/, companies/, marketplace/
pipeline/     cleaning/, features/, dags/
ml/           shop_matcher, extraction helpers
frontend/     React dashboard → trang công bố chỉ tiêu
data/         mappings/, seeds/, raw/, models/
docs/         proposal-v4, evol-1, adr/, archive/
.scratch/     archive/ (handoff cũ)
```

## Docs (đọc theo nhu cầu)

| File | Dùng khi |
|------|----------|
| [`docs/evol-1.md`](./docs/evol-1.md) | Task đang làm (T01–T21) |
| [`docs/proposal-v4.md`](./docs/proposal-v4.md) | Thiết kế nghiên cứu + roadmap 14 tuần |
| [`docs/plan.md`](./docs/plan.md) | Mục lục ngắn → evol-1 / proposal-v4 |
| [`CONTEXT.md`](./CONTEXT.md) | Thuật ngữ domain (một phần đang cập nhật theo v4) |
| [`docs/adr/`](./docs/adr/) | Quyết định kiến trúc |
| [`AGENTS.md`](./AGENTS.md) | Quy tắc cho AI agent |
| [`docs/archive/`](./docs/archive/) | Lịch sử (proposal-v2, Epic 4/5 plan) |

Glossary người đọc: `docs/knowledge.md` (không dùng cho agent context).

## Quy tắc dữ liệu

- Crawl fail → **fallback có provenance**, không bịa số GSO/OECD/CafeF/marketplace.
- Chỉ tiêu TMĐT / pipeline đo → cập nhật `docs/proposal-v4.md` + ADR khi đổi thiết kế.
- Thêm DN → `data/seeds/companies.json` + `scripts/onboard_company.py`, không insert DB ad-hoc.
- Marketplace live: cache allowlist (ADR-0002); **không** cào listing sàn hàng loạt (proposal-v4).

## Trạng thái dự án

| Giai đoạn | Status |
|-----------|--------|
| Epic 1–5 (platform học kỳ) | Shipped — xem `docs/archive/plan-archive.md` |
| **Evol-1 → báo cáo 12/2026** | **Đang triển khai** — OBEC / thiết bị đo TMĐT |

## Dev / agent

- Branch/PR: 1 task = 1 branch = 1 PR — [`.cursor/skills/epic-phase-task-git/SKILL.md`](./.cursor/skills/epic-phase-task-git/SKILL.md)
- CI: `pytest` + frontend build (`.github/workflows/ci.yml`)
