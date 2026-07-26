# Handoff — Task #34 Listing depth (không bịa GMV)

**Status:** DONE (chưa commit/push — chờ user)  
**Branch:** `cursor/epic3-phase2-task34-listing-depth` (base: tip Task #33 `e7c1583`)  
**Date:** 2026-07-25  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** *(chưa — chỉ khi user Explicit yêu cầu)*

---

## Delivered

- Curated DQC listing depth: 2 `website` catalog rows từ `dienquang.com` (`price` set; `units_sold_est`/`revenue_est` **null**) — PROVENANCE trong `data/raw/marketplace_listings_fallback.PROVENANCE.md`
- Sync seed + fallback: `data/seeds/companies.json`, `data/raw/marketplace_listings_fallback.json`
- **Follow-up từ W1 explore:** `backend/app/seed.py` `_upsert_marketplace_listings` trên re-seed (trước đây chỉ insert listing khi company mới — DQC curated không vào DB)
- Ops: `scripts/enrich_marketplace_listings.py` + `crawlers/marketplace/listing_depth.py`
- Report: `.scratch/epic3-task34-listing-depth.{md,csv}`
- Docs: `docs/economy-knowledge.md`, `docs/knowledge.md`, `docs/ops-demo.md`, `docs/plan.md` #34, phase2 plan
- Tests: provenance + DQC no-GMV + B2B empty + seed↔fallback parity + re-seed upsert DQC

### Counts (2026-07-25)

| Metric | Before | After |
|--------|--------|-------|
| Mẫu niêm yết | 28 | 28 |
| Có shop TMĐT | 6 | 6 |
| Có ≥1 listing | 5 | **6** (RAL, VNM, FPT, MSN, PNJ, **DQC**) |
| Có GMV listing (price×units) | 5 | **5** (DQC không invent units) |
| Live scrape ok | — | **0** (Shopee/TikTok 403) |

---

## Task review — #34 Listing depth

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task34-listing-depth` · uncommitted · PR chưa mở

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Chỉ thêm listing khi live hoặc curated + PROVENANCE | done | Live 403 → curated DQC website catalog |
| DQC/peer shop ưu tiên live/curated; B2B `[]` | done | HPG/BMP/… vẫn empty; tests lock |
| Docs tách mẫu niêm yết vs mẫu có TMĐT | done | economy-knowledge + ops-demo + report |
| Báo cáo trước/sau listing counts | done | `.scratch/epic3-task34-listing-depth.*` |
| Không invent GMV/units; Digital VA không đổi | done | DQC units/revenue null → online rev vẫn 0 |
| Provenance `source ∈ {live,seed,fallback}` | done | tests + live mock tags `live` |

Deliverable chính:
- Listing tickers 5→6 không tăng GMV tickers; script smoke live cho Task #35

### Làm thế nào
- Waves: W1 explore (2 subagents) → W2 curated DQC + listing_depth module/script/docs/tests → W3 pytest + live smoke → W4 handoff (no commit)
- Trade-off: không gắn giá website thành Shopee GMV; `platform=website` + units null; chờ #35 cho chiến lược live (cache/session)

### Còn lại / rủi ro (không làm trong chat này)
- Live marketplace vẫn 403 — đã có **Task #35** (bỏ qua, không tạo task trùng)
- Matcher discovery gate — đã có **#36**
- Website SSL/DNS fail 9 ticker — đã có **#40**
- GMV thật DQC / optional TikTok VNM·PNJ sau khi live/cache ổn — **Task #41** (mới ghi plan)

---

## Testing results — Task #34

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: provenance contract giữ; DQC depth không bịa GMV; B2B empty; coverage 28/6/6/5

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. pytest -q tests/marketplace/ tests/companies/test_epic3_digital_honesty.py` | unit | **32 passed** | +parity + re-seed DQC upsert |
| 2 | `… enrich_marketplace_listings.py --no-live` | offline report | exit 0 | with_listing=6 |
| 3 | `… enrich_marketplace_listings.py` | live smoke 28 | exit 0 | live_ok=0 (403) |

### Failures
- Không

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | User chưa yêu cầu | Khi ship |
| `--persist-db` full crawl | Không cần để đóng AC seed | Optional ops |
| FE build | Không đổi FE | Không |

---

## Do not reopen
- Không làm #35–#40 trong chat Task #34
- Không invent units/GMV cho DQC hoặc peer B2B
- Không đổi Digital VA formulas

## Next
**Task #35 — Chiến lược marketplace live (sau Playwright mock)**

Base: tip Task #34 branch (hoặc merge #34 → main trước nếu user ship).

---

## Paste prompt (chat sau)

```text
# Task
Tiếp tục **Epic 3 Phase 2**. Chat này chỉ làm **Task #35 — Chiến lược marketplace live**. STOP sau #35; không làm #36–#40.

Đang chạy theo lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user yêu cầu).

## Context
Repo: `/Users/hale/Code/AI in Data Economy`

Đọc bắt buộc:
- `.scratch/handoff-task34.md` (Task #34 DONE — listing 5→6 tickers; GMV vẫn 5; live Shopee/TikTok 403)
- `.scratch/epic3-phase2-plan.md` § Task #35
- `.scratch/epic3-task34-listing-depth.md`
- `docs/plan.md` § Epic 3 Phase 2
- `CONTEXT.md`, `AGENTS.md`
- `crawlers/marketplace/` (shopee/tiktok/browser_fetch/listing_depth)

**Phase 2 thứ tự:** #32–#34 DONE → **#35** → #36 → …

## Git / branch
1. Base: tip `cursor/epic3-phase2-task34-listing-depth` (merge/PR #34 nếu user đã ship) hoặc tip #33 nếu #34 chưa có.
2. Branch: `cursor/epic3-phase2-task35-marketplace-live-strategy`
3. Không commit/push trừ khi user Explicit yêu cầu.

## Task #35 — Yêu cầu

Mục tiêu: chọn **1–2** chiến lược marketplace live ổn định sau Playwright mock; ghi ADR ngắn nếu đụng ToS/chi phí. Crawl contract không silent invent.

### Functional (chọn khuyến nghị mặc định + optional)
1. **Allowlist nhỏ + cache snapshot + badge live|seed|fallback** (khuyến nghị mặc định).
2. Optional: session cookie sau login tay (ops only).
3. Optional spike: API/đối tác dữ liệu — không implement full nếu không có hợp đồng.
4. Không dùng anti-bot SaaS lách ToS làm mặc định đồ án.

### Honesty
- Không silent invent GMV khi block/403.
- Giữ `source ∈ {live, seed, fallback}`.
- Không đổi Digital VA formulas.

### AC
- Document quyết định trong `.scratch/` hoặc `docs/adr/`.
- Crawl contract không silent invent.
- Ít nhất một đường demo ổn định (cache snapshot hoặc live thật).

## Constraints
- Một chat = Task #35 only.
- Không matcher gate (#36), không ratio/GRDP (#37/#38), không website domain fix (#40).

## Waves / Subagents

### W1 — Explore (1–2 subagent song song)
- **A:** Live path hiện tại (httpx→Playwright), Task #34 live_ok=0 / 403 evidence, cache/snapshot seams.
- **B:** Ops/demo needs + ADR patterns trong `docs/adr/`.

Deliverable: recommendation table (option → cost/ToS/demo stability) + đề xuất chọn 1–2.

### W2 — Implement
- ADR / strategy note + wire allowlist+cache (hoặc option đã chọn)
- Badge/provenance path ổn định cho demo
- Tests: block→seed/fallback; cache hit không invent

### W3 — Verify
```bash
PYTHONPATH=. pytest -q tests/marketplace/
```

### W4 — Ship
Handoff `.scratch/handoff-task35.md` + Task review + Testing results + prompt #36 (có Waves) → STOP.
Không commit trừ khi user bảo.
```
