# Handoff — Task #39 Scale architecture (toàn Section C)

**Status:** DONE (uncommitted — commit/PR when user asks)  
**Branch:** `cursor/epic3-phase2-task39-scale-architecture`  
**Date:** 2026-07-26  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** _(pending user request)_  
**Base:** `main` @ `f4f5022` (Task #38 PR #25 merged)

---

## Delivered

- **Three-tier architecture** documented: macro ngành · universe (shallow) · deep listed sample
- **ADR-0003** — scale policy; no nationwide crawl; no DB migration until identity key sourced
- **`docs/economy-knowledge.md` §6.0** + diagram §1.3; `CONTEXT.md` + `docs/knowledge.md` terms
- **Stub:** `data/raw/company_universe/rows.json` = `[]` + PROVENANCE; Pydantic contract + `universe_service`
- **Honesty:** Digital VA / percentiles = `prototype_listed_sample`; auto-promote always forbidden
- **Plans:** `docs/plan.md` + `.scratch/epic3-phase2-plan.md` mark #39 DONE with limits

### Not done (out of scope)

- National firm crawl / invent BCTC/GMV
- Alembic `company_universe` table (deferred — identity key unresolved)
- Tasks #40–#43

---

## Task review — #39 Scale architecture (toàn Section C)

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task39-scale-architecture` · uncommitted on `f4f5022` · PR pending

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Tài liệu + optional schema/stub universe | done | economy-knowledge §6.0, ADR-0003, empty rows stub + Pydantic |
| `docs/plan.md` / phase2 plan ghi rõ giới hạn | done | #39 checked; limits in phase2 plan |
| Không crawl toàn quốc / invent trăm BCTC | done | rows=`[]`; no crawler; auto-promote=False |

Deliverable chính:
- ADR-0003 + universe stub contract; scale path without fake national coverage

### Làm thế nào
- Waves: W1 explore (2 subagents) → W2 docs+ADR+stub+tests → W3 pytest → W4 handoff (no commit)
- Subagents: [Explore seed/company schema](7a4fcff8-b273-4cdb-b049-0abaa9692036), [Explore Section C scale gaps](49169905-233e-4f5c-9648-786bbc4e447f)
- File chính: `docs/adr/0003-*.md`, `docs/economy-knowledge.md`, `backend/app/schemas/universe.py`, `data/raw/company_universe/`
- Trade-off: **migration-free stub** (Pydantic + empty JSON) thay vì Alembic sớm — tránh khóa PK khi chưa có nguồn đăng ký/thống kê
- So với plan: đúng #39 AC; không đụng #40–#43

### Còn lại / rủi ro (đã ghi plan để xử lý sau)
- Website domain fix — **Task #40**
- GMV backfill — **#41**
- Cookie/partner — **#42**
- Discovery crawl — **#43**
- Later: sourced universe adapter + optional DB table once identity key known

---

## Testing results — Task #39

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: stub + docs consistent; seed deep sample untouched; universe empty by design

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. pytest -q tests/ -k "company or seed or vsic or universe" --maxfail=20` | company/seed/vsic/universe | **61 passed**, 252 deselected | includes 7 new universe stub tests |

### Failures
- None

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | User chưa yêu cầu | Khi ship |
| Nationwide ingest smoke | Ngoài AC #39 | Khi có nguồn + adapter |
| Alembic universe table | Deferred ADR-0003 | Khi chốt identity key |

---

## Do not reopen
- Không làm #40–#43 trong chat Task #39
- Không invent / copy-seed vào `company_universe`
- Không đổi Digital VA formulas
- Không crawl toàn quốc

## Next
**Task #40 — Sửa domain website seed (nợ từ audit #33)**

Base: tip Task #39 branch (hoặc merge #39 → main trước nếu user ship).

---

## Paste prompt (chat sau)

```text
# Task
Tiếp tục **Epic 3 Phase 2**. Chat này chỉ làm **Task #40 — Sửa domain website seed (nợ từ audit #33)**. STOP sau #40; không làm #41–#43.

Đang chạy theo lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user yêu cầu).

## Context
Repo: `/Users/hale/Code/AI in Data Economy`

Đọc bắt buộc:
- `.scratch/handoff-task39.md` (Task #39 DONE — scale architecture stub; universe rows=[])
- `.scratch/epic3-task33-website-url-audit.md` (bằng chứng 9 ticker fail)
- `.scratch/epic3-phase2-plan.md` § Task #40
- `docs/plan.md` § Epic 3 Phase 2
- `data/seeds/companies.json` (website_url + digital_presence.website)
- `CONTEXT.md`, `AGENTS.md`

**Phase 2 thứ tự:** #32–#39 DONE → **#40** → #41 → …

## Git / branch
1. Base: tip `cursor/epic3-phase2-task39-scale-architecture` (merge/PR #39 nếu user đã ship) hoặc tip `main` sau merge #39.
2. Branch: `cursor/epic3-phase2-task40-website-domain-fix`
3. Không commit/push trừ khi user Explicit yêu cầu.

## Task #40 — Yêu cầu

Mục tiêu: sửa / kết luận rõ 9 ticker `website_ok=false` từ audit #33 — **không** tắt SSL verify toàn cục; **không** suy checkout khi chưa fetch được.

### Tickers (từ audit)
| Ticker | Seed URL hiện tại | Lỗi |
|--------|-------------------|-----|
| IDI | idi.com.vn | DNS |
| SBT | ttcsugar.com.vn | DNS |
| NKG | namkimgroup.vn | timeout |
| POM | pomina-steel.com | SSL weak key |
| TLH | tienlensteel.com.vn | SSL issuer |
| GEE | gelexelectric.com.vn | self-signed |
| DPR | dpr.com.vn | self-signed |
| CSV | hcb.com.vn | SSL hostname |
| DCM | damcamau.vn | connection reset |

### Functional
1. Xác minh domain/URL công bố (HOSE/HNX / CafeF / site chính thức) → cập nhật seed `website_url` + `digital_presence.website.url` khi có URL đúng.
2. SSL yếu/self-signed: đổi URL đúng **hoặc** ghi nhận “không fetch được” hợp lệ; giữ `has_checkout=unknown` nếu chưa fetch OK.
3. Chạy lại `PYTHONPATH=. python scripts/audit_website_marketplace.py` và so `website_ok` trước/sau (cập nhật report trong `.scratch/`).

### Honesty
- Không invent checkout/GMV; không tắt SSL verify mặc định; không đổi Digital VA.

### AC
- Mỗi ticker trong bảng có kết luận: URL mới `website_ok=true` **hoặc** lý do vẫn fail có ghi nhận.
- Không ticker nào bị suy checkout khi chưa fetch được.

## Constraints
- Một chat = Task #40 only.
- Không GMV (#41), không cookie (#42), không discovery (#43), không scale universe ingest.

## Waves / Subagents

### W1 — Explore (1–2 subagent song song)
- **A:** seed fields + website_detector / audit script contract.
- **B:** evidence for correct domains (prior audit + public listing pages if reachable).

Deliverable: per-ticker plan (new URL vs keep-fail + reason).

### W2 — Implement
- Update seed + audit report; only real verified URLs.

### W3 — Verify
```bash
PYTHONPATH=. python scripts/audit_website_marketplace.py
PYTHONPATH=. pytest -q tests/ -k "website or company or seed" --maxfail=20
```

### W4 — Ship
Handoff `.scratch/handoff-task40.md` + Task review + Testing results + prompt #41 (có Waves) → STOP.
Không commit trừ khi user bảo.
```
