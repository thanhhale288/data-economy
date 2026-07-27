# Handoff — Task #46 Pipeline cleaning/features VA (nợ từ #38)

**Status:** DONE (uncommitted — commit/PR when user Explicit asks)  
**Branch:** `cursor/epic3-phase2-task46-pipeline-va`  
**Date:** 2026-07-27  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** _(pending user request)_  
**Base:** `origin/main` @ `58896dc` (PR #31 Task #45 merged)

---

## Delivered

- **Cleaning:** `run_data_cleaning` loads `VA_C` / `VA_C_NOMINAL` from `gso_macro` → `va_c` / `va_c_nominal` in `cleaned_macro.parquet` with `*_source`, `*_unit`, `*_alignment=step_hold_at_ingest`
- **Honest clean:** VA uses `max_gap=0`, `fill_long_gaps=False`, `outlier_method="none"` — no linear invent on step-held levels; report notes `role=auxiliary_feature`
- **Missing VA:** listed in `series_missing`; **not** invented from IIP
- **Features:** `load_macro_dataframe` / `build_features` carry VA levels (+ provenance cols); DB fallback loads same; **no** VA lags in v1; `_IIP_DROPNA_SUBSET` unchanged
- **Manifest:** `forecast_target: "iip"`, `feature_groups.va_auxiliary`, notes that VA is auxiliary
- **XGBoost:** provenance string cols excluded; numeric `va_c` may train as exog; artifact `target` stays `iip`
- **Docs:** `docs/plan.md` #46 `[x]`; `docs/knowledge.md`; phase2 plan chat order

### Not done (out of scope)

- Task #43 discovery, #47 GRDP biên bản, #50 UniverseCoverageNote
- #41 / #48 / #49 / #19b (tạm dừng)
- Commit/push/PR (user chưa Explicit yêu cầu)
- VA lags/rolls; ARIMA/LSTM VA exog; đổi forecast target

---

## Task review — #46 Pipeline cleaning/features VA

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task46-pipeline-va` · uncommitted on `58896dc` · PR pending

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Cleaned có `VA_C` (+ optional nominal) + provenance | done | parquet cols + cleaning_report.macro.va_c |
| Features có VA với provenance | done | levels + alignment/source/unit; manifest |
| Step-hold honest / không invent dynamics | done | ingest step-hold; no linear clean on VA |
| Forecast target không đổi im lặng | done | target remains `iip`; manifest + XGB artifact |
| Tests pass | done | 32 related pytest |
| plan #46 `[x]` + handoff | done | this file |

Deliverable chính:
- Wire national manufacturing VA from #38 into cleaned/features as **auxiliary** series; IIP remains ML target

### Làm thế nào
- Waves: W1 explore (2 subagents) → W2 cleaning+features+xgboost exclude → W3 pytest → W4 handoff (no commit)
- Subagents: [Explore cleaning VA path](124d84fd-893f-4467-95e1-5d85dca5e835), [Explore features/forecast target](62d4a0f3-8fc9-4683-b71f-8b5084c376f9)
- File chính: `pipeline/cleaning/run_cleaning.py`, `pipeline/features/engineering.py`, `ml/models/xgboost_model.py`, tests under `tests/pipeline|features|ml`
- Trade-off: VA **levels-only** in features (no lags) để không đụng `MACRO_LAG_COLS` validation; đủ AC “đưa vào features”
- So với plan: đúng #46; không đụng #43/#47/#50

### Còn lại / rủi ro
- Demo cần `gso_macro` đã có VA (#38 crawl/seed) trước khi cleaned/features chứa `va_c`
- Optional later: VA lags as exog; ARIMA `EXOG_CANDIDATES` — không silent target change
- Next open wave: `#43` `#47` `#50` (#41/#48/#49/#19b vẫn tạm dừng)

---

## Testing results — Task #46

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: VA vào cleaned/features honest; forecast target vẫn IIP; không invent khi thiếu VA

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `PYTHONPATH=. pytest -q tests/pipeline/test_run_cleaning.py tests/features/test_engineering.py tests/ml/test_xgboost.py tests/pipeline/test_cleaner.py tests/features/test_validation.py` | cleaning + features + xgb + regression | **32 passed** | includes VA present/absent + target=`iip` artifact |

### Failures
- Không (một assert `result["target"]` sai shape return dict — đã sửa sang load joblib artifact)

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | User chưa Explicit yêu cầu | Khi ship |
| Full `pytest tests/` | Scope #46 đủ AC | CI khi mở PR |
| Live seed → clean → features smoke | Unit fixtures cover wire | Ops bootstrap khi demo |

---

## Do not reopen
- Không làm #43 / #47 / #50 trong chat #46
- Không đổi `target_col` / `_IIP_DROPNA_SUBSET` sang VA
- Không linear-interpolate VA trong cleaning
- Không invent VA từ IIP / Digital VA

## Next
Gợi ý **Task #43 — Discovery crawl + fuzzy hygiene (nợ từ #36)** (search sàn thật → candidates vào cổng QA; không bật discovery mặc định).

Alternates still open: `#47` (GRDP biên bản only), `#50` (`UniverseCoverageNote`).

---

## Paste prompt (chat sau)

```markdown
# Task
Hoàn thành **Task #43 — Discovery crawl + fuzzy hygiene (nợ từ #36)** — search sàn thật (khi ToS/ops cho phép) → candidates vào cổng QA #36; siết token FP; **không** bật discovery mặc định.

Một chat = **#43 only**. STOP sau #43.

Lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user Explicit yêu cầu).

## Plan alignment
Đọc `docs/plan.md` § Epic 3 Phase 2 — **Quyết định người dùng (2026-07-27)** + **Phase 2 — còn mở**:
- #45 / #46 DONE
- #41 / #48 / #49 / #19b = tạm dừng — **không** mở
- Wave còn mở: `#43` `#47` `#50` — chat này chỉ **#43**

## Context
Repo: `/Users/hale/Code/AI in Data Economy` (worktree tip có #46 nếu đã merge/commit)

Đọc bắt buộc:
- `.scratch/handoff-task46.md`, `.scratch/handoff-task36.md` (nếu có), `.scratch/epic3-phase2-plan.md` § Task #43
- `crawlers/marketplace/shop_finder.py`, `ml/shop_matcher/`, `data/mappings/discovery_allowlist.json`
- Gate #36: discovery OFF mặc định; threshold 0.65 + QA allowlist — **không phá**

## Git / branch
1. Base: `main` đã merge #46 (hoặc tip `cursor/epic3-phase2-task46-pipeline-va` nếu PR chưa merge)
2. Branch: `cursor/epic3-phase2-task43-discovery-crawl`
3. Không commit trừ khi user yêu cầu

## Requirements
- Đường candidate shop từ search Shopee/TikTok **hoặc** biên bản “chưa crawl search (anti-bot/ToS)” với evidence
- Candidates chỉ feed cổng `discover_shops_for_company` / allowlist QA — không invent URL/GMV
- Fuzzy hygiene: siết token ngắn generic FP (có test citation)
- Ops smoke optional: ≥1 QA allowlist entry chứng minh `match_source=qa_discovery` khi env bật
- Cập nhật `docs/ops-demo.md` + artifact `.scratch/epic3-task43-discovery-crawl.*`

## Non-goals
- #47 GRDP, #50 UniverseCoverageNote, #41/#48/#49
- Bật discovery mặc định; anti-bot SaaS; đổi Digital VA; ép alias ticker không shop

## Acceptance criteria
- Có đường search candidate **hoặc** biên bản deferred có evidence
- Cổng #36 không bị phá; precision baseline không tụt; không invent shop/GMV
- Tests pass; `docs/plan.md` #43 `[x]` + handoff + review + testing + next prompt

## Waves / Subagents
- **W1 Explore (parallel, read-only):** (a) shop_finder + discovery gate/allowlist (b) matcher fuzzy FP + resolve_shop_to_company
- **W2 Implement:** chỉ Task #43 trên `cursor/epic3-phase2-task43-discovery-crawl`
- **W3 Verify:** pytest marketplace/matcher (+ ops smoke nếu mạng); ghi Testing results
- **W4 Ship:** handoff → task review → testing → next prompt → STOP (commit/PR chỉ khi user Explicit)

## Deliverable
Handoff `.scratch/handoff-task43.md`, plan sync, Task review + Testing results, paste prompt task kế (có Waves).
```
