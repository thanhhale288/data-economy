# Handoff — Task #37 Industry-ratio (re-gate)

**Status:** DONE (no commit yet — wait for user)  
**Branch:** `cursor/epic3-phase2-task37-industry-ratio-regate`  
**Date:** 2026-07-26  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** _(none — user chưa yêu cầu commit/push)_  
**Base:** tip `cursor/epic3-phase2-task36-matcher-gate` @ `3a336fd` (PR #36 chưa merge `main`)

---

## Delivered

- **Decision: NO-GO** — keep `SOURCED_INDUSTRY_ECOMMERCE_RATIO = None`
- **Research re-gate:** `.scratch/epic3-task30-industry-ratio-research.md` § Task #37 (GSO digital VA % GDP, VECOM EBI 2025 Fig. 20 all-sector bins, MoIT B2C/retail, UNCTAD/OECD/WB — all rejected)
- **No** `data/mappings/` ratio file; **no** Digital VA formula change
- **Tests:** assert constant is `None`; missing listings → `0.0`; explicit `industry_ratio=` still works
- **Docs:** `CONTEXT.md`, `docs/knowledge.md`, `docs/ops-demo.md`, `docs/plan.md` #37 ✅, phase2 plan DONE

### Behavior unchanged

```text
no marketplace listings + SOURCED_INDUSTRY_ECOMMERCE_RATIO is None
  → online_revenue = 0.0 + log (not inventing)
```

---

## Task review — #37 Industry-ratio (re-gate)

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task37-industry-ratio-regate` · _(uncommitted)_ · —

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Constant set có citation **hoặc** đóng “vẫn None” + biên bản | done | **vẫn None** + research note § #37 |
| Không silent invent từ % KT số/GDP | done | GSO digital VA % GDP / e-commerce % digital VA rejected |
| Tests khớp quyết định | done | `SOURCED_… is None`; HPG → 0.0; explicit ratio path |

Deliverable chính:
- Biên bản re-gate NO-GO + tests khóa None

### Làm thế nào
- Waves: W1 explore (2 subagents) → W2 docs/tests (no wire) → W3 pytest → W4 handoff (no commit)
- Subagents: [Explore industry-ratio code](fcbe8cda-5518-4398-ace5-72a93799c81f), [Re-check ratio sources](f3443957-49a6-481b-92c1-18761c0072f0)
- File chính: `.scratch/epic3-task30-industry-ratio-research.md`, `pipeline/cleaning/digital_metrics.py` (comment only), tests
- Trade-off: VECOM Fig. 20 near-miss (bins &lt;15% for 58% firms) rejected — wiring 0.15 = recreating invent
- So với plan: đúng #37 AC “vẫn None”; không đụng #38–#42

### Còn lại / rủi ro (đã ghi plan để xử lý sau)
- GRDP/VA — **Task #38**
- Scale architecture — **#39**
- Website domain — **#40**
- GMV cache — **#41**
- Cookie/partner — **#42**
- Discovery crawl / fuzzy hygiene (nợ #36) — **#43** (phase2 plan)

---

## Testing results — Task #37

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: constant vẫn None; không silent invent; explicit ratio path còn sống

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. python -m pytest -q tests/companies/test_epic3_digital_honesty.py tests/pipeline/ -k "digital or ratio or online"` | honesty + pipeline filter | **7 passed**, 45 deselected | prompt W3 |
| 2 | `PYTHONPATH=. python -m pytest -q tests/companies/test_epic3_digital_honesty.py tests/pipeline/ -k "digital or ratio or online" tests/digital_metrics/test_metrics.py` | + digital_metrics unit | **23 passed**, 45 deselected | includes new None-guard tests |

### Failures
- None

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | User chưa yêu cầu | Khi user bảo ship |
| Wire mapping constant | NO-GO — no citation | Khi GSO/VECOM có CBCT revenue share |

---

## Do not reopen
- Không làm #38–#42 trong chat Task #37
- Không invent ratio / GMV
- Không silent enable từ GDP digital %
- Không đổi Digital VA formulas

## Next
**Task #38 — GRDP/VA (re-gate NSO)**

Base: tip Task #37 branch (hoặc merge #37 → main trước nếu user ship).

---

## Paste prompt (chat sau)

```text
# Task
Tiếp tục **Epic 3 Phase 2**. Chat này chỉ làm **Task #38 — GRDP/VA (re-gate NSO)**. STOP sau #38; không làm #39–#43.

Đang chạy theo lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user yêu cầu).

## Context
Repo: `/Users/hale/Code/AI in Data Economy`

Đọc bắt buộc:
- `.scratch/handoff-task37.md` (Task #37 DONE — industry-ratio vẫn None)
- `.scratch/epic3-phase2-plan.md` § Task #38
- `.scratch/epic3-task31-grdp-spike.md` (Phase 1 GRDP deferral)
- `docs/plan.md` § Epic 3 Phase 2
- `CONTEXT.md`, `AGENTS.md`
- GSO crawl / `gso_macro` models + existing IIP path

**Phase 2 thứ tự:** #32–#37 DONE → **#38** → #39 → …

## Git / branch
1. Base: tip `cursor/epic3-phase2-task37-industry-ratio-regate` (merge/PR #37 nếu user đã ship) hoặc tip `main` sau merge #37.
2. Branch: `cursor/epic3-phase2-task38-grdp-va-regate`
3. Không commit/push trừ khi user Explicit yêu cầu.

## Task #38 — Yêu cầu

Mục tiêu: xác nhận bảng PX-Web/SDMX cho GRDP/VA; implement crawl **chỉ** khi có ID+series; không thì giữ deferred + IIP stack.

### Functional
1. Re-check NSO/GSO table IDs for GRDP or manufacturing VA usable by the platform.
2. Nếu có ID+series: crawl → `gso_macro` với `source=GSO|GSO_FALLBACK` + provenance.
3. Nếu không: đóng task với biên bản “chưa có bảng” + giữ IIP path.

### Honesty
- Không invent GRDP/VA numbers.
- Không silent fill từ IIP giả làm VA.
- Fallback phải có nhãn nguồn rõ.

### AC
- Series thật trong `gso_macro` có `source=GSO|GSO_FALLBACK`, **hoặc** biên bản “chưa có bảng”.
- Tests: không invent; behavior khớp quyết định (wired hoặc still deferred).

## Constraints
- Một chat = Task #38 only.
- Không scale (#39), không website domain (#40), không GMV (#41), không cookie (#42), không discovery crawl (#43).

## Waves / Subagents

### W1 — Explore (1–2 subagent song song)
- **A:** current GSO crawl / `gso_macro` / IIP ingest + any GRDP stubs from Task #31.
- **B:** NSO PX-Web/SDMX catalog — table ID candidates for GRDP/VA (citation quality).

Deliverable: go/no-go + file map + table IDs (or “none”).

### W2 — Implement
- Crawl+persist **nếu** go; else update deferral docs/tests only.

### W3 — Verify
```bash
PYTHONPATH=. pytest -q tests/ -k "gso or grdp or macro or iip" --maxfail=20
```

### W4 — Ship
Handoff `.scratch/handoff-task38.md` + Task review + Testing results + prompt #39 (có Waves) → STOP.
Không commit trừ khi user bảo.
```
