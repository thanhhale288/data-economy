# Khảo sát Epic 5 — Task #95 (audit)

**Status:** DONE (báo cáo khảo sát — không sửa code trong branch này)
**Date:** 2026-08-19
**Branch:** `cursor/epic5-phase0-task95-epic5-audit` (từ `origin/main` @ `045c8f6`)
**Nguồn:** `.scratch/epic5-remain-plan.md`, handoff #66–#81 + wave1–4, `git log`, `gh pr list`, CI GitHub Actions, pytest local.
**Không đọc:** `docs/knowledge.md`.

---

## 1. Tổng quan trạng thái Epic 5

| Nhóm | Task | Trạng thái |
|------|------|-----------|
| Runnable #66–#81 (16 task) | tất cả | **Đã merge vào `main`** qua 4 wave (PR #59–#74) |
| Gated #92 (Benchmark Wave B) | #92 | Code xong, [PR #75](https://github.com/thanhhale288/data-economy/pull/75) **OPEN — Backend tests FAIL** |
| Gated còn lại | #82–#91, #93, #94 | Chưa mở (đúng quy tắc gate) |

**Verify độc lập (2026-08-19):**

- Local `PYTHONPATH=. pytest -q` trên tip `main` (045c8f6): **491 passed** (85s).
- CI `main` 3 run gần nhất: **success**.
- PR #75: Frontend build pass, **Backend tests fail** (chi tiết §2.1).
- Checklist trong `epic5-remain-plan.md` và `docs/plan.md` **chưa tick** #66–#81 (các wave chờ lệnh `tick epic5`).

---

## 2. Fix được ngay (không cần dữ liệu ngoài / quyết định lớn)

### 2.1. PR #75 (task #92) fail CI — ĐÃ FIX trong lúc khảo sát ✔

- Nguyên nhân: test smoke của #68 `tests/benchmark/test_docai_extract_smoke.py::test_confirm_before_compare_is_frontend_gate` assert chuỗi `id="benchmark-upload-input"` / `requireConfirm` … phải nằm trong `frontend/src/pages/Benchmark.jsx`; #92 tách các phần đó sang `frontend/src/components/benchmark/BenchmarkForm.jsx` → assert fail.
- **Đã fix** bởi phiên làm task #92: commit `888582c` «Fix DocAI smoke test to read BenchmarkForm after Wave B split moved the confirm gate markup» đã push lên branch — chờ CI xanh rồi merge PR #75.
- Lưu ý: branch #92 còn 1 stash whitespace-only trên `handoff-task92.md` (`git stash list` — stash@{0}) — có thể drop.

### 2.2. Tick checklist Epic 5 (đợi user gọi `tick epic5`)

