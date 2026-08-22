# Handoff — Epic 5 Wave 1 (#66 #67 #71 #73)

**Status:** DONE (PRs open, CI green) — chưa merge  
**Date:** 2026-08-19  
**Base:** `origin/main` @ `58d2bc2` (PR #58 Epic 5 playbook)  
**Playbook:** `.scratch/epic5-remain-plan.md`  
**Không tick:** `docs/plan.md` / checklist epic5 (đợi user `tick epic5` sau khi merge)

Mỗi task = 1 worktree + 1 branch + 1 PR → `main`. Merge hết 4 PR rồi mới mở wave 2.

---

## Branches / PRs

| Task | Branch | PR | CI |
|------|--------|----|----|
| #66 | `cursor/epic5-phase1-task66-docai-extract-honesty-ux` | https://github.com/thanhhale288/data-economy/pull/60 | Backend + Frontend **pass** |
| #67 | `cursor/epic5-phase1-task67-bctc-english-aliases` | https://github.com/thanhhale288/data-economy/pull/62 | Backend + Frontend **pass** |
| #71 | `cursor/epic5-phase2-task71-lightgbm-train-ops` | https://github.com/thanhhale288/data-economy/pull/61 | Backend + Frontend **pass** |
| #73 | `cursor/epic5-phase2-task73-dashboard-anomaly-chip` | https://github.com/thanhhale288/data-economy/pull/59 | Backend + Frontend **pass** |

Worktrees (gitignore): `.worktrees/t66` `t67` `t71` `t73`. Có thể `git worktree remove` sau khi merge.

Handoff chi tiết từng PR nằm trên branch tương ứng (`.scratch/handoff-task66.md` …). File này = batch wave.

---

## Task #66 — FE honesty OCR / pages_capped

### Đã làm được gì
- Banner Benchmark map token kỹ thuật → câu tiếng Việt (`frontend/src/extractWarningCopy.js`).
- `ocr_unavailable`: máy chủ chưa OCR; dùng CafeF hoặc PDF chữ; scan để form trống.
- `pages_capped:15`: chỉ đọc 15 trang đầu.
- Token lạ: giữ raw token trong câu generic, không nuốt im.
- Confirm-before-compare không đổi; không bịa 0.

### Hạn chế / chưa làm được
- Không cài PaddleOCR; scan vẫn trống nếu server không OCR.
- Không sửa `bctc_extract.py`.

### Testing results
- Overall: **PASS**
- `cd frontend && node --test src/extractWarningCopy.test.js` → 6 passed
- `cd frontend && npm run build` → pass
- CI PR #60: Backend tests pass, Frontend build pass

---

## Task #67 — English aliases BCTC extract

### Đã làm được gì
- Alias EN (dài trước ngắn): profit before tax, net revenue, revenue from sales, total assets, owner's equity / owners equity / total equity, number of employees / employees.
- Đơn vị: in millions of dong/VND, VND million, in thousands — cùng hệ số nghìn/triệu.
- Fixture synthetic `tests/benchmark/fixtures/sample_bctc_text_en.pdf` + golden `text_full_en`.
- Alias VI không regress; field không match → null + `missing_field:*`.

### Hạn chế / chưa làm được
- PDF tự tạo, không phải BCTC HOSE thật (golden thật = #70).
- Không đổi OCR `lang=en`.

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. pytest -q tests/benchmark/ -k extract` → 42 passed, 32 deselected
- CI PR #62: Backend tests pass, Frontend build pass

---

## Task #71 — LightGBM train/ops + monitoring

### Đã làm được gì
- `CANONICAL_MODELS` + `ARTIFACT_CANDIDATES` gồm `lightgbm` (`lightgbm_model.joblib`, `lightgbm_importance.json`).
- Chưa train → metrics null + warning (honesty).
- Docs train: `POST /api/ml/train`, `./run.sh train`, Pipeline `ml_training` trong `docs/ops-demo.md`.
- Train local `train_lightgbm` trên Postgres: MAPE **9.9306** (fit thật). Không commit binary.
- `.gitignore` thêm `data/models/lightgbm_model.joblib` và `lightgbm_features.joblib`.

### Hạn chế / chưa làm được
- Không chạy `train_all_models` (tránh ghi đè artifact ARIMA/XGB/LSTM đang track).
- `artifact_path` registry trỏ worktree nếu train từ `.worktrees/t71` — train lại từ checkout serve trước khi xóa worktree.
- Drift baseline = task #72 (sau khi merge #71).

### Testing results
- Overall: **PASS**
- `PYTHONPATH=. pytest -q tests/ml/ -k 'lightgbm or ml_monitoring'` → 12 passed, 45 deselected
- CI PR #61: Backend tests pass, Frontend build pass

---

## Task #73 — Dashboard anomaly chip

### Đã làm được gì
- Dashboard gọi `api.getAnomalies`. Chip `banner-warn` cạnh biểu đồ IIP **chỉ khi** kỳ IIP mới nhất `is_anomaly === true` và `available === true`.
- Thiếu series / API lỗi / chưa flagged → **ẩn**, không bịa alert, không banner “all clear”.
- Copy: Isolation Forest trên GSO Section C; link ML Lab. Không sửa detector.

### Hạn chế / chưa làm được
- Chỉ kỳ IIP mới nhất; cờ lịch sử ở ML Lab.
- Không có Vitest trong repo (helper tách `frontend/src/iipAnomalyChip.js`).

### Testing results
- Overall: **PASS**
- `cd frontend && npm run build` → pass
- CI PR #59: Backend tests pass, Frontend build pass

---

## Do not reopen

- Không tick `docs/plan.md` / checklist epic5 trong các PR này.
- Không mở wave 2 (#77 #74 #72 #69) trước khi 4 PR wave 1 merge vào `main` (#72 phụ thuộc #71).
- Gated #82–#94 vẫn đóng.
- Không invent số GSO/OECD/CafeF; không đổi Digital VA / VDEI.
- Labels `epic:5` / `phase:1|2` chưa có trên repo — PR không gắn label mới.
