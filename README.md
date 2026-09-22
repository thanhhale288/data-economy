# Manufacturing Data Economy Platform

[![CI](https://github.com/thanhhale288/data-economy/actions/workflows/ci.yml/badge.svg)](https://github.com/thanhhale288/data-economy/actions/workflows/ci.yml)

Hệ thống đọc website doanh nghiệp ngành chế biến, chế tạo (VSIC Section C), ghi sáu đặc trưng bán trên môi trường số, đối chiếu với khảo sát % doanh thu online. Macro GSO/OECD và 28 DN niêm yết là bối cảnh / case study — không phải KPI báo cáo lab.

> **Nguồn sự thật:** [`docs/plan.md`](./docs/plan.md) — đang làm nốt bề nổi còn lại (form, khung nhãn, khớp MST, dàn ý). Không hoàn thiện nghiên cứu quốc gia; không sprint “xong tháng 12”.

## Chạy local (nhanh nhất)

```bash
cp .env.example .env
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Full stack (API + ML). Lean CI deps only: pip install -r requirements-ci.txt
# ML extras alone:        pip install -r requirements-ci.txt -r requirements-ml.txt

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
ml/           shop_matcher, extraction helpers, local_llm
frontend/     React dashboard
data/         mappings/, seeds/, raw/, models/
docs/         plan.md, adr/, archive/
.scratch/     archive/ (handoff cũ)
```

## Docs (đọc theo nhu cầu)

| File | Dùng khi |
|------|----------|
| [`docs/plan.md`](./docs/plan.md) | Nguồn sự thật: checklist bề nổi đang làm vs còn chặn |
| [`docs/lab/KHAO-SAT-DOANH-NGHIEP.md`](./docs/lab/KHAO-SAT-DOANH-NGHIEP.md) | Bộ câu hỏi form (bản thảo; chưa gửi DN) |
| [`docs/lab/DAN-Y-BAO-CAO.md`](./docs/lab/DAN-Y-BAO-CAO.md) | Dàn ý báo cáo (không phải bản 25 trang) |
| [`docs/lab/KHOP-FORM-WEB.md`](./docs/lab/KHOP-FORM-WEB.md) | Khớp form ↔ web + `DT × %` (fixture; chưa có phiếu thật) |
| [`CONTEXT.md`](./CONTEXT.md) | Thuật ngữ domain (Digital VA / IIP = demo cũ) |
| [`docs/adr/`](./docs/adr/) | Quyết định kiến trúc |
| [`AGENTS.md`](./AGENTS.md) | Quy tắc cho AI agent |
| [`docs/archive/`](./docs/archive/) | Proposal v2–v4, evol-1, Epic 1–5 |

Glossary người đọc: `docs/knowledge.md` (không dùng cho agent context).

## Quy tắc dữ liệu

- Crawl fail → **fallback có provenance**, không bịa số GSO/OECD/CafeF/marketplace.
- Đổi thiết kế đo lường → cập nhật `docs/plan.md` + ADR khi cần.
- Thêm DN → `data/seeds/companies.json` + `scripts/onboard_company.py`, không insert DB ad-hoc.
- Marketplace live: cache allowlist (ADR-0002); **không** cào listing sàn hàng loạt.

## Trạng thái dự án

| Giai đoạn | Status |
|-----------|--------|
| Epic 1–5 (platform học kỳ) | Shipped — `docs/archive/plan-archive.md` |
| **Đề tài lab (GVHD)** | Đang làm bề nổi còn lại — [`docs/plan.md`](./docs/plan.md) |

## Dev / agent

- Branch/PR: 1 task = 1 branch = 1 PR — [`.cursor/skills/epic-phase-task-git/SKILL.md`](./.cursor/skills/epic-phase-task-git/SKILL.md)
- CI: `pytest` + frontend build (`.github/workflows/ci.yml`)
