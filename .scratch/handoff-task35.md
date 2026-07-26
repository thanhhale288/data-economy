# Handoff — Task #35 Chiến lược marketplace live

**Status:** DONE (uncommitted — chờ user commit/PR)  
**Branch:** `cursor/epic3-phase2-task35-marketplace-live-strategy` (base: tip Task #34 `6a79ee9`)  
**Date:** 2026-07-26  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** chưa — user chưa yêu cầu ship

---

## Delivered

- **ADR-0002** `docs/adr/0002-marketplace-live-strategy.md` — default allowlist+cache+badge; optional session cookie ops-only; partner API spike-only; reject anti-bot SaaS
- **Live cache module** `crawlers/marketplace/live_cache.py` + `data/raw/marketplace_live_cache/` (RAL×shopee, VNM×tiktok) + PROVENANCE + `.gitignore` exception
- **Crawl wire:** HTTP live → allowlisted cache (`live:cache:…` → `source=live`) → seed → fallback; `--prefer-cache` / `--no-cache` on enrich script
- **Optional ops cookies:** `SHOPEE_SESSION_COOKIE` / `TIKTOK_SESSION_COOKIE` → Cookie header
- **Badge:** Company detail cột Nguồn `live|seed|fallback`; crawl timeline `listing_source=…`
- **Docs:** ops-demo, plan #35 ✅, phase2 plan, knowledge, economy-knowledge, CONTEXT, strategy note + smoke report
- **Tests:** `tests/marketplace/test_epic3_live_cache.py` + updated block→seed tests

### Demo path (stable)

```bash
PYTHONPATH=. python scripts/enrich_marketplace_listings.py --prefer-cache --tickers RAL,VNM,FPT
# → live_ok=2 (RAL, VNM cache); FPT 403 → no invent
```

---

## Task review — #35 Marketplace live strategy

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task35-marketplace-live-strategy` · uncommitted · PR chưa mở

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Document quyết định ADR/`.scratch` | done | ADR-0002 + `.scratch/epic3-task35-marketplace-live-strategy.md` |
| Crawl contract không silent invent | done | block→cache only if allowlisted file; else seed/fallback; revenue = price×units only |
| ≥1 đường demo ổn định | done | prefer-cache RAL/VNM → `live_ok=2` offline/snapshot |
| Badge live\|seed\|fallback | done | CompanyDetail + listing_source in crawl detail |
| Không anti-bot SaaS mặc định | done | ADR Decision §4 |
| Không đổi Digital VA | done | không đụng formulas |

Deliverable chính:
- Chiến lược mặc định allowlist+cache; demo ổn định khi HTTP 403

### Làm thế nào
- Waves: W1 explore (2 subagents) → W2 ADR+cache+wire+FE badge+tests → W3 pytest + prefer-cache smoke → W4 handoff (no commit)
- Trade-off: cache snapshots = demo-shaped fixtures (cùng parse shape test fixtures), tagged `live:cache` — không claim “fetched this run”; Task #41 có thể refresh từ live thật sau

### Còn lại / rủi ro (đã ghi plan để xử lý sau)
- Matcher discovery gate — **Task #36**
- Website domain fix — **#40**
- GMV backfill DQC + **refresh live-cache từ capture thật** — **Task #41** (mở rộng sau #35)
- Session cookie ops smoke + partner API spike note — **Task #42** (mới từ #35)

---

## Testing results — Task #35

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: cache-hit → `source=live` không invent; block không cache → seed; FPT ngoài allowlist vẫn 403 honest

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. pytest -q tests/marketplace/` | unit | **34 passed** | + live_cache tests |
| 2 | `PYTHONPATH=. pytest -q tests/companies/test_epic3_digital_honesty.py` | honesty | **6 passed** | Digital VA untouched |
| 3 | prefer-cache smoke RAL,VNM,FPT | ops | `live_ok=2` | artifact `.scratch/epic3-task35-live-cache-smoke.*` |

### Failures
- Không

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | User chưa yêu cầu | Khi ship |
| FE build | Badge nhỏ; optional | Khi PR |
| Session cookie live refresh | Ops-only; cần login tay | Optional ops |

---

## Do not reopen
- Không làm #36–#41 trong chat Task #35
- Không invent units cho DQC/B2B để “đủ GMV”
- Không bật anti-bot SaaS làm mặc định

## Next
**Task #36 — Matcher: chỉ DN có shop; discovery có cổng**

Base: tip Task #35 branch (hoặc merge #35 → main trước nếu user ship).

---

## Paste prompt (chat sau)

```text
# Task
Tiếp tục **Epic 3 Phase 2**. Chat này chỉ làm **Task #36 — Matcher gate (chỉ DN có shop; discovery có cổng)**. STOP sau #36; không làm #37–#41.

Đang chạy theo lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user yêu cầu).

## Context
Repo: `/Users/hale/Code/AI in Data Economy`

Đọc bắt buộc:
- `.scratch/handoff-task35.md` (Task #35 DONE — ADR-0002 allowlist+cache; demo RAL/VNM)
- `.scratch/epic3-phase2-plan.md` § Task #36
- `docs/plan.md` § Epic 3 Phase 2
- `CONTEXT.md`, `AGENTS.md`
- `ml/shop_matcher.py`, `crawlers/marketplace/shop_finder.py`
- Task #33/#34 URL/listing artifacts nếu cần alias

**Phase 2 thứ tự:** #32–#35 DONE → **#36** → #37 → …

## Git / branch
1. Base: tip `cursor/epic3-phase2-task35-marketplace-live-strategy` (merge/PR #35 nếu user đã ship) hoặc tip #34 nếu #35 chưa có.
2. Branch: `cursor/epic3-phase2-task36-matcher-gate`
3. Không commit/push trừ khi user Explicit yêu cầu.

## Task #36 — Yêu cầu

Mục tiêu: matcher chỉ gắn DN có shop; discovery search sàn **tắt mặc định**; bật chỉ với threshold 0.65 + QA list. Không alias ép 28 ticker không shop.

### Functional
1. Khi #33/#34 thêm URL → cập nhật alias/tests nếu cần.
2. Discovery search sàn: **off by default**; enable chỉ với threshold 0.65 + QA allowlist.
3. Ticker không shop vẫn unlinked (precision không tụt).

### Honesty
- Không invent shop links / GMV.
- Giữ match threshold 0.65 (CONTEXT).
- Không đổi Digital VA formulas.

### AC
- Precision không tụt so với baseline tests.
- Ticker không shop vẫn unlinked.
- Discovery mặc định tắt; có cổng bật có kiểm soát.

## Constraints
- Một chat = Task #36 only.
- Không ratio/GRDP (#37/#38), không scale (#39), không website domain (#40), không GMV backfill (#41).

## Waves / Subagents

### W1 — Explore (1–2 subagent song song)
- **A:** ShopMatcher + find_shops / discovery call sites; current default discovery behavior.
- **B:** Alias/tests + seed shop URLs from #33/#34; gaps for gate.

Deliverable: map file + đề xuất gate (flag/env/config) + alias diffs cần thiết.

### W2 — Implement
- Discovery off by default + controlled enable (threshold 0.65 + QA list)
- Alias/tests sync if URLs added
- Tests: no-shop unlinked; precision; discovery default off

### W3 — Verify
```bash
PYTHONPATH=. pytest -q tests/marketplace/ tests/ml/ -k matcher
# hoặc suite matcher/shop liên quan trong repo
```

### W4 — Ship
Handoff `.scratch/handoff-task36.md` + Task review + Testing results + prompt #37 (có Waves) → STOP.
Không commit trừ khi user bảo.
```
