# Handoff — Task #33 Batch website detector + audit marketplace URL

**Status:** DONE (shipping PR)  
**Branch:** `cursor/epic3-phase2-task33-batch-website-qa` (base: `origin/main` @ `e215763`)  
**Date:** 2026-07-25  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** _(điền sau push)_

---

## Delivered

- Batch audit: `scripts/audit_website_marketplace.py` + `crawlers/companies/website_audit.py`
- Report: `.scratch/epic3-task33-website-url-audit.{md,csv}`
- Live smoke allowlist **28**: `website_ok=19`, `website_fail=9` (checkout=`unknown` khi fail — không invent), `flag_url_mismatch=0`, `db_mismatch=0`
- DB fix: DQC thiếu Shopee DP → `added_shopee_url` via `--fix-db`
- Seed re-seed: `_upsert_digital_presence` upsert **mọi** channel (không chỉ website) — tránh drift sau này
- Ops: `docs/ops-demo.md` § Website + marketplace URL audit + “chỗ xem URL”
- Tests: `tests/companies/test_epic3_website_audit.py` + mở rộng digital honesty
- `docs/plan.md` Task #33 checked

### Live result (2026-07-25)

| Metric | Value |
|--------|-------|
| Tickers | 28 |
| `website_ok` | 19 |
| `website_fail` (checkout unknown) | 9 |
| `flag_url_mismatch` | 0 |
| `db_mismatch` (sau fix) | 0 |
| Marketplace URLs (shopee+tiktok) | 8 |

Fail honest (không đoán checkout): IDI, SBT (DNS), NKG (timeout), POM/TLH/GEE/DPR/CSV (SSL), DCM (reset).

---

## Task review — #33 Batch website + URL audit

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task33-batch-website-qa` · uncommitted · PR chưa mở

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Job full allowlist ~28 → detector + list marketplace URLs | done | CLI + library |
| Báo cáo CSV/MD cột yêu cầu | done | `.scratch/epic3-task33-website-url-audit.*` |
| Sửa seed/DB mismatch rõ | done | DQC Shopee; seed upsert all DP |
| 0 flag marketplace=true thiếu URL | done | seed + tests |
| Doc chỗ xem URL + ops one-liner | done | ops-demo |
| Không invent checkout khi HTTP fail | done | `has_checkout=None` + tests |
| Tests consistency + mock fail | done | honesty + website_audit |

Deliverable chính:
- Batch website QA + report + DB sync DQC
- Honesty path khi SSL/DNS/timeout

### Làm thế nào
- Waves: W1 explore (2 subagents) → W2 implement → W3 verify (pytest + live) → W4 handoff (no commit)
- Mirror Task #32 CLI/report pattern
- Trade-off: audit **không** ghi checkout khi fail (khác enrich_company keep-prior khi re-crawl); `--fix-db` chỉ sync URL từ seed + checkout khi live OK

### Còn lại / rủi ro (không làm trong chat này)
- 9 website fail (SSL/DNS/timeout) — **đã ghi thành Task #40** trong `docs/plan.md` + `.scratch/epic3-phase2-plan.md` § Task #40 (bảng ticker + lỗi + AC). Không chặn #34
- Task #34 listing depth — ngoài phạm vi
- Commit/PR khi user yêu cầu

---

## Testing results — Task #33

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: seed flag→URL sạch; mock fail không invent checkout; live 28 report + DQC DB fixed

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. pytest -q tests/companies/` (+ bctc parity) | unit | **44 passed** | gồm test mới #33 |
| 2 | `… audit_website_marketplace.py --no-detect --fix-db` | offline+DB | exit 0 | DQC `added_shopee_url` |
| 3 | `… audit_website_marketplace.py` | live HTTP | exit 0 | 19 ok / 9 fail unknown checkout |

### Failures
- Không

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | User chưa yêu cầu | Khi ship |
| FE build | Không đổi FE | Không |

---

## Do not reopen
- Không làm #34–#39 trong chat Task #33
- Không invent GMV / đổi Digital VA
- Không ép checkout=true trên ticker SSL/DNS fail

## Next
**Task #34 — Listing depth (không bịa GMV)**

Base: tip Task #33 branch (hoặc merge #33 → main trước nếu user ship).

---

## Paste prompt (chat sau)

```text
# Task
Tiếp tục **Epic 3 Phase 2**. Chat này chỉ làm **Task #34 — Listing depth (không bịa GMV)**. STOP sau #34; không làm #35–#39.

Đang chạy theo lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user yêu cầu).

## Context
Repo: `/Users/hale/Code/AI in Data Economy`

Đọc bắt buộc:
- `.scratch/handoff-task33.md` (Task #33 DONE — website URL audit 28; 0 flag mismatch)
- `.scratch/epic3-phase2-plan.md` § Task #34
- `.scratch/handoff-epic3-phase1-data.md`
- `docs/plan.md` § Epic 3 Phase 2
- `CONTEXT.md`, `AGENTS.md`

**Phase 2 thứ tự:** #32 DONE → #33 DONE → **#34** → #35 → …

## Git / branch
1. Base: tip `cursor/epic3-phase2-task33-batch-website-qa` (merge/PR #33 nếu user đã ship) hoặc tip #32 nếu #33 chưa có.
2. Branch: `cursor/epic3-phase2-task34-listing-depth`
3. Không commit/push trừ khi user Explicit yêu cầu.

## Task #34 — Yêu cầu

Mục tiêu: mở rộng listing depth **chỉ** khi có provenance (live scrape `source=live` cho allowlist shop, hoặc curation tay có PROVENANCE). Không bịa GMV cho peer B2B.

### Functional
- Chỉ thêm/cập nhật `marketplace_listings` khi (a) live scrape `source=live` cho shop trong allowlist, hoặc (b) curated seed có nguồn ghi rõ.
- DQC và peer có shop: ưu tiên live/curated; B2B giữ `[]` (không invent listing).
- Docs: tách rõ mẫu niêm yết (~28) vs mẫu có TMĐT (subset có shop/listing).
- Báo cáo ngắn trong `.scratch/` nếu có thay đổi listing counts trước/sau.

### Honesty
- Không invent GMV / units_sold / revenue_est khi không scrape/curate.
- Không đổi Digital VA formulas.
- Không silent invent để “đủ 10 DN có listing”.

### Tests
- Provenance: listing mới phải `source ∈ {live, seed, fallback}` đúng contract Epic 3.
- Peer B2B không shop → vẫn không có listing bịa.
- Giữ digital honesty / marketplace provenance tests.

## Constraints
- Một chat = Task #34 only.
- Không ADR marketplace live strategy (#35), không matcher gate (#36), không website QA lại (#33).

## Waves / Subagents

### W1 — Explore (1–2 subagent song song)
- **A:** `crawlers/marketplace/` (fetch/persist), seed `marketplace_listings`, DQC/RAL shop URLs từ Task #33 report.
- **B:** `tests/marketplace/` provenance + digital_metrics impact khi thêm listing.

Deliverable: map chỗ thêm listing an toàn + gap “bao nhiêu ticker có listing hôm nay”.

### W2 — Implement
- Live và/hoặc curated listing depth chỉ với provenance
- Docs mẫu niêm yết vs mẫu TMĐT
- Tests provenance

### W3 — Verify
```bash
PYTHONPATH=. pytest -q tests/marketplace/ tests/companies/test_epic3_digital_honesty.py
```

### W4 — Ship
Handoff `.scratch/handoff-task34.md` + Task review + Testing results + prompt #35 (có Waves) → STOP.
Không commit trừ khi user bảo.
```
