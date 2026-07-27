# Handoff — Task #43 Discovery crawl + fuzzy hygiene (nợ từ #36)

**Status:** DONE (shipped locally — commit/PR khi user Explicit yêu cầu)  
**Branch:** `cursor/epic3-phase2-task43-discovery-crawl`  
**Date:** 2026-07-27  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** _(chưa — user chưa yêu cầu commit)_  
**Base:** `origin/main` @ `94f459c` (PR #32 Task #46 merged)

---

## Delivered

- **Search path:** `search_marketplace_shop_candidates` + `candidates_to_qa_allowlist_entries` in `crawlers/marketplace/shop_finder.py` — parse-only candidates; never invent; never auto-link (still #36 gate)
- **Deferred biên bản:** live Shopee/TikTok search **blocked** (anti-bot) — `.scratch/epic3-task43-discovery-crawl.{md,csv}`
- **Ops smoke:** injected RAL allowlist → `match_source=qa_discovery`; committed `discovery_allowlist.json` stays `entries: []`; discovery default OFF
- **Fuzzy hygiene:** `MIN_TOKEN_CONTAINMENT_LEN=5` + `_COMPANY_NOISE` += `dong`; DPR ↛ `rangdong_official`; RAL still matches via brand alias
- **Pipeline gate:** `resolve_shop_to_company(..., discovery_gated=True, allowed_company_ids=…)` + `allowed_company_ids_for_discovery_url`; clean path refuses `qa_discovery` rows without allowed ids
- **Docs:** `docs/ops-demo.md`, `docs/knowledge.md`, `docs/plan.md` #43 `[x]`, `.env.example`, phase2 plan

### Not done (out of scope)

- Task #47 GRDP biên bản, #50 UniverseCoverageNote
- #41 / #48 / #49 / #19b (tạm dừng)
- Commit/push/PR — chờ user Explicit
- Live search unlock / anti-bot SaaS
- Bật discovery mặc định; ép alias no-shop tickers

---

## Task review — #43 Discovery crawl + fuzzy hygiene

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task43-discovery-crawl` · _(uncommitted)_ · —

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Đường search candidate **hoặc** biên bản deferred | done | Code path + live spike blocked → biên bản |
| Cổng #36 không bị phá | done | OFF default; empty allowlist; threshold 0.65 |
| Precision baseline không tụt | done | fp==0; rubber peers now safe in matrix |
| Không invent shop/GMV | done | parse-only; allowlist empty in git |
| Fuzzy token FP siết + test citation | done | DPR/rangdong + RAL/dongphu tests |
| Ops smoke `qa_discovery` | done | injected allowlist; unit + live script |
| plan #43 `[x]` + handoff | done | this file |

Deliverable chính:
- Search candidate API into QA gate + deferred anti-bot evidence + fuzzy hygiene for short generic tokens

### Làm thế nào
- Waves: W1 explore (2 subagents) → W2 search+hygiene+resolve gate → W3 pytest + live spike → W4 handoff (no commit)
- Subagents: [Explore shop_finder gate](8a04682a-1352-4d77-8501-46d141ef05de), [Explore matcher fuzzy FP](41380695-463f-4527-8f1c-a6ed330dbde1)
- File chính: `crawlers/marketplace/shop_finder.py`, `ml/shop_matcher/matcher.py`, `pipeline/cleaning/marketplace_clean.py`, tests under `tests/marketplace|shop_matcher|pipeline`
- Trade-off: live search deferred (anti-bot) rather than inventing candidates; code path ready when ToS/ops allow
- So với plan: đúng #43; không đụng #47/#50

### Còn lại / rủi ro
- Live search vẫn blocked — reopen crawl only when ToS/ops allow real parseable results
- Optional later: auto-write allowlist from search (still needs human QA) — not in #43
- Next open wave: `#47` `#50` (#41/#48/#49/#19b vẫn tạm dừng)

---

## Testing results — Task #43

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: search path + gate intact; fuzzy FP fixed; live search honestly deferred

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. pytest -q tests/shop_matcher/ tests/marketplace/test_discovery_search.py tests/marketplace/test_fetch.py tests/pipeline/test_marketplace_clean.py` | core #43 | **72 passed** | hygiene + search mocks + gate |
| 2 | `PYTHONPATH=. pytest -q tests/shop_matcher/ tests/marketplace/ tests/pipeline/test_marketplace_clean.py tests/companies/test_epic3_digital_honesty.py` | broader regression | **106 passed** | honesty + live_cache untouched |
| 3 | Live `search_marketplace_shop_candidates` (Shopee×2, TikTok×1) | ops spike | **blocked** ×3 | anti-bot; CSV/MD artifact |
| 4 | Injected allowlist → `discover_shops_for_company` | ops smoke | **qa_discovery** | then env unset → OFF |

### Failures
- Không

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | User chưa Explicit yêu cầu | Khi user bảo ship |
| Full `pytest tests/` | Scope #43 đủ AC | CI khi mở PR |
| Live search success path | Anti-bot | Khi ToS/ops cho phép |

---

## Do not reopen
- Không làm #47 / #50 trong chat #43
- Không bật discovery mặc định
- Không invent shop URLs / GMV
- Không anti-bot SaaS; không đổi Digital VA

## Next
Gợi ý **Task #47 — GRDP tỉnh×ngành re-gate (nợ từ #38)** — **chỉ biên bản** deferred/NO-GO (chưa table ID NSO); không crawl; không copy `VA_C` quốc gia xuống tỉnh.

Alternate still open: `#50` (`UniverseCoverageNote`).

---

## Paste prompt (chat sau)

```markdown
# Task
Hoàn thành **Task #47 — GRDP tỉnh×ngành re-gate (nợ từ #38)** — **chỉ biên bản** deferred/NO-GO (chưa có table ID NSO đáng tin); **không crawl**; **không** copy `VA_C` quốc gia xuống tỉnh.

Một chat = **#47 only**. STOP sau #47.

Lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user Explicit yêu cầu).

## Plan alignment
Đọc `docs/plan.md` § Epic 3 Phase 2 — **Quyết định người dùng (2026-07-27)** + **Phase 2 — còn mở**:
- #42 / #43 / #45 / #46 DONE
- #41 / #48 / #49 / #19b = tạm dừng — **không** mở
- Wave còn mở: `#47` `#50` — chat này chỉ **#47**

## Context
Repo: `/Users/hale/Code/AI in Data Economy` (worktree tip có #43 nếu đã merge/commit)

Đọc bắt buộc:
- `.scratch/handoff-task43.md`, `.scratch/handoff-task38.md` (nếu có), `.scratch/epic3-phase2-plan.md` § Task #47
- `.scratch/epic3-task31-grdp-spike.md` (spike cũ)
- `docs/economy-knowledge.md` / ADR liên quan VA vs GRDP tỉnh
- Code ingest VA quốc gia (`VA_C`) — chỉ để **không** nhân bản xuống tỉnh

## Git / branch
1. Base: `main` đã merge #43 (hoặc tip `cursor/epic3-phase2-task43-discovery-crawl` nếu PR chưa merge)
2. Branch: `cursor/epic3-phase2-task47-grdp-deferred`
3. Không commit trừ khi user yêu cầu

## Requirements
- Biên bản NO-GO / deferred có evidence: chưa table ID NSO tỉnh×ngành CBCT
- Ghi rõ: cấm copy `VA_C` quốc gia → tỉnh; national VA từ #38 vẫn OK
- Artifact `.scratch/epic3-task47-grdp-deferred.*` + cập nhật `docs/plan.md` / economy-knowledge nếu cần
- Không implement crawler GRDP tỉnh

## Non-goals
- #50 UniverseCoverageNote; #41/#48/#49
- Crawl GRDP; invent GRDP; wire tỉnh vào dashboard/pipeline

## Acceptance criteria
- Biên bản deferred/NO-GO rõ ràng + citation gap
- Không crawl / không invent / không copy national VA xuống tỉnh
- plan #47 `[x]` + handoff + review + testing + next prompt

## Waves / Subagents
- **W1 Explore (parallel, read-only):** (a) #31/#38 GRDP spike + VA_C ingest path (b) plan/economy-knowledge GRDP tỉnh gaps
- **W2 Implement:** chỉ biên bản + doc sync trên `cursor/epic3-phase2-task47-grdp-deferred`
- **W3 Verify:** không regress VA_C tests; ghi Testing results (doc/artifact review)
- **W4 Ship:** handoff → task review → testing → next prompt → STOP (commit/PR chỉ khi user Explicit)

## Deliverable
Handoff `.scratch/handoff-task47.md`, plan sync, Task review + Testing results, paste prompt task kế (có Waves) — gợi ý **#50**.
```
