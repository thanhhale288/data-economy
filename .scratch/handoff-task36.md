# Handoff — Task #36 Matcher gate (chỉ DN có shop; discovery có cổng)

**Status:** DONE (PR open)  
**Branch:** `cursor/epic3-phase2-task36-matcher-gate`  
**Date:** 2026-07-26  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** `9cafd4c` · PR https://github.com/thanhhale288/data-economy/pull/23  
**Base:** `main` @ `091c0a6` (Task #35 merged)

---

## Delivered

- **Discovery gate** in `crawlers/marketplace/shop_finder.py`:
  - `is_marketplace_discovery_enabled()` — env `MARKETPLACE_DISCOVERY_ENABLED` (default **OFF**)
  - `marketplace_discovery_threshold()` — env `MARKETPLACE_DISCOVERY_THRESHOLD` (default **0.65**)
  - `load_discovery_allowlist()` + `discover_shops_for_company()` — QA entries only
  - `run_marketplace_crawl(..., discover=None)` merges discovery only when enabled
- **QA allowlist:** `data/mappings/discovery_allowlist.json` (`entries: []` by default)
- **Alias hygiene:** `train()` skips website-host aliases for no-shop tickers; GVR marker narrowed to `cong nghiep cao su` (no DPR/CSM inherit `gvr`)
- **Docs:** `docs/knowledge.md`, `docs/ops-demo.md`, `docs/plan.md` #36 ✅, phase2 plan, shop-matcher-qa
- **Tests:** discovery default off; allowlist+threshold enable path; no-shop unlinked; precision baseline; joblib retrained (6 shop-only alias keys)

### Enable path (ops)

```bash
export MARKETPLACE_DISCOVERY_ENABLED=1
export MARKETPLACE_DISCOVERY_THRESHOLD=0.65
# edit data/mappings/discovery_allowlist.json entries: [{ticker, channel_type, url}]
```

---

## Task review — #36 Matcher gate

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task36-matcher-gate` · `9cafd4c` · https://github.com/thanhhale288/data-economy/pull/23

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Precision không tụt so với baseline | done | `test_cross_matrix_precision_over_90` — fp==0, precision>0.90 |
| Ticker không shop vẫn unlinked | done | seed `find_shops` empty; discovery off / not on allowlist → `[]` |
| Discovery mặc định tắt; cổng bật có kiểm soát | done | env flag + empty allowlist + threshold 0.65 |
| Không alias ép no-shop tickers | done | `train()` chỉ website alias khi đã có marketplace shop |
| #33/#34 URL sync | done | #33/#34 không thêm shop URL mới — POSITIVE_PAIRS 8 handles ổn |
| Không invent shop/GMV; không đổi Digital VA | done | honesty tests pass |

Deliverable chính:
- Cổng discovery tường minh (OFF default) + QA allowlist file

### Làm thế nào
- Waves: W1 explore (2 subagents) → W2 gate+alias+tests+docs → W3 pytest → W4 handoff (no commit)
- Subagents: [ShopMatcher discovery](0f1b61e7-3a73-4c6b-9731-5a2d655c010c), [alias/tests/seeds](4a3d3c9d-2ea0-4f83-af7e-b7e67f7dc67a)
- File chính: `crawlers/marketplace/shop_finder.py`, `ml/shop_matcher/matcher.py`, `data/mappings/discovery_allowlist.json`
- Trade-off: `evaluate_discovered_shop` vẫn là score-only helper (HPG↔hoaphat có thể ≥0.65); **product link** chỉ qua `discover_shops_for_company` (flag+allowlist). Không có crawler search sàn thật — cổng sẵn cho khi bật sau.
- So với plan: đúng #36; không đụng #37–#41

### Còn lại / rủi ro (đã ghi plan để xử lý sau)
- Industry-ratio re-gate — **Task #37**
- GRDP/VA — **#38**
- Scale architecture — **#39**
- Website domain fix — **#40**
- GMV backfill / live-cache refresh — **#41**
- Cookie/partner spike — **#42**

---

## Testing results — Task #36

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: discovery OFF giữ no-shop unlinked; precision baseline giữ; enable path chỉ QA allowlist + 0.65

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. pytest -q tests/shop_matcher/ tests/marketplace/` | matcher + marketplace | **74 passed** | gate + precision + live_cache |
| 2 | `PYTHONPATH=. pytest -q tests/companies/test_epic3_digital_honesty.py tests/pipeline/test_marketplace_clean.py` | honesty + clean | **16 passed** | Digital VA / resolve_shop untouched formulas |
| 3 | `ShopMatcher().train()` | joblib | ok | 6 alias keys (shop tickers only) |

### Failures
- Transient: precision FP khi thêm DPR vào COMPANIES matrix (`dong` ⊂ `rangdong`) — **không merge DPR vào precision matrix**; giữ test GVR marker riêng. Fixed.

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | Shipped PR #23 | Merge khi CI green |
| Live Shopee search crawler | Ngoài scope — chỉ cổng | Khi có discovery source thật |

---

## Do not reopen
- Không làm #37–#41 trong chat Task #36
- Không invent shop URLs / GMV
- Không ép alias cho 22 ticker không shop
- Không đổi Digital VA formulas

## Next
**Task #37 — Industry-ratio (re-gate)**

Base: tip Task #36 branch (hoặc merge #36 → main trước nếu user ship).

---

## Paste prompt (chat sau)

```text
# Task
Tiếp tục **Epic 3 Phase 2**. Chat này chỉ làm **Task #37 — Industry-ratio (re-gate)**. STOP sau #37; không làm #38–#42.

Đang chạy theo lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user yêu cầu).

## Context
Repo: `/Users/hale/Code/AI in Data Economy`

Đọc bắt buộc:
- `.scratch/handoff-task36.md` (Task #36 DONE — discovery OFF + QA allowlist)
- `.scratch/epic3-phase2-plan.md` § Task #37
- `.scratch/epic3-task30-industry-ratio-research.md` (Phase 1 deferral)
- `docs/plan.md` § Epic 3 Phase 2
- `CONTEXT.md`, `AGENTS.md`
- `pipeline/cleaning/digital_metrics.py` (online revenue / ratio hooks)

**Phase 2 thứ tự:** #32–#36 DONE → **#37** → #38 → …

## Git / branch
1. Base: tip `cursor/epic3-phase2-task36-matcher-gate` (merge/PR #36 nếu user đã ship) hoặc tip `main` sau merge #36.
2. Branch: `cursor/epic3-phase2-task37-industry-ratio-regate`
3. Không commit/push trừ khi user Explicit yêu cầu.

## Task #37 — Yêu cầu

Mục tiêu: chỉ wire industry-ratio nếu có tỷ trọng TMĐT/doanh thu (hoặc proxy có citation rõ) cho CBCT/manufacturing. File `data/mappings/` + PROVENANCE. Không dùng % kinh tế số/GDP làm × revenue DN.

### Functional
1. Re-check research note #30: có nguồn citation đủ để set constant không?
2. Nếu có: wire mapping + provenance; digital metrics dùng constant có nguồn.
3. Nếu không: đóng task với “vẫn None” + cập nhật research note / plan.

### Honesty
- Không invent ratio / GMV.
- Không đổi Digital VA formulas ngoài chỗ ratio đã thiết kế có nguồn.
- Không silent enable ratio từ GDP digital %.

### AC
- Constant set **có citation** trong `data/mappings/` + PROVENANCE, **hoặc** task đóng “vẫn None” + biên bản cập nhật.
- Tests: không silent invent; behavior khớp quyết định (wired hoặc still None).

## Constraints
- Một chat = Task #37 only.
- Không GRDP (#38), không scale (#39), không website domain (#40), không GMV (#41).

## Waves / Subagents

### W1 — Explore (1–2 subagent song song)
- **A:** digital_metrics / industry-ratio call sites + current None/deferred behavior.
- **B:** research note #30 + candidate public sources (citation quality).

Deliverable: go/no-go recommendation + file map.

### W2 — Implement
- Wire constant+PROVENANCE **nếu** go; else update deferral docs/tests only.
- Tests matching decision.

### W3 — Verify
```bash
PYTHONPATH=. pytest -q tests/companies/test_epic3_digital_honesty.py tests/pipeline/ -k "digital or ratio or online"
```

### W4 — Ship
Handoff `.scratch/handoff-task37.md` + Task review + Testing results + prompt #38 (có Waves) → STOP.
Không commit trừ khi user bảo.
```
