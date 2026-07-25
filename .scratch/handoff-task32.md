# Handoff — Task #32 CafeF live → BCTC thật

**Status:** DONE (pushed; mở PR trên GitHub)  
**Branch:** `cursor/epic3-phase2-task32-cafef-live-bctc` (base: `origin/main` @ `39b3ce9`)  
**Date:** 2026-07-25  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** `6b481d9` · PR: https://github.com/thanhhale288/data-economy/pull/new/cursor/epic3-phase2-task32-cafef-live-bctc

---

## Delivered

- Batch enrich: `scripts/enrich_bctc_cafef.py` + `crawlers/financial/batch_enrich.py`
- Report: `.scratch/epic3-task32-cafef-bctc-report.md` (+ `.csv`)
- Live smoke allowlist **28/28 `cafef_ok`**; persist DB: 28 tickers có quarterly CafeF `source_url`
- API: `FinancialReportOut.source_url`; UI Company detail: nhãn nguồn `cafef|seed|fallback|live`
- Seed annual ghi `source_url=seed:companies.json` (re-seed để gắn nhãn row annual cũ còn `null`)
- Ops: `docs/ops-demo.md` § CafeF BCTC enrich
- Tests mock: `tests/financial/test_epic3_cafef_enrich.py`
- `docs/plan.md` Task #32 checked

### Live result (2026-07-25)

| Metric | Value |
|--------|-------|
| Tickers | 28 |
| `cafef_ok` | 28 |
| `fallback` / `error` | 0 |
| Persist | True (Postgres demo DB) |
| Quarterly `employees` | all null (không lấp seed) |

CafeF redirects `s.cafef.vn/{T}/…` → `cafef.vn/du-lieu/{t}/…` (httpx follow). HOSE/PDF/XBRL **không** cần cho đóng #32.

---

## Task review — #32 CafeF live BCTC

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task32-cafef-live-bctc` · tip local uncommitted · PR chưa mở

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Smoke CafeF full allowlist ~28 | done | 28/28 `cafef_ok` |
| Bảng ticker→status/detail/period/source_url | done | `.scratch/epic3-task32-cafef-bctc-report.{md,csv}` |
| Upsert khi parse OK + `source_url` CafeF | done | quarterly rows; key `(company_id, period, report_type)` |
| Field thiếu = null, không backfill seed | done | employees null trên CafeF; annual seed tách key |
| Ops một lệnh | done | `PYTHONPATH=. python scripts/enrich_bctc_cafef.py` |
| UI/API phân biệt nguồn | done | schema + Company detail “Nguồn: cafef\|…” |
| Tests mock OK + fail→fallback | done | `test_epic3_cafef_enrich.py` |
| Không invent / không đổi Digital VA | done | |

Deliverable chính:
- Batch CafeF enrich + report + persist thật 28 ticker
- Provenance API/UI + mock tests

### Làm thế nào
- Waves: W1 explore (2 subagents) → W2 implement → W3 verify + live smoke → W4 handoff (no commit)
- Entrypoint sẵn: `fetch_bctc` → `fetch_cafef_bctc`; thêm batch + report
- Trade-off: CafeF = quarterly; seed annual giữ song song (benchmark vẫn ưu tiên annual đủ field)
- Không migration: `source_url` đã có trên model

### Còn lại / rủi ro (không làm trong chat này)
- Annual rows cũ trong DB vẫn `source_url=null` cho đến khi `python -m backend.app.seed`
- DGC/BFC có thể có >1 quarterly CafeF period trong DB demo (lịch sử) — không hại AC
- Task #33+ (website QA, listing, marketplace strategy…) — ngoài phạm vi

---

## Testing results — Task #32

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: mock đường CafeF/fallback chắc; live mạng chứng minh 28/28 parse OK và persist được

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. pytest -q tests/financial/ tests/companies/test_listed_companies.py` | mock + listed | **24 passed** | gồm test mới Task #32 |
| 2 | `PYTHONPATH=. pytest -q tests/financial/test_epic3_cafef_enrich.py tests/financial/test_epic3_bctc_parity.py` | recheck | **8 passed** | |
| 3 | `PYTHONPATH=. python scripts/enrich_bctc_cafef.py --dry-run` | live HTTP | **28 cafef_ok** | không DB |
| 4 | `PYTHONPATH=. python scripts/enrich_bctc_cafef.py` | live + persist | **28 cafef_ok, persisted=True** | Postgres |

