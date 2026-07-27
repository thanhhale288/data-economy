# Handoff — Task #38 GRDP/VA (re-gate NSO)

**Status:** DONE (uncommitted — commit/PR when user asks)  
**Branch:** `cursor/epic3-phase2-task38-grdp-va-regate`  
**Date:** 2026-07-26  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** _(pending user request)_  
**Base:** `main` @ `f9755e5` (Task #37 PR #24 merged; branch rebased)

---

## Delivered

- **Decision: GO** — national manufacturing VA from NSO SDMX `GDPVNM.xml`
- **Wired into `gso_macro`:**
  - `VA_C` ← `NGDPVA_R_ISIC4_C_XDC` (constant 2010, billion VND)
  - `VA_C_NOMINAL` ← `NGDPVA_ISIC4_C_XDC` (current prices)
- Prefer `FREQ=Q`; expand to monthly via **step-hold**; `source=GSO|GSO_FALLBACK`
- Fallback: `data/raw/gso_va_fallback.csv` + PROVENANCE
- **Still deferred:** province × industry GRDP (no confirmed table ID)
- **Not done (out of scope):** dashboard chart for VA; ML features on VA; invent GRDP

### Live smoke (2026-07-26)

```text
fetch_gso_va() → status=ok
source_url=https://nsdp.nso.gov.vn/GSO-chung/SDMXFiles/GSO/GDPVNM.xml
402 records (VA_C=204, VA_C_NOMINAL=198), all source=GSO
```

---

## Task review — #38 GRDP/VA (re-gate NSO)

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task38-grdp-va-regate` · uncommitted on `f9755e5` base · PR pending

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Series thật trong `gso_macro` với `source=GSO\|GSO_FALLBACK` **hoặc** biên bản chưa có bảng | done | **Wired** VA quốc gia; GRDP tỉnh vẫn deferred (biên bản spike) |
| Không invent GRDP/VA; không silent fill IIP→VA | done | Mapping SDMX rõ; unmapped sectors skipped; tests |
| Tests khớp quyết định | done | `tests/gso/test_gdp_va_crawler.py` + filter suite |

Deliverable chính:
- `fetch_gso_va` + integrate `fetch_gso_macro`; docs/spike re-gate GO

### Làm thế nào
- Waves: W1 explore (2 subagents) → W2 crawl+docs+tests → W3 pytest + live smoke → W4 handoff (no commit)
- Subagents: [Explore GSO/IIP stack](f65ea82c-a2a5-432f-8918-9b7c2c9dc88e), [NSO GRDP/VA catalog](75e6bf40-ae7c-40f2-81e1-457f41a2cbac)
- File chính: `crawlers/gso/iip_crawler.py`, `data/raw/gso_va_fallback.csv`, `.scratch/epic3-task31-grdp-spike.md`
- Trade-off: wire **national VA** (usable M1) chứ không chờ GRDP tỉnh; dashboard vẫn IIP làm nhịp SX
- So với plan: đúng #38 AC; không đụng #39–#43

### Còn lại / rủi ro (đã ghi plan để xử lý sau)
- Scale architecture — **Task #39**
- Website domain — **#40**
- GMV cache — **#41**
- Cookie/partner — **#42**
- Discovery crawl — **#43**
- Optional later: dashboard/API surface for `VA_C`; province GRDP if NSO publishes table ID

---

## Testing results — Task #38

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: VA crawl wired; không invent; fallback sourced; live NSO OK

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. pytest -q tests/ -k "gso or grdp or macro or iip" --maxfail=20` | gso/macro/iip filter | **28 passed**, 278 deselected | includes new VA tests |
| 2 | `PYTHONPATH=. python -c '… fetch_gso_va() …'` | live NSO smoke | **status=ok**, 402 rows `source=GSO` | network |

### Failures
- None

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | User chưa yêu cầu | Khi ship |
| Dashboard VA chart | Ngoài AC #38 | Optional sau |
| Persist vào Postgres demo | Smoke parse-only; seed path đã gọi `fetch_gso_macro` | Ops seed khi cần |

---

## Do not reopen
- Không làm #39–#43 trong chat Task #38
- Không invent GRDP tỉnh
- Không gán IIP / Digital VA thành `VA_C`
- Không đổi Digital VA formulas

## Next
**Task #39 — Scale architecture (toàn Section C)**

Base: tip Task #38 branch (hoặc merge #38 → main trước nếu user ship).

---

## Paste prompt (chat sau)

```text
# Task
Tiếp tục **Epic 3 Phase 2**. Chat này chỉ làm **Task #39 — Scale architecture (toàn Section C)**. STOP sau #39; không làm #40–#43.

Đang chạy theo lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user yêu cầu).

## Context
Repo: `/Users/hale/Code/AI in Data Economy`

Đọc bắt buộc:
- `.scratch/handoff-task38.md` (Task #38 DONE — national VA wired; GRDP tỉnh deferred)
- `.scratch/epic3-phase2-plan.md` § Task #39
- `docs/plan.md` § Epic 3 Phase 2
- `docs/economy-knowledge.md`, `CONTEXT.md`, `AGENTS.md`
- Seed / company allowlist hiện tại (~28) vs “toàn Section C”

**Phase 2 thứ tự:** #32–#38 DONE → **#39** → #40 → …

## Git / branch
1. Base: tip `cursor/epic3-phase2-task38-grdp-va-regate` (merge/PR #38 nếu user đã ship) hoặc tip `main` sau merge #38.
2. Branch: `cursor/epic3-phase2-task39-scale-architecture`
3. Không commit/push trừ khi user Explicit yêu cầu.

## Task #39 — Yêu cầu

Mục tiêu: thiết kế + skeleton kiến trúc scale cho toàn VSIC Section C — **không** crawl cả nước / invent hàng trăm BCTC.

### Functional
1. Tách rõ: **vũ trụ DN** (đăng ký/thống kê/niêm yết) vs **mẫu sâu** (BCTC+digital) vs **macro ngành**.
2. Đặc tả ingest nông (VSIC, tên, website?) + queue lô + rate limit + provenance.
3. Ghi rõ: percentile / Digital VA trên mẫu niêm yết = **prototype**, không tuyên bố chuẩn quốc gia.
4. Doc trong `docs/economy-knowledge.md` + ADR ngắn nếu cần; optional schema/stub “universe”.

### Honesty
- Không invent hàng trăm BCTC / GMV / listing.
- Không scale bằng copy seed demo.

### AC
- Tài liệu + optional schema/stub universe.
- `docs/plan.md` / phase2 plan ghi rõ giới hạn.
- Không crawl toàn quốc trong task này.

## Constraints
- Một chat = Task #39 only.
- Không website domain (#40), không GMV (#41), không cookie (#42), không discovery crawl (#43).

## Waves / Subagents

### W1 — Explore (1–2 subagent song song)
- **A:** current seed/onboard/company schema + digital pipeline boundaries.
- **B:** gaps vs “toàn Section C” (universe sources candidates, rate limits, provenance).

Deliverable: file map + recommended doc/ADR outline + stub vs docs-only decision.

### W2 — Implement
- Docs (+ optional ADR/schema stub) theo AC; không invent data.

### W3 — Verify
```bash
# docs/ADR consistency; any new schema tests if stub added
PYTHONPATH=. pytest -q tests/ -k "company or seed or vsic" --maxfail=20
```

### W4 — Ship
Handoff `.scratch/handoff-task39.md` + Task review + Testing results + prompt #40 (có Waves) → STOP.
Không commit trừ khi user bảo.
```
