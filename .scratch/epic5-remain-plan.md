# Epic 5 — Productize remaining gaps

**Status:** planning (docs) — implement từng task trên branch riêng  
**Date:** 2026-08-19  
**Base:** `origin/main` @ `c2ec4f6` (đã gồm PR #57 cap 15 trang)  
**Inventory nguồn:** [`docs/guides/epic4-gaps-backlog.md`](../docs/guides/epic4-gaps-backlog.md), [`docs/plan.md`](../docs/plan.md), remain-1908 chat  
**Không đọc:** `docs/knowledge.md`

Epic 4 (#52–#64) **đã ship**. Epic 5 không làm lại DocAI/anomaly/NLP/narrative từ đầu — chỉ **khép gap**, **ops**, và **surface** những gì đã có.

---

## Bạn chỉ cần nói (điều khiển)

Không cần nhớ worktree / phase / conflict. Nói **một** trong các câu:

| Bạn nói | Agent làm |
|---------|-----------|
| `chạy task #66` (hoặc bất kỳ #66–#81) | Đúng **một** task: worktree + branch + code + test + PR |
| `chạy wave 1` | Tối đa 4 task **song song** của wave đó (xem bảng wave dưới) |
| `chạy tiếp` | Wave kế chưa xong; nếu wave đang dở thì hoàn thành nốt |
| `chạy task #82` … `#94` | Chỉ khi bạn **ghi đúng số gated** |

**Không nói:** “làm hết phase 5.1” — agent phải từ chối và hỏi lại số task hoặc số wave.

Chạy **theo task**, không theo phase. Phase chỉ là nhóm trong file này.

---

## Wave (tối ưu thời gian, tránh conflict)

Mỗi wave ≤ 4 agent. **Merge hết PR wave vào `main` rồi mới mở wave sau.**

| Wave | Task (song song) | Ghi chú |
|------|------------------|---------|
| **1** | **#66** #67 #71 #73 | Bắt đầu ngay (sau `main` có playbook Epic 5) |
| **2** | #77 #74 #72 #69 | #72 sau khi #71 đã merge |
| **3** | #78 #80 #70 #76 | #78 sau #66; #80 sau #74; #70 sau #67 |
| **4** | #68 #75 #79 #81 | #68/#81 sau #66+#78 (cùng `Benchmark.jsx`) |

Gated #82–#94: ngoài wave. Không tự mở.

### File nóng — không song song

| File | Chỉ 1 task tại một thời điểm |
|------|------------------------------|
| `frontend/src/pages/Benchmark.jsx` | #66 → #78 → #68 → #81 |
| `frontend/src/pages/CompanyDetail.jsx` | #74 → #80 |
| `backend/app/services/ml_monitoring.py` | #71 → #72 |
| `backend/app/services/bctc_extract.py` + golden | #67 → #70 |
| `docs/plan.md` + checklist file này | **Không** sửa trong PR feature. Tick `[x]` bằng 1 commit docs nhỏ **sau khi wave merge** (agent hoặc user bảo `tick epic5`) |

Lane độc lập (được song song): #67 · #69 · #71 · #73 · #74 · #76 · #77.

---

## Agent bắt buộc khi user nói `chạy task #N`

1. Đọc card Task #N trong **file này** (toàn bộ) + `CONTEXT.md` + `AGENTS.md`. FE → Hallmark skill.
2. **Không** implement trên `remain-1908` hay `main` checkout sẵn. Tạo worktree từ `origin/main`:

```bash
cd "/Users/hale/Code/AI in Data Economy"
git fetch origin
git worktree add ".worktrees/t<N>" -b cursor/epic5-phase<P>-task<N>-<slug> origin/main
```

`<P>` và `<slug>` lấy từ card task. Thư mục `.worktrees/` đã gitignore.

3. Làm việc **trong** `.worktrees/t<N>` (venv: `source` `.venv` của repo gốc; **không** copy `.env`).
4. Một task = một branch = một PR → `main`. Không làm task khác. Không gộp phase.
5. Test theo AC card. Handoff `.scratch/handoff-task<N>.md`. **Không** tick checklist file này / `docs/plan.md` trong cùng PR (tránh conflict 4 PR).
6. Xong: `git worktree remove .worktrees/t<N>` sau khi PR merge (nếu user không giữ).

**Cấm:** invent số GSO/OECD/CafeF; đổi Digital VA/VDEI; đọc `docs/knowledge.md`; commit `.env` / PDF PII / model binary.

Khi user nói `chạy wave K`: mở đúng các task của wave K, **mỗi task một worktree**, không mở task file nóng trùng bảng trên.

---

## Prompt khung (khi user không dán card, agent tự lấy)

User nói `chạy task #N` = đủ. Agent **tự** làm theo card #N (không bắt user copy prompt cuối card).

```
Repo: /Users/hale/Code/AI in Data Economy
User: chạy task #<N>
Đọc card #<N> trong .scratch/epic5-remain-plan.md + CONTEXT.md + AGENTS.md.
Worktree: .worktrees/t<N> từ origin/main, branch cursor/epic5-phase<P>-task<N>-<slug>
Một task = một PR. Không sửa docs/plan.md. Không invent số.
```

---

## Hệ thống đã có (Epic 1–4)

| Khu vực | Đã ship | Còn gap (Epic 5) |
|---------|---------|------------------|
| Macro | GSO IIP, VA_C fallback ngắn, OECD peer | VA_C chuỗi thật dài hơn; IIP theo ngành VSIC |
| DN mẫu | Seed ~28, CafeF BCTC, website audit | Chip URL fail; GEE SSL; GMV live (#41 paused) |
| Marketplace | Crawl allowlist+cache, hybrid matcher, categorizer **offline** | Categorizer chưa API/FE; ST runtime; nhãn nhỏ |
| Forecast | ARIMA / XGB / LSTM (+ LightGBM code) | LightGBM chưa train trên DB; drift baseline thiếu |
| Anomaly | Isolation Forest + ML Lab timeline | Chưa badge Dashboard; chưa LSTM AE |
| Benchmark / DocAI | Upload → extract → confirm → compare; cap 15 trang; rental ẩn UX | Scan thiếu OCR → form trống; alias chỉ VI; golden nhỏ |
| Narrative | Rules-first VI; LLM optional OpenAI URL cứng | Chưa `BASE_URL`; chưa đánh giá key |
| Monitoring | `GET /api/ml/monitoring`; feedback JSONL khi confirm DocAI | Drift null; chưa retrain; CafeF/manual chưa signal |
| FE | Hallmark pass đã trên `main` | Wave A Benchmark; chip URL; categorizer column |

**WIP đã xong trước Epic 5:** PR [#57](https://github.com/thanhhale288/data-economy/pull/57) cap extract/OCR 15 trang — **không** mở lại.

---

## Bản đồ phase

| Phase | Mục tiêu | Task |
|-------|----------|------|
| **5.0** | Plan | #65 (file này) |
| **5.1** | DocAI harden | #66–#70 |
| **5.2** | Forecast / anomaly productize | #71–#73 |
| **5.3** | Marketplace NLP ra sản phẩm | #74–#76 |
| **5.4** | Narrative + feedback | #77–#79 |
| **5.5** | FE leftover | #80–#81 |
| **5.6** | Gated — chỉ khi user gọi đúng số task | #82–#94 |

**Thứ tự:** dùng bảng **Wave** ở trên (không chạy tuần tự 16 task một file). User nói `chạy wave 1` hoặc `chạy task #66`.

---

# Phase 5.0 — Plan

### Task #65 — Epic 5 task breakdown

- **Status:** DONE (file này trên `remain-1908`)
- **Branch inventory:** `remain-1908` (docs; không phải branch implement)
- **Slug implement:** không — đây là tài liệu

**Đã có:** Epic 4 #52–#64 trên `main`; backlog [`docs/guides/epic4-gaps-backlog.md`](../docs/guides/epic4-gaps-backlog.md).  
**Nhiệm vụ:** chia inventory thành task agent-ready.  
**Không làm lại.**

---

# Phase 5.1 — DocAI harden

### Task #66 — FE honesty khi OCR/cap trang

- **Cỡ:** S · **Blocked by:** none  
- **Branch:** `cursor/epic5-phase1-task66-docai-extract-honesty-ux`

**Hệ thống đã có**

- `POST /api/benchmark/extract` trả `warnings` gồm `ocr_unavailable`, `no_extractable_fields`, `pages_capped:15` (service OCR + PR #57).
- [`frontend/src/pages/Benchmark.jsx`](../frontend/src/pages/Benchmark.jsx) hiện `extractMeta.warnings.join(', ')` — user thấy mã kỹ thuật, form trống khi scan không OCR.

**Nhiệm vụ**

Đổi copy honesty tiếng Việt theo warning đã có. Không cài PaddleOCR. Không đổi mapper.

**Hướng triển khai**

1. Map warning → câu VI, ví dụ: `ocr_unavailable` → server chưa có OCR, dùng CafeF prefill hoặc PDF chữ; `pages_capped:15` → chỉ đọc 15 trang đầu.
2. Banner `banner-warn` (token sẵn); không inline hex.
3. Giữ confirm-before-compare; null field không bịa 0.
4. Test: không bắt buộc RTL e2e; ít nhất assert helper map warning nếu tách module nhỏ, hoặc comment snapshot copy trong handoff + `npm run build`.

**AC**

- [ ] `ocr_unavailable` không còn chỉ hiện raw token
- [ ] `pages_capped:15` giải thích được
- [ ] Không auto-compare; không sửa `bctc_extract.py`

**Out of scope:** vision-LLM (#85); cài OCR (#69 ops).

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #66 Epic 5 — FE honesty OCR/pages_capped.
Đọc CONTEXT.md, AGENTS.md, .scratch/epic5-remain-plan.md card #66, .agents/skills/hallmark/SKILL.md.
Branch: cursor/epic5-phase1-task66-docai-extract-honesty-ux từ origin/main.
Sửa Benchmark.jsx (+ index.css token nếu cần). Không cài PaddleOCR. Không đổi extract math.
Verify: cd frontend && npm run build
Handoff: .scratch/handoff-task66.md
```

---

### Task #67 — Alias tiếng Anh cho extract

- **Cỡ:** S–M · **Blocked by:** none  
- **Branch:** `cursor/epic5-phase1-task67-bctc-english-aliases`

**Hệ thống đã có**

- `_LABEL_ALIASES` trong [`backend/app/services/bctc_extract.py`](../backend/app/services/bctc_extract.py) — nhãn VI đã bỏ dấu.
- Unit scale: `nghìn` / `triệu`; `extract_fields_from_lines` dùng chung text + OCR.
- Golden: [`tests/benchmark/golden/extract_golden_cases.json`](../tests/benchmark/golden/extract_golden_cases.json).

**Nhiệm vụ**

PDF text tiếng Anh map được field whitelist (revenue, PBT, employees, assets, equity). OCR `lang` không bắt buộc đổi nếu text-PDF đủ.

**Hướng triển khai**

1. Thêm alias English, dài trước ngắn: `profit before tax`, `net revenue`, `revenue from sales`, `total assets`, `owners equity` / `owner's equity`, `total equity`, `employees` / `number of employees`.
2. Unit: `in millions of dong/VND`, `VND million`, `in thousands`.
3. Fixture PDF text English (synthetic, không PII) + 1 golden case.
4. Không hạ `DEFAULT_FIELD_CONFIDENCE_THRESHOLD`. Honesty: không match → null + `missing_field:*`.

**AC**

- [ ] Fixture English map ≥ các field `EXTRACT_FIELDS` khi nhãn chuẩn
- [ ] Test VI cũ không regress (`tests/benchmark/test_bctc_extract.py`)
- [ ] `PYTHONPATH=. pytest -q tests/benchmark/ -k extract`

**Out of scope:** scan OCR lang=en (#85); golden BCTC HOSE thật (#70).

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #67 Epic 5 — English aliases BCTC extract.
Đọc CONTEXT.md, AGENTS.md, card #67 trong .scratch/epic5-remain-plan.md, backend/app/services/bctc_extract.py.
Branch: cursor/epic5-phase1-task67-bctc-english-aliases từ origin/main.
Chỉ rules/aliases + fixture + golden. Không API/FE/OCR deps.
Verify: PYTHONPATH=. pytest -q tests/benchmark/ -k extract
Handoff: .scratch/handoff-task67.md
```

---

### Task #68 — Smoke UI / e2e extract flow

- **Cỡ:** S · **Blocked by:** #66 nên merge trước (copy warning), không cứng  
- **Branch:** `cursor/epic5-phase1-task68-docai-extract-smoke`

**Hệ thống đã có**

- Flow FE upload → prefill → confirm → compare; test API extract; `vite build`.
- Fixtures: `tests/benchmark/fixtures/` (text PDF + scan PNG).

**Nhiệm vụ**

Một đường smoke lặp lại được: text-PDF fixture đi hết confirm (không bắt compare có DB đầy). Playwright **hoặc** script + checklist `docs/ops-demo.md` — chọn Playwright nếu `frontend` đã có dev server pattern; không thêm SaaS.

**Hướng triển khai**

1. Ưu tiên Playwright hit `POST /extract` + UI confirm trên fixture text (không cần OCR extra).
2. Scan path: ghi rõ skip nếu `ocr_unavailable`.
3. Không đổi math compare.

**AC**

- [ ] Có lệnh trong handoff: pass text-PDF; scan skip/honesty
- [ ] CI: e2e optional/`pytest.mark.e2e` để default CI không phụ thuộc browser nếu nặng — ghi rõ

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #68 Epic 5 — smoke/e2e DocAI upload→confirm.
Đọc card #68 .scratch/epic5-remain-plan.md, frontend/src/pages/Benchmark.jsx, tests/benchmark/fixtures/.
Branch: cursor/epic5-phase1-task68-docai-extract-smoke từ origin/main.
Không đổi extract mapper. Không invent số compare.
Handoff: .scratch/handoff-task68.md kèm lệnh đã chạy.
```

---

### Task #69 — OCR ops note (lazy-load vs Docker bake)

- **Cỡ:** S · **Blocked by:** none · **Chủ yếu docs**  
- **Branch:** `cursor/epic5-phase1-task69-ocr-ops-note`

**Hệ thống đã có**

- [`requirements-ocr.txt`](../requirements-ocr.txt); lazy PaddleOCR; model `~/.paddlex`; [`backend/Dockerfile`](../backend/Dockerfile) chưa bake OCR.

**Nhiệm vụ**

Quyết định **ghi rõ**: mặc định lazy-load + ops note; **không** bake image trừ khi user yêu cầu trong chat này. File: `docs/ops-demo.md` (hoặc `docs/guides/ocr-ops.md`) — cài extra, biến `PADDLE_*`, lần đầu chậm, workaround CafeF.

**AC**

- [ ] Ops note: cài / không cài / FE sẽ hiện gì (#66)
- [ ] Không đổi formula; không commit model OCR

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #69 Epic 5 — OCR ops note.
Đọc card #69, requirements-ocr.txt, backend/app/services/bctc_extract_ocr.py, Dockerfile.
Branch: cursor/epic5-phase1-task69-ocr-ops-note từ origin/main.
Chỉ docs trừ khi user bảo bake Docker. Không commit ~/.paddlex.
Handoff: .scratch/handoff-task69.md
```

---

### Task #70 — Golden set extract (de-identified)

- **Cỡ:** M · **Blocked by:** #67 nên có nếu thêm case English  
- **Branch:** `cursor/epic5-phase1-task70-extract-golden-realish`

**Hệ thống đã có**

- [`backend/app/services/bctc_extract_eval.py`](../backend/app/services/bctc_extract_eval.py), `scripts/eval_benchmark_extract.py`, 3 case synthetic.

**Nhiệm vụ**

Thêm 2–5 case **không PII** (tự tạo layout HOSE-like hoặc redacted). Không commit PDF công ty thật. Chạy eval, ghi accuracy/coverage mới (có thể < 1.0 — không tune để đạt 1.0 giả).

**AC**

- [ ] Golden > 3 cases; eval script chạy
- [ ] Handoff giải thích coverage; không bịa field

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #70 Epic 5 — mở rộng golden extract, không PII.
Đọc card #70, bctc_extract_eval.py, tests/benchmark/golden/.
Branch: cursor/epic5-phase1-task70-extract-golden-realish từ origin/main.
Không commit BCTC DN thật. Không hạ honesty threshold để tăng accuracy.
Verify: PYTHONPATH=. python3 scripts/eval_benchmark_extract.py
Handoff: .scratch/handoff-task70.md
```

---

# Phase 5.2 — Forecast & anomaly

### Task #71 — Train LightGBM + registry

- **Cỡ:** S (ops + nhỏ code) · **Blocked by:** none  
- **Branch:** `cursor/epic5-phase2-task71-lightgbm-train-ops`

**Hệ thống đã có**

- [`ml/models/lightgbm_model.py`](../ml/models/lightgbm_model.py), `train_all_models` gọi LightGBM; FE card trống nếu registry thiếu.
- [`CANONICAL_MODELS`](../backend/app/services/ml_monitoring.py) = `arima, xgboost, lstm` — **chưa** `lightgbm`.

**Nhiệm vụ**

1. Đưa `lightgbm` vào canonical monitoring + artifact candidates (`lightgbm_model.joblib`, `lightgbm_importance.json`).
2. Docs/ops: lệnh train (`POST /api/ml/train` hoặc script trainer) trên DB local; **không** commit `.pt/.joblib` lớn nếu gitignore cấm.
3. Soft-fail nếu thiếu `lightgbm` giữ nguyên.

**AC**

- [ ] Monitoring liệt kê lightgbm (metrics null + warning nếu chưa train — honesty)
- [ ] Handoff: lệnh train đã chạy **hoặc** lý do DB trống
- [ ] `PYTHONPATH=. pytest -q tests/ml/ -k 'lightgbm or ml_monitoring'`

**Không:** đổi target `iip`; không cài darts.

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #71 Epic 5 — LightGBM train/ops + monitoring candidate.
Đọc card #71, ml/models/lightgbm_model.py, ml_monitoring.py CANONICAL_MODELS, tests/ml/test_lightgbm.py.
Branch: cursor/epic5-phase2-task71-lightgbm-train-ops từ origin/main.
Target vẫn iip. Không commit model binary nếu repo ignore.
Handoff: .scratch/handoff-task71.md
```

---

### Task #72 — Drift baseline file

- **Cỡ:** S · **Blocked by:** #71 nếu muốn có MAPE LightGBM; có thể làm chỉ 3 model cũ  
- **Branch:** `cursor/epic5-phase2-task72-ml-drift-baseline`

**Hệ thống đã có**

- Drift = current MAPE − baseline MAPE; không file → `drift_flag`/`drift_score` = null.
- Schema [`MlMonitoringBaselineIn`](../backend/app/schemas/ml_monitoring.py); tests trong `tests/ml/test_ml_monitoring.py`.

**Nhiệm vụ**

Tạo `data/models/ml_monitoring_baseline.json` từ MAPE registry **thật** nếu có; nếu registry trống — script `scripts/write_ml_monitoring_baseline.py` ghi từ registry + warning, **không bịa MAPE**. Docs: cập nhật baseline sau retrain đạt chuẩn.

**AC**

- [ ] Format JSON khớp service (per-model mape)
- [ ] Test: có baseline → drift tính được; thiếu file → vẫn null
- [ ] Không invent mape

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #72 Epic 5 — ml_monitoring_baseline.json từ registry thật.
Đọc card #72, backend/app/services/ml_monitoring.py, tests/ml/test_ml_monitoring.py.
Branch: cursor/epic5-phase2-task72-ml-drift-baseline từ origin/main.
Không bịa MAPE. Nếu registry trống: script + honesty, không fake baseline.
Handoff: .scratch/handoff-task72.md
```

---

### Task #73 — Anomaly chip trên Dashboard

- **Cỡ:** S · **Blocked by:** none (`GET /api/ml/anomaly` đã có)  
- **Branch:** `cursor/epic5-phase2-task73-dashboard-anomaly-chip`

**Hệ thống đã có**

- [`GET /api/ml/anomaly`](../backend/app/api/anomaly.py); timeline [`MLLab.jsx`](../frontend/src/pages/MLLab.jsx); Dashboard chưa gọi.

**Nhiệm vụ**

Chip/banner nhỏ trên Dashboard: kỳ IIP mới nhất flagged → cảnh báo; `available=false` hoặc series ngắn → **ẩn**, không bịa alert. Hallmark: không marketing glow.

**Hướng triển khai**

1. `api.getAnomalies` đã có [`frontend/src/api.js`](../frontend/src/api.js).
2. [`Dashboard.jsx`](../frontend/src/pages/Dashboard.jsx): 1 chỗ gần IIP/forecast; honesty copy.
3. Không sửa `ml/anomaly/detector.py`.

**AC**

- [ ] Thiếu data → không hiện điểm giả
- [ ] `npm run build`; optional test nếu có dashboard test helper

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #73 Epic 5 — anomaly chip Dashboard.
Đọc card #73, Dashboard.jsx, api.getAnomalies, .agents/skills/hallmark/SKILL.md.
Branch: cursor/epic5-phase2-task73-dashboard-anomaly-chip từ origin/main.
Không sửa detector. Honesty: ẩn khi unavailable.
Verify: cd frontend && npm run build
Handoff: .scratch/handoff-task73.md
```

---

# Phase 5.3 — Marketplace NLP

### Task #74 — Categorizer API + cột FE

- **Cỡ:** M · **Blocked by:** none  
- **Branch:** `cursor/epic5-phase3-task74-categorizer-api-fe`

**Hệ thống đã có**

- Offline [`ml/product_categorizer/`](../ml/product_categorizer/): TF-IDF + LR; abstain `unknown` / low confidence.
- Listing hiện [`CompanyDetail.jsx`](../frontend/src/pages/CompanyDetail.jsx) (`product_name`, price, units) — **không** có trang Marketplace riêng.

**Nhiệm vụ**

`POST /api/ml/categorize` (hoặc `/api/marketplace/categorize`) nhận `product_name` → `{vsic_code, confidence, reason}` (null khi abstain). FE: cột “VSIC dự đoán” trên listing Company detail. Abstain → "—" + title reason.

**Hướng triển khai**

1. Service mỏng wrap `ProductCategorizer`; không train trong request.
2. Whitelist Section C giữ nguyên.
3. Test API happy + OOV.
4. FE Hallmark: cột thêm, không đổi IA.

**AC**

- [ ] Abstain không bịa mã
- [ ] pytest categorizer + API; `npm run build`

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #74 Epic 5 — product categorizer API + cột listing CompanyDetail.
Đọc card #74, ml/product_categorizer/, CompanyDetail.jsx, CONTEXT.md VSIC.
Branch: cursor/epic5-phase3-task74-categorizer-api-fe từ origin/main.
Không sửa shop_matcher. Abstain → null. Hallmark khi sửa FE.
Handoff: .scratch/handoff-task74.md
```

---

### Task #75 — Mở rộng nhãn categorizer / matcher QA

- **Cỡ:** M (gán nhãn) · **Blocked by:** none; tốt hơn sau #74  
- **Branch:** `cursor/epic5-phase3-task75-nlp-label-expand`

**Hệ thống đã có**

- `data/seeds/product_categorizer_labels.json` (~122 train); shop QA `data/seeds/shop_matcher_qa_sample.json` n=22.

**Nhiệm vụ**

Thêm nhãn từ listing **đã có trong seed/DB/cache** (không invent tên shop). Re-eval precision; **không** hạ threshold chỉ để giữ 1.0. Ghi report trong handoff.

**AC**

- [ ] Eval scripts chạy; gate matcher không tụt giả
- [ ] Provenance: nguồn từng nhãn mới

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #75 Epic 5 — mở rộng nhãn NLP từ listing có sẵn, không invent.
Đọc card #75, data/seeds/product_categorizer_labels.json, shop_matcher_qa_sample.json.
Branch: cursor/epic5-phase3-task75-nlp-label-expand từ origin/main.
Không bịa GMV/units. Re-tune threshold chỉ khi có evidence trên sample mới.
Handoff: .scratch/handoff-task75.md + bảng precision trước/sau.
```

---

### Task #76 — Shop matcher ST mid-band (eval, optional runtime)

- **Cỡ:** S–M · **Blocked by:** none  
- **Branch:** `cursor/epic5-phase3-task76-shop-matcher-st-eval`

**Hệ thống đã có**

- Hybrid RapidFuzz + TF-IDF default; `sentence-transformers==3.3.1` pin; runtime **tfidf**.
- FN còn: `led_chieusang_congnghiep`.

**Nhiệm vụ**

Chạy `scripts/eval_shop_matcher.py --backend sentence_transformers` (offline, có thể tải model lần đầu — không commit model). Báo F1 vs tfidf. **Mặc định runtime vẫn tfidf** trừ khi gate tăng **và** user trong chat này bảo bật flag env.

**AC**

- [ ] Handoff: bảng fuzzy / tfidf / ST
- [ ] CI mặc định không download Hub
- [ ] Nếu thêm env `SHOP_MATCHER_BACKEND` — default `tfidf`

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #76 Epic 5 — eval shop matcher sentence-transformers, runtime default tfidf.
Đọc card #76, ml/shop_matcher/, scripts/eval_shop_matcher.py.
Branch: cursor/epic5-phase3-task76-shop-matcher-st-eval từ origin/main.
Không bật ST runtime trừ khi gate rõ và user đồng ý trong chat.
Không sửa scraper Shopee/TikTok.
Handoff: .scratch/handoff-task76.md
```

---

# Phase 5.4 — Narrative & feedback

### Task #77 — LLM BASE_URL + model env

- **Cỡ:** S · **Blocked by:** none  
- **Branch:** `cursor/epic5-phase4-task77-narrative-llm-base-url`

**Hệ thống đã có**

- [`benchmark_narrative.py`](../backend/app/services/benchmark_narrative.py) / [`forecast_narrative.py`](../backend/app/services/forecast_narrative.py) POST cứng `https://api.openai.com/v1/chat/completions`.
- Honesty gate số; fallback rules nếu thiếu key / fail.

**Nhiệm vụ**

Env: `BENCHMARK_NARRATIVE_LLM_BASE_URL`, `FORECAST_NARRATIVE_LLM_BASE_URL` (fallback `NARRATIVE_LLM_BASE_URL` / OpenAI default), + model name đã có. Test monkeypatch URL. Không bắt buộc gọi mạng thật.

**AC**

- [ ] Key Gemini + OpenAI-compatible base URL dùng được về mặt config
- [ ] Honesty gate không nới
- [ ] `pytest -q tests/benchmark/ -k narrative` và `tests/ml/ -k narrative`

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #77 Epic 5 — narrative LLM_BASE_URL.
Đọc card #77, benchmark_narrative.py, forecast_narrative.py (chỗ api.openai.com).
Branch: cursor/epic5-phase4-task77-narrative-llm-base-url từ origin/main.
Không nới honesty. Không log key. Tests mock HTTP.
Handoff: .scratch/handoff-task77.md
```

---

### Task #78 — Feedback CafeF + manual

- **Cỡ:** S · **Blocked by:** none  
- **Branch:** `cursor/epic5-phase4-task78-feedback-cafef-manual`

**Hệ thống đã có**

- Schema `source_type` đã allow `cafef_prefill` / `manual`; POST chỉ lúc confirm DocAI ([`Benchmark.jsx`](../frontend/src/pages/Benchmark.jsx) ~795).

**Nhiệm vụ**

Gửi signal khi user confirm sau CafeF prefill hoặc sau sửa form nhập tay (cùng checkbox confirm hoặc confirm compare). Không lưu raw PDF. Diff allowlisted fields như #64.

**AC**

- [ ] Test FE không bắt buộc; backend nhận `source_type` đã có
- [ ] Không double-count nếu cùng session — ghi quy tắc trong handoff
- [ ] pytest `tests/benchmark/ -k feedback`

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #78 Epic 5 — feedback signal CafeF + manual.
Đọc card #78, backend/app/services/feedback_signal.py, Benchmark.jsx postFeedbackSignal.
Branch: cursor/epic5-phase4-task78-feedback-cafef-manual từ origin/main.
Không persist raw PDF/secret. Không đổi compare math.
Handoff: .scratch/handoff-task78.md
```

---

### Task #79 — Harvest alias từ feedback (v1, không auto-retrain model)

- **Cỡ:** M · **Blocked by:** #78 giúp nhiều signal hơn, không cứng  
- **Branch:** `cursor/epic5-phase4-task79-feedback-alias-harvest`

**Hệ thống đã có**

- JSONL `data/feedback/training_signals.jsonl`; scheduler chỉ đếm; chưa học.

**Nhiệm vụ v1**

Script đọc JSONL → đề xuất alias/rules khi **≥N** lần user sửa cùng field (N mặc định 3, config). **Không** tự ghi `_LABEL_ALIASES` lúc runtime. Output: report markdown + optional JSON đề xuất. Không Prefect.

**AC**

- [ ] Không apply im lặng vào extract
- [ ] Không chứa raw doc trong report
- [ ] Test với JSONL fixture

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #79 Epic 5 — harvest alias từ feedback JSONL, không auto-apply.
Đọc card #79, feedback_signal.py, bctc_extract.py aliases.
Branch: cursor/epic5-phase4-task79-feedback-alias-harvest từ origin/main.
Không Prefect. Không retrain sklearn/OCR. Không ghi secret.
Handoff: .scratch/handoff-task79.md
```

---

# Phase 5.5 — FE leftover

### Task #80 — Chip URL website fail

- **Cỡ:** S · **Blocked by:** none  
- **Branch:** `cursor/epic5-phase5-task80-website-url-fail-chip`

**Hệ thống đã có**

- Audit #40: 27/28 website_ok; GEE SSL fail (biên bản `.scratch/archive/epic3/epic3-task40-website-domain-fix.md`).
- [`Companies.jsx`](../frontend/src/pages/Companies.jsx) / [`CompanyDetail.jsx`](../frontend/src/pages/CompanyDetail.jsx) hiện URL; chưa chip “chưa verify / fail”.

**Nhiệm vụ**

Chip honesty khi website không verify được (dùng field API/seed **đã có** — `last_http_status` / provenance / detector). **Không** bịa checkout. Không tắt SSL verify.

**Hướng triển khai**

1. Tìm field hiện có trên company/digital_presence API; nếu thiếu status — chỉ chip khi URL có + detector unknown/fail đã serialize. Không invent HTTP.
2. Hallmark: chip không pill glow 999px nếu token repo đã bỏ.

**AC**

- [ ] GEE (hoặc fixture fail) nhìn thấy trạng thái fail/unknown
- [ ] Ticker OK không bị gắn fail
- [ ] `npm run build`

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #80 Epic 5 — chip URL website fail/unknown.
Đọc card #80, Companies.jsx, CompanyDetail.jsx, company API schema, .agents/skills/hallmark/SKILL.md.
Branch: cursor/epic5-phase5-task80-website-url-fail-chip từ origin/main.
Không tắt SSL verify. Không suy checkout từ fail.
Handoff: .scratch/handoff-task80.md
```

---

### Task #81 — Benchmark Wave A (industry context)

- **Cỡ:** S–M · **Blocked by:** none  
- **Branch:** `cursor/epic5-phase5-task81-benchmark-wave-a`

**Hệ thống đã có**

- Roadmap [`docs/guides/frontend-benchmark-roadmap.md`](../docs/guides/frontend-benchmark-roadmap.md) Wave A.
- Hallmark pass; rental ẩn UX; DocAI upload primary CTA.

**Nhiệm vụ**

Header + breadcrumb + khối industry context **trên form**: peer = mẫu niêm yết VSIC 2-digit, không census GSO. Thiếu số nguồn → N/A / ẩn, không bịa bảng ngành.

**AC**

- [ ] Copy honesty; không GSO giả
- [ ] Không đổi `benchmark_service.py` math
- [ ] Không làm Wave B split components
- [ ] `npm run build`

**Prompt agent**

```
Repo: /Users/hale/Code/AI in Data Economy
Một chat = một task. Không đọc docs/knowledge.md.
Làm Task #81 Epic 5 — Benchmark Wave A header/breadcrumb/industry context.
Đọc card #81, docs/guides/frontend-benchmark-roadmap.md, Benchmark.jsx, CONTEXT.md Benchmark, hallmark skill.
Branch: cursor/epic5-phase5-task81-benchmark-wave-a từ origin/main.
Không invent GSO. Không Wave B. Không đổi percentile math.
Handoff: .scratch/handoff-task81.md
```

---

# Phase 5.6 — Gated (không mở agent trừ khi user ghi rõ Task #N)

Mỗi card gated: **GATE** + điều kiện. Agent thấy “làm Epic 5” mà không nêu số gated → **bỏ qua**.

### Task #82 — Energy intensity (nguồn thật)

- **GATE:** user dán Task #82 **và** chỉ citation nguồn số (GSO/BCTC thuyết minh). File local `docs/Ngành công nghiệp chủ yếu vào năng lượng….docx` chỉ là gợi ý — **không** phải nguồn số.
- **Branch:** `cursor/epic5-phase6-task82-energy-intensity-spike`
- Spike đọc nguồn → mapping + PROVENANCE; không bịa kWh/tấn. Cần ADR nếu đụng Digital VA. P3 trong epic4 plan.

### Task #83 — Vision-LLM extract (Gemini)

- **GATE:** user chấp nhận PII gửi API ngoài.
- Rasterize pypdfium2 → JSON whitelist + confidence; human confirm; honesty gate. Có thể cover English.
- **Branch:** `cursor/epic5-phase6-task83-vision-llm-extract`

### Task #84 — #41 GMV backfill live-cache

- **GATE:** có capture live/`historical_sold` thật. Không invent units.
- Paused Epic 3. **Branch:** `cursor/epic5-phase6-task84-gmv-live-cache`

### Task #85 — #48 Universe nông ingest

- **GATE:** nguồn DN Section C + quyền truy cập. Không copy seed thành vũ trụ.
- **Branch:** `cursor/epic5-phase6-task85-universe-ingest`

### Task #86 — #49 Deep-sample expand

- **GATE:** sau #85. Không invent trăm BCTC.
- **Branch:** `cursor/epic5-phase6-task86-deep-sample-expand`

### Task #87 — #19b Proposal Mục 4

- **GATE:** khi viết proposal học kỳ. Không invent số demo thành official.
- **Branch:** `cursor/epic5-phase6-task87-proposal-muc-4`

### Task #88 — IIP theo ngành VSIC 2+

- **GATE:** có table/series NSO. Unlock «Ngành nổi bật».
- **Branch:** `cursor/epic5-phase6-task88-iip-by-vsic`

### Task #89 — Benchmark xu hướng theo năm

- **GATE:** ≥2 kỳ BCTC đủ field trên peer.
- **Branch:** `cursor/epic5-phase6-task89-benchmark-yoy`

### Task #90 — VA_C SDMX dài hơn (bỏ fallback ngắn)

- **GATE:** crawl SDMX thật thành công; không copy số.
- **Branch:** `cursor/epic5-phase6-task90-va-c-live-sdmx`

### Task #91 — LSTM autoencoder anomaly

- **GATE:** chuỗi đủ dài; so sánh với Isolation Forest, không thay im lặng.
- **Branch:** `cursor/epic5-phase6-task91-lstm-ae-anomaly`

### Task #92 — Benchmark Wave B componentize

- Split `frontend/src/components/benchmark/*`. Không đổi API.
- **Branch:** `cursor/epic5-phase6-task92-benchmark-wave-b`

### Task #93 — Website brochure vs commerce classifier

- P2 epic4. Cần labeled HTML sample.
- **Branch:** `cursor/epic5-phase6-task93-website-digital-classifier`

### Task #94 — BCTC consistency vs lịch sử ticker

- So extract/CafeF với `financial_reports` cùng ticker; flag lệch; không overwrite im lặng.
- **Branch:** `cursor/epic5-phase6-task94-bctc-consistency-check`

---

## Checklist nóng (copy sang `docs/plan.md` khi đóng)

**Runnable**

- [x] #65 Epic 5 plan
- [ ] #66 FE extract honesty
- [ ] #67 English aliases
- [ ] #68 Smoke/e2e
- [ ] #69 OCR ops note
- [ ] #70 Golden expand
- [ ] #71 LightGBM train/ops
- [ ] #72 Drift baseline
- [ ] #73 Dashboard anomaly chip
- [ ] #74 Categorizer API/FE
- [ ] #75 NLP labels
- [ ] #76 Matcher ST eval
- [ ] #77 LLM BASE_URL
- [ ] #78 Feedback CafeF/manual
- [ ] #79 Alias harvest
- [ ] #80 URL fail chip
- [ ] #81 Benchmark Wave A

**Gated:** #82–#94 — không tick cho đến khi user mở.