### Failures
- Không

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | User chưa yêu cầu | Khi ship |
| FE `npm run build` | Đổi JSX nhỏ (source label) | Optional |

---

## Do not reopen
- Không làm #33–#39 trong chat Task #32
- Không invent GMV / đổi Digital VA
- Không bắt buộc HOSE/XBRL nếu CafeF đủ (đã đủ)

## Next
**Task #33 — Batch website detector + audit marketplace URL**

Base: tip Task #32 branch (hoặc merge #32 → main trước nếu user ship).

---

## Paste prompt (chat sau)

```text
# Task
Tiếp tục **Epic 3 Phase 2**. Chat này chỉ làm **Task #33 — Batch website detector + audit marketplace URL**. STOP sau #33; không làm #34–#39.

Đang chạy theo lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user yêu cầu).

## Context
Repo: `/Users/hale/Code/AI in Data Economy`

Đọc bắt buộc:
- `.scratch/handoff-task32.md` (Task #32 DONE — CafeF 28/28 live)
- `.scratch/handoff-epic3-phase1-data.md`
- `.scratch/epic3-phase2-plan.md` § Task #33
- `docs/plan.md` § Epic 3 Phase 2
- `CONTEXT.md`, `AGENTS.md`

**Phase 2 thứ tự:** #32 DONE → **#33** → #34 → …

## Git / branch
1. Base: tip `cursor/epic3-phase2-task32-cafef-live-bctc` (merge/PR #32 nếu user đã ship) hoặc Phase 1 tip nếu #32 chưa merge.
2. Branch: `cursor/epic3-phase2-task33-batch-website-qa`
3. Không commit/push trừ khi user Explicit yêu cầu.

## Task #33 — Yêu cầu

Mục tiêu: một job/script chạy mọi ticker seed → website detector + liệt kê marketplace DP URLs; báo cáo CSV/MD; sửa seed/DB khi mismatch; không đoán checkout khi 403/timeout.

### Functional
- Job/script: full allowlist ~28 → website detector + list shopee/tiktok/lazada URLs từ seed/DP.
- Báo cáo: `stock_code, website_ok, has_checkout, shopee_url, tiktok_url, flag_vs_url_mismatch` (CSV/MD dưới `.scratch/` hoặc `data/processed/`).
- Sửa seed/DB khi mismatch rõ; 0 flag marketplace=true thiếu URL.
- Doc: “chỗ xem URL” = seed + report + Company detail; dòng ops trong `docs/ops-demo.md`.

### Honesty
- Không invent checkout khi HTTP fail/block.
- Không invent GSO/OECD/CafeF/GMV; không đổi Digital VA.

### Tests
- Consistency: flag marketplace ⇒ phải có URL (giữ/ mở rộng tests Epic 3 digital honesty).
- Mock detector fail → không ghi checkout=true bịa.

## Constraints
- Một chat = Task #33 only.
- Không listing depth (#34), không ADR marketplace live strategy (#35), không CafeF lại (#32).

## Waves / Subagents

### W1 — Explore (1–2 subagent song song)
- **A:** `crawlers/companies/website_detector.py`, `listed_companies.py`, seed digital_channels/digital_presence.
- **B:** Tests `tests/companies/test_epic3_digital_honesty.py` + chỗ UI hiện URL.

Deliverable: map “chỗ xem URL” + gap list cho batch report.

### W2 — Implement
- Script batch QA + report artifact
- Fix seed/DB mismatches nếu phát hiện
- Ops one-liner + tests

### W3 — Verify
```bash
PYTHONPATH=. pytest -q tests/companies/
# + digital honesty / related
```

### W4 — Ship
Handoff `.scratch/handoff-task33.md` + Task review + Testing results + prompt #34 (có Waves) → STOP.
Không commit trừ khi user bảo.
```
