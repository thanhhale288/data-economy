# Handoff — Epic 5 Wave 4 (#68 #75 #79 #81)

**Status:** DONE (PRs open, CI green) — chưa merge  
**Date:** 2026-08-19  
**Base:** `origin/main` @ `f17bf4c` (wave 3 #78 #80 #70 #76 đã merge)  
**Playbook:** `.scratch/epic5-remain-plan.md`  
**Không tick:** `docs/plan.md` / checklist epic5 (đợi user `tick epic5` sau khi merge)

Mỗi task = 1 worktree + 1 branch + 1 PR → `main`. Merge hết 4 PR rồi mới mở gated #82–#94 (chỉ khi user gọi đúng số).

**Conflict note:** #68 và #79 cùng sửa `docs/ops-demo.md` nhưng **khác section** (DocAI smoke vs alias harvest). Git thường auto-merge; nếu conflict thì chỉ docs. #81 sửa `Benchmark.jsx`; #68 **không** đụng file đó.

---

## Branches / PRs

| Task | Branch | PR | CI |
|------|--------|----|-----|
| #68 | `cursor/epic5-phase1-task68-docai-extract-smoke` | https://github.com/thanhhale288/data-economy/pull/71 | Backend + Frontend **pass** |
| #75 | `cursor/epic5-phase3-task75-nlp-label-expand` | https://github.com/thanhhale288/data-economy/pull/74 | Backend + Frontend **pass** |
| #79 | `cursor/epic5-phase4-task79-feedback-alias-harvest` | https://github.com/thanhhale288/data-economy/pull/72 | Backend + Frontend **pass** |
| #81 | `cursor/epic5-phase5-task81-benchmark-wave-a` | https://github.com/thanhhale288/data-economy/pull/73 | Backend + Frontend **pass** |

Worktrees (gitignore): `.worktrees/t68` `t75` `t79` `t81`. Có thể `git worktree remove` sau khi merge.

Handoff chi tiết từng PR nằm trên branch tương ứng (`.scratch/handoff-task68.md` …). File này = batch wave.

---

## Task #68 — DocAI extract smoke

### Đã làm được gì
- Smoke TestClient: `POST /api/benchmark/extract` với `sample_bctc_text.pdf` → field có số, `source_type=pdf_text`.
- Scan PNG/PDF: honesty `ocr_unavailable` + field trống khi thiếu PaddleOCR (không bịa số).
- Confirm-before-compare ghi là cổng FE sẵn có (checkbox); **không** sửa `Benchmark.jsx`.
- `docs/ops-demo.md`: lệnh text-PDF; scan skip; bước UI thủ công.

### Hạn chế / chưa làm được
- Không thêm Playwright (CI mặc định không tải browser).
- Smoke không chạy compare (không cần DB peer đầy).

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. pytest -q tests/benchmark/test_docai_extract_smoke.py` → 5 passed
- `PYTHONPATH=. pytest -q tests/benchmark/ -k extract` → 48 passed, 40 deselected
- CI PR #71: Backend tests pass, Frontend build pass
- Branch / PR: `cursor/epic5-phase1-task68-docai-extract-smoke` / https://github.com/thanhhale288/data-economy/pull/71

---

## Task #75 — Mở rộng nhãn NLP / matcher QA

### Đã làm được gì
- Categorizer labels 144 → **147** từ tên **đã có** trong live cache (không invent).
- Precision giữ **1.0** — không hạ threshold 0.22 / 0.04.
- Shop QA 22 → **30**: thêm 8 `seed_negative` từ handle `digital_presence` sẵn có. Hybrid gate vẫn pass (precision 1.0, recall 0.9286). FN còn `led_chieusang_congnghiep`.

### Hạn chế / chưa làm được
- Seed + fallback listing titles gần như đã có nhãn; live cache chỉ thêm được 3 tên.
- Shop positive đã cover mọi handle marketplace trong seed — QA mới chỉ là negative.
- Không persist model binary; runtime matcher vẫn tfidf.

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. python3 scripts/eval_product_categorizer.py --no-persist` → precision 1.0 (train 123 / test 24)
- `PYTHONPATH=. python3 scripts/eval_shop_matcher.py --backend tfidf --no-persist` → gate_pass=true
- `PYTHONPATH=. pytest -q tests/product_categorizer/ tests/shop_matcher/` → 63 passed
- CI PR #74: Backend tests pass, Frontend build pass
- Branch / PR: `cursor/epic5-phase3-task75-nlp-label-expand` / https://github.com/thanhhale288/data-economy/pull/74

---

## Task #79 — Harvest alias từ feedback JSONL

### Đã làm được gì
- CLI `scripts/harvest_feedback_aliases.py` đọc JSONL → đề xuất markdown/JSON khi ≥N (mặc định 3) lần sửa cùng field.
- Heuristic đơn vị: after/before ~1000 hoặc 1e6 → đề xuất nghìn/triệu.
- **Không** ghi `_LABEL_ALIASES`. `proposed_aliases` rỗng vì JSONL không có nhãn BCTC gốc.
- Report không chứa raw PDF.

### Hạn chế / chưa làm được
- Không auto-apply vào extract.
- Không Prefect / không retrain.
- Signal thật trên máy demo có thể chưa đủ N=3 — fixture test thì đủ.

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. pytest -q tests/benchmark/ -k 'feedback or harvest or alias'` → 25 passed, 66 deselected
- CI PR #72: Backend tests pass, Frontend build pass
- Branch / PR: `cursor/epic5-phase4-task79-feedback-alias-harvest` / https://github.com/thanhhale288/data-economy/pull/72

---

## Task #81 — Benchmark Wave A

### Đã làm được gì
- Header: tiêu đề + subtitle honesty (peer niêm yết mẫu, không census GSO).
- Breadcrumb: `Benchmark` khi thiếu VSIC; `Benchmark → VSIC 27` khi có mã (2 chữ số đầu). Không bịa mã.
- Khối industry context **trên form**: `peer_scope`, VSIC 2-digit, peer = BCTC niêm yết seed (~28), link demo VSIC 1100 `insufficient_peers`.
- Thiếu số → N/A / ẩn. Không bảng tỷ lệ ngành GSO giả.
- Không đổi math `benchmark_service.py`. Không Wave B.

### Hạn chế / chưa làm được
- `~28` là copy mẫu sẵn có, không phải số census mới.
- Wave B (tách component) vẫn gated #92.

### Testing results
- Overall: **PASS**
- `cd frontend && node --test src/benchmarkIndustryContext.test.js` → 7 passed
- `cd frontend && npm run build` → pass
- CI PR #73: Backend tests pass, Frontend build pass
- Branch / PR: `cursor/epic5-phase5-task81-benchmark-wave-a` / https://github.com/thanhhale288/data-economy/pull/73

---

## Do not reopen

- Không tick `docs/plan.md` / checklist epic5 trong các PR này.
- Gated #82–#94 vẫn đóng (chỉ mở khi user ghi đúng số task).
- Không invent số GSO/OECD/CafeF; không đổi Digital VA / VDEI.