- 16 task merged nhưng `epic5-remain-plan.md` + bảng tiến độ `docs/plan.md` vẫn ghi «Plan (#65)». Docs-only, 1 commit.

### 2.3. Wave handoff chưa lưu vết

- `.scratch/handoff-wave1.md` … `handoff-wave4.md` đang **untracked** (chỉ trên máy local). Handoff từng task đã commit; batch wave thì chưa. Commit docs-only để không mất lịch sử.

### 2.4. LightGBM drift vẫn null — ops local, không cần data mới

- `data/models/ml_monitoring_baseline.json` chỉ có arima 31.70 / xgboost 6.44 / lstm 10.08; **lightgbm omitted** (`registry_missing`).
- #71 đã train được LightGBM trên Postgres local (MAPE 9.93) nhưng registry ghi từ worktree đã xóa (`artifact_path` sai).
- **Fix:** train lại từ checkout serve (`POST /api/ml/train` hoặc trainer script) → chạy `PYTHONPATH=. python3 scripts/write_ml_monitoring_baseline.py` → baseline có lightgbm, drift hết null. Không commit binary (`.gitignore` đã chặn).

### 2.5. Dọn sau merge

- `.worktrees/t66…t81` đã merge xong → `git worktree remove` được.
- Bundle FE > 500 kB (warning sẵn có): chunk-split Recharts qua `build.rollupOptions.manualChunks` — việc nhỏ, có thể gộp vào #92 hoặc 1 PR riêng.

### 2.6. FN matcher `led_chieusang_congnghiep` — fix được một phần

- TF-IDF hybrid miss case này (recall 0.9286); ST bắt được nhưng gate fail vì 1 FP.
- Có thể thêm QA/alias targeted từ dữ liệu **đã có** trong seed/cache (không invent) rồi re-eval. Nếu không đủ evidence → chuyển hướng tương lai (§3.4).

---

## 3. Không giải quyết được bây giờ → hướng tương lai

### 3.1. GEE SSL fail (#80)

- `https://gelex-electric.com` fail SSL **thật** — lỗi phía DN, ngoài tầm repo. Chip «chưa verify (SSL)» đã hiển thị đúng.
- **Hướng:** re-audit website định kỳ (script #40); khi DN sửa cert thì cập nhật provenance seed. Tuyệt đối không tắt SSL verify.

### 3.2. Scan PDF/ảnh vẫn trống khi thiếu OCR (#66/#69)

- Mặc định lazy-load, chưa cài PaddleOCR — FE đã honesty (`ocr_unavailable`).
- **Hướng:** (a) ops cài `requirements-ocr.txt` theo `docs/ops-demo.md` khi cần demo scan; (b) dài hạn là **#83 vision-LLM extract** — gate: user chấp nhận PII gửi API ngoài.

### 3.3. Narrative LLM chưa chạy live (#77)

- Config `*_LLM_BASE_URL` xong, test mock pass; chưa gọi mạng thật vì cần key.
- **Hướng:** user cấp key (OpenAI hoặc Gemini OpenAI-compatible) vào `.env` local → smoke 1 lần. Không log key, không commit.

### 3.4. Sentence-transformers runtime (#76)

- ST F1 0.9655 > TF-IDF 0.9630 nhưng **fail gate** (1 FP, precision 0.9333) → runtime giữ tfidf (đúng quy tắc).
- **Hướng:** mở rộng QA sample (hiện n=30, phần lớn negative mới), calibrate threshold ST riêng; chỉ bật `SHOP_MATCHER_BACKEND=sentence_transformers` khi gate pass **và** user đồng ý.

### 3.5. Feedback loop chưa có signal thật (#78/#79)

- Hạ tầng xong (CafeF/manual/DocAI đều POST signal; harvest CLI N≥3) nhưng JSONL demo chưa đủ N nên `proposed_aliases` rỗng.
- **Hướng:** cần usage thật; chạy `scripts/harvest_feedback_aliases.py` định kỳ, review đề xuất thủ công (không auto-apply). Retrain model = ngoài scope Epic 5.

### 3.6. Nhãn NLP đã cạn nguồn nội bộ (#75)

- Seed + live cache chỉ thêm được 3 tên (147 labels); positive shop QA đã cover hết handle trong seed.
- **Hướng:** nguồn nhãn mới chỉ đến từ **#84** (GMV live capture) hoặc **#85** (universe ingest) — cả hai gated vì cần data/quyền thật.

### 3.7. Golden extract coverage 0.73 (#70)

- Không phải bug: case partial/empty cố ý expected null (honesty). 9 case đều synthetic.
- **Hướng:** thêm BCTC thật đã redact (không PII) khi có nguồn; không tune threshold để đạt 1.0 giả.

### 3.8. Gated #82–#94 còn lại — điều kiện mở

| Task | Chờ gì |
|------|--------|
| #82 Energy intensity | Citation nguồn số GSO/BCTC thuyết minh (file .docx local chỉ là gợi ý) |
| #83 Vision-LLM extract | User chấp nhận PII ra API ngoài |
| #84 GMV live-cache | Capture live / `historical_sold` thật |
| #85 Universe ingest | Nguồn DN Section C + quyền truy cập |
| #86 Deep-sample expand | Sau #85 |
| #87 Proposal Mục 4 | Khi viết proposal học kỳ |
| #88 IIP theo VSIC 2+ | Table/series NSO |
| #89 Benchmark YoY | ≥2 kỳ BCTC đủ field trên peer |
| #90 VA_C SDMX dài | Crawl SDMX thật thành công |
| #91 LSTM AE anomaly | Chuỗi đủ dài + so sánh Isolation Forest |
| #93 Website classifier | Labeled HTML sample |
| #94 BCTC consistency | Không gate data — mở khi user gọi số |

---

## 4. Thứ tự đề xuất

1. Fix CI PR #75 (§2.1) → merge #92.
2. `tick epic5` + commit wave handoffs (§2.2–2.3).
3. Ops LightGBM registry + baseline (§2.4) — khép nốt gap #71/#72.
4. Dọn worktree + chunk-split Recharts (§2.5).
5. Các mục §3 để ngỏ đến khi đủ gate/data.

## Testing results (khảo sát này)

- Overall: **PASS** (audit; không đổi code)
- `PYTHONPATH=. pytest -q` trên `main` @ 045c8f6 → **491 passed**
- `gh pr list` → 16 PR Epic 5 merged; PR #75 open
- `gh pr checks 75` → Frontend pass, Backend **fail** (nguyên nhân §2.1)
- CI `main` 3 run gần nhất → success
