# Handoff — Epic 5 Wave 3 (#78 #80 #70 #76)

**Status:** DONE (PRs open) — chưa merge  
**Date:** 2026-08-19  
**Base:** `origin/main` @ `5a30cce` (wave 2 #77 #74 #72 #69 đã merge)  
**Playbook:** `.scratch/epic5-remain-plan.md`  
**Không tick:** `docs/plan.md` / checklist epic5 (đợi user `tick epic5` sau khi merge)

Mỗi task = 1 worktree + 1 branch + 1 PR → `main`. Merge hết 4 PR rồi mới mở wave 4.

**Conflict note:** bốn PR không chung file nóng (`Benchmark.jsx` / `CompanyDetail.jsx` / golden extract / shop matcher). Merge độc lập được.

---

## Branches / PRs

| Task | Branch | PR | CI |
|------|--------|----|-----|
| #78 | `cursor/epic5-phase4-task78-feedback-cafef-manual` | https://github.com/thanhhale288/data-economy/pull/69 | Backend + Frontend **pass** |
| #80 | `cursor/epic5-phase5-task80-website-url-fail-chip` | https://github.com/thanhhale288/data-economy/pull/70 | opened after local tests |
| #70 | `cursor/epic5-phase1-task70-extract-golden-realish` | https://github.com/thanhhale288/data-economy/pull/68 | Backend + Frontend **pass** |
| #76 | `cursor/epic5-phase3-task76-shop-matcher-st-eval` | https://github.com/thanhhale288/data-economy/pull/67 | Backend + Frontend **pass** |

Worktrees (gitignore): `.worktrees/t78` `t80` `t70` `t76`. Có thể `git worktree remove` sau khi merge.

Handoff chi tiết từng PR nằm trên branch tương ứng (`.scratch/handoff-task78.md` …). File này = batch wave.

---

## Task #78 — Feedback CafeF + manual

### Đã làm được gì
- CafeF prefill đi qua checkbox confirm hiện có trước khi so sánh.
- Form nhập tay gửi training signal lúc Compare (`source_type=manual`).
- DocAI giữ confirm-before-compare.
- Một phiên tối đa một POST (`feedbackPostedRef`; checkbox thắng Compare).
- Chỉ diff field allowlist; không lưu PDF.

### Hạn chế / chưa làm được
- Không đổi math compare.
- Harvest alias từ JSONL vẫn là #79.

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. pytest -q tests/benchmark/ -k feedback` → 9 passed, 73 deselected
- `cd frontend && npm run build` → pass (agent)
- CI PR #69: Backend tests pass, Frontend build pass
- Branch / PR: `cursor/epic5-phase4-task78-feedback-cafef-manual` / https://github.com/thanhhale288/data-economy/pull/69

---

## Task #80 — Chip URL website fail

### Đã làm được gì
- GEE hiện chip **chưa verify (SSL)** trên danh sách và trang chi tiết.
- Provenance seed/Task #40: `website_verify_status=fail`, `reason=ssl_unverified` — không bịa mã HTTP.
- Ticker OK (RAL) không gắn fail. Copy không suy “không có TMĐT” / checkout no từ SSL fail.
- SSL verify vẫn bật.

### Hạn chế / chưa làm được
- GEE `https://gelex-electric.com` vẫn fail SSL thật.
- Checkout GEE vẫn **unknown**; `has_checkout=false` chỉ default lưu trữ.
- DB cũ cần re-seed (hoặc fallback ticker+URL) mới thấy chip.

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. pytest -q tests/companies/test_website_verify.py` → 8 passed
- `cd frontend && node --test src/websiteVerifyChip.test.js` → 5 passed
- `cd frontend && npm run build` → pass (agent)
- Branch / PR: `cursor/epic5-phase5-task80-website-url-fail-chip` / https://github.com/thanhhale288/data-economy/pull/70

---

## Task #70 — Golden extract HOSE-like

### Đã làm được gì
- Golden 4 → 9 case synthetic (không BCTC DN thật): `hose_like_trieu`, `en_sales_layout`, `partial_revenue_assets`, `hose_notes_noise`, `hose_nghin_dong`.
- Không hạ threshold 0.75; không retune alias để giả 1.0.

### Hạn chế / chưa làm được
- Accuracy 1.0 là so với expected trung thực (kể cả null), không phải coverage đầy đủ field.
- `coverage_all_slots` **0.73** vì case partial/empty cố ý để null.

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. python3 scripts/eval_benchmark_extract.py` → 9 cases, 45/45 đúng expected, coverage_all_slots 0.733
- `PYTHONPATH=. pytest -q tests/benchmark/ -k 'extract or golden'` → 43 passed, 37 deselected
- CI PR #68: Backend tests pass, Frontend build pass
- Branch / PR: `cursor/epic5-phase1-task70-extract-golden-realish` / https://github.com/thanhhale288/data-economy/pull/68

---

## Task #76 — Shop matcher ST eval

### Đã làm được gì
- Eval QA n=22, threshold 0.65. Runtime mặc định vẫn **tfidf**.
- Env `SHOP_MATCHER_BACKEND` (default tfidf). CI không download Hub.
- ST F1 0.9655 vs TF-IDF 0.9630 nhưng **fail gate** (1 FP); rescue `led_chieusang_congnghiep`.

| Matcher | Precision | Recall | F1 | Gate |
|---------|-----------|--------|----|------|
| Fuzzy | 1.0000 | 0.7143 | 0.8333 | — |
| Hybrid TF-IDF | 1.0000 | 0.9286 | 0.9630 | pass |
| Hybrid ST | 0.9333 | 1.0000 | 0.9655 | fail (1 FP) |

### Hạn chế / chưa làm được
- Không bật ST production (user chưa đồng ý trong chat).
- FN TF-IDF còn `led_chieusang_congnghiep`.

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. pytest -q tests/shop_matcher/` → 54 passed
- eval `--backend tfidf --no-persist` → gate_pass=true
- eval `--backend sentence_transformers --no-persist` → gate_pass=false
- CI PR #67: Backend tests pass, Frontend build pass
- Branch / PR: `cursor/epic5-phase3-task76-shop-matcher-st-eval` / https://github.com/thanhhale288/data-economy/pull/67

---

## Do not reopen

- Không tick `docs/plan.md` / checklist epic5 trong các PR này.
- Không mở wave 4 (#68 #75 #79 #81) trước khi 4 PR wave 3 merge vào `main`.
- Gated #82–#94 vẫn đóng.
- Không invent số GSO/OECD/CafeF; không đổi Digital VA / VDEI.
