# Handoff — Epic 5 Wave 2 (#77 #74 #72 #69)

**Status:** DONE (PRs open) — chưa merge  
**Date:** 2026-08-19  
**Base:** `origin/main` @ `3772afe` (wave 1 #66 #67 #71 #73 đã merge)  
**Playbook:** `.scratch/epic5-remain-plan.md`  
**Không tick:** `docs/plan.md` / checklist epic5 (đợi user `tick epic5` sau khi merge)

Mỗi task = 1 worktree + 1 branch + 1 PR → `main`. Merge hết 4 PR rồi mới mở wave 3.

**Conflict note:** #69 và #72 cùng sửa `docs/ops-demo.md`. Merge cái sau có thể cần rebase/resolve (chỉ docs). #74 và #77 không đụng file đó.

---

## Branches / PRs

| Task | Branch | PR |
|------|--------|----|
| #77 | `cursor/epic5-phase4-task77-narrative-llm-base-url` | https://github.com/thanhhale288/data-economy/pull/66 |
| #74 | `cursor/epic5-phase3-task74-categorizer-api-fe` | https://github.com/thanhhale288/data-economy/pull/65 |
| #72 | `cursor/epic5-phase2-task72-ml-drift-baseline` | https://github.com/thanhhale288/data-economy/pull/64 |
| #69 | `cursor/epic5-phase1-task69-ocr-ops-note` | https://github.com/thanhhale288/data-economy/pull/63 |

Worktrees (gitignore): `.worktrees/t77` `t74` `t72` `t69`. Có thể `git worktree remove` sau khi merge.

Handoff chi tiết từng PR nằm trên branch tương ứng (`.scratch/handoff-task77.md` …). File này = batch wave.

---

## Task #77 — Narrative LLM BASE_URL

### Đã làm được gì
- Benchmark/forecast narrative không POST cứng `api.openai.com`.
- Env: per-service BASE_URL → `NARRATIVE_LLM_BASE_URL` → OpenAI default. Host Gemini OpenAI-compatible nối `/chat/completions`.
- Honesty gate không nới; không log key. `.env.example` commented, không secret.

### Hạn chế / chưa làm được
- Không gọi mạng thật OpenAI/Gemini.
- Live demo vẫn cần key + BASE_URL trong local `.env`.

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. pytest -q tests/benchmark/ -k narrative` → 10 passed, 69 deselected
- `PYTHONPATH=. pytest -q tests/ml/ -k narrative` → 11 passed, 51 deselected
- Branch / PR: `cursor/epic5-phase4-task77-narrative-llm-base-url` / https://github.com/thanhhale288/data-economy/pull/66

---

## Task #74 — Categorizer API + cột FE

### Đã làm được gì
- `POST /api/ml/categorize` wrap TF-IDF classifier; load artifact một lần; không train trong request.
- Abstain → `vsic_code` null + `reason`. CompanyDetail cột **VSIC dự đoán**; fail/abstain → **—** + tooltip.

### Hạn chế / chưa làm được
- Không persist prediction; một request / listing; không batch.
- Không mở rộng nhãn (#75); không sửa shop_matcher.

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. pytest -q tests/product_categorizer/ tests/ml/ -k 'categor'` → 12 passed, 57 deselected
- `cd frontend && npm run build` → pass (Vite 5.4.21)
- Branch / PR: `cursor/epic5-phase3-task74-categorizer-api-fe` / https://github.com/thanhhale288/data-economy/pull/65

---

## Task #72 — Drift baseline file

### Đã làm được gì
- `scripts/write_ml_monitoring_baseline.py` đọc MAPE mới nhất từ `ModelRegistry`; không bịa MAPE.
- JSON committed từ sqlite local: arima 31.7036, xgboost 6.4405, lstm 10.0786. **lightgbm omitted** (`registry_missing`).
- Docs: refresh baseline sau retrain đạt chuẩn.

### Hạn chế / chưa làm được
- LightGBM chưa có hàng registry trên sqlite demo → drift LightGBM vẫn null cho đến khi train + ghi registry rồi chạy lại script.
- Không query Postgres từ `.env`.

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. pytest -q tests/ml/ -k 'ml_monitoring or baseline or drift'` → 9 passed, 52 deselected
- Branch / PR: `cursor/epic5-phase2-task72-ml-drift-baseline` / https://github.com/thanhhale288/data-economy/pull/64

---

## Task #69 — OCR ops note

### Đã làm được gì
- `docs/ops-demo.md`: mặc định lazy-load PaddleOCR; **không** bake Docker.
- Cài extra, `PADDLE_*`, `~/.paddlex`, FE `ocr_unavailable` (#66), workaround CafeF / PDF chữ, pytest `-m "not ocr"`.

### Hạn chế / chưa làm được
- Không cài paddle; không đo thời gian first-init.
- Scan trên image chưa extra vẫn form trống + banner.

### Testing results
- Overall: **PASS** (docs review)
- Không chạy pytest/paddle (đúng card)
- Branch / PR: `cursor/epic5-phase1-task69-ocr-ops-note` / https://github.com/thanhhale288/data-economy/pull/63

---

## Do not reopen

- Không tick `docs/plan.md` / checklist epic5 trong các PR này.
- Không mở wave 3 (#78 #80 #70 #76) trước khi 4 PR wave 2 merge vào `main`.
- Gated #82–#94 vẫn đóng.
- Không invent số GSO/OECD/CafeF; không đổi Digital VA / VDEI.
