# Tour Task #57–#64 — Epic 4 (anomaly → feedback)

Tài liệu catch-up: mục đích, cách làm, kết quả test, và khoảng trống còn lại.
Nguồn: `.scratch/handoff-task5[7-9].md`, `.scratch/handoff-task6[0-3].md`, handoff #64 trên branch task, `.scratch/epic4-ai-ml-plan.md`. Không đọc `docs/knowledge.md`.

**Ngày tổng hợp:** 2026-07-30  
**Epic:** Epic 4 — AI / ML / DL  
**Phạm vi phase:** 4.2 Forecast & anomaly → 4.3 Marketplace NLP → 4.4 Assist UX → 4.5 Monitoring & feedback

---

## 0. Bản đồ 30 giây

| Task | Tên dễ hiểu | Phase | PR | Trạng thái artifact |
|------|-------------|-------|----|---------------------|
| #57 | Phát hiện bất thường IIP/VA | 4.2 | [#45](https://github.com/thanhhale288/data-economy/pull/45) | DONE |
| #58 | Panel anomaly + LightGBM trên ML Lab | 4.2 | [#49](https://github.com/thanhhale288/data-economy/pull/49) | DONE |
| #59 | Phân loại tên SP → VSIC 4 số | 4.3 | [#46](https://github.com/thanhhale288/data-economy/pull/46) | DONE |
| #60 | Ghép shop marketplace hybrid | 4.3 | [#50](https://github.com/thanhhale288/data-economy/pull/50) | DONE |
| #61 | Giải thích benchmark bằng tiếng Việt | 4.4 | [#47](https://github.com/thanhhale288/data-economy/pull/47) | DONE |
| #62 | Giải thích dự báo IIP | 4.4 | [#51](https://github.com/thanhhale288/data-economy/pull/51) | DONE |
| #63 | Hợp đồng giám sát chất lượng model | 4.5 | [#48](https://github.com/thanhhale288/data-economy/pull/48) | DONE |
| #64 | Lưu chỉnh sửa user thành training signal | 4.5 | [#52](https://github.com/thanhhale288/data-economy/pull/52) | DONE (merged 2026-07-30) |

**Luồng end-to-end (tóm tắt):**

1. GSO IIP/VA → Isolation Forest anomaly (#57) → hiện timeline trên ML Lab (#58).
2. Train thêm LightGBM cạnh ARIMA/XGB/LSTM (#58).
3. Tên sản phẩm marketplace → VSIC (#59); tên shop → ticker hybrid (#60).
4. Sau compare / forecast → narrative tiếng Việt chỉ cite số API (#61–#62).
5. Pipeline Monitor đọc chất lượng/drift (#63); chỉnh sửa DocAI prefill → JSONL feedback (#64).

---

## Task #57 — Anomaly detector v1 (IIP/VA)

**Một câu:** Tìm điểm bất thường trên chuỗi IIP (và tùy chọn VA) bằng Isolation Forest, trả API — không bịa alert khi thiếu dữ liệu.

### Mục đích

Epic plan hứa anomaly trên IIP/VA. Task này dựng **pipeline + API** trước; FE để #58.

### Bao gồm gì

- `ml/anomaly/detector.py` — Isolation Forest trên feature lag/roll/growth; `random_state=42`; ngưỡng baseline = boundary sklearn `0.0`.
- `backend/app/services/anomaly_service.py` — đọc `IIP_C` (+ optional VA) từ `gso_macro`; không ghi DB.
- `GET /api/ml/anomaly` — query `vsic_code`, `include_va`, `va_indicator`, `contamination`.
- Series ngắn/rỗng → `available=false`, `points=[]`, warning rõ (không invent flag).

### Làm như thế nào

1. Pre-flight: `sklearn` + `torch` đã có; không thêm darts.
2. Feature hóa chuỗi → Isolation Forest → score + flag.
3. Wire service + router dưới `/api/ml`.
4. Test unit detector + API (empty DB honesty).

### Test đã chạy

```bash
PYTHONPATH=. pytest -q tests/ml/ -k anomaly
# 10 passed, 30 deselected
```

Smoke: OpenAPI có `/api/ml/anomaly`; DB trống → `available=false`.

### Khoảng trống lúc đóng

- Chưa có UI ML Lab.
- Chưa LightGBM / model compare refresh.
- Không LSTM autoencoder (Isolation Forest đủ v1).

### Task sau cải thiện

#58 gắn timeline FE + thêm LightGBM vào compare.

---

## Task #58 — ML Lab anomaly panel + LightGBM

**Một câu:** Hiện timeline anomaly trên ML Lab và thêm đường train/forecast LightGBM cạnh các model cũ.

### Mục đích

Hoàn phase 4.2: người dùng thấy anomaly + so sánh thêm LightGBM (deps đã có từ trước, chưa có train path).

### Bao gồm gì

- `ml/models/lightgbm_model.py` — cùng feature frame với XGBoost; target vẫn `iip`; soft-fail nếu thiếu package.
- Artifact: `lightgbm_model.joblib`, `lightgbm_features.joblib`, `lightgbm_importance.json`.
- `trainer.py` / `ml_lab_service.py` — train + feature importance.
- FE `MLLab.jsx` — anomaly timeline (`GET /api/ml/anomaly`) + card LightGBM.
- API client: `getAnomalies`, `getLightgbmFeatureImportance`, `forecastLightgbm`.

### Làm như thế nào

1. Xác nhận `lightgbm` import được (vd. 4.5.0).
2. Implement train path song song XGB; không sửa core `ml/anomaly/**`.
3. Wire FE compare + anomaly banner khi series thiếu.
4. Pytest `tests/ml/` (gồm LightGBM + importance).

### Test đã chạy

```bash
python3 -c "import lightgbm; print(lightgbm.__version__)"  # 4.5.0
PYTHONPATH=. pytest -q tests/ml/
# 50 passed
```

### Khoảng trống lúc đóng

- LightGBM chỉ hiện sau train thành công có metrics.
- Monitoring (#63 lúc đó) chưa liệt kê LightGBM trong contract candidates (out of scope #58).
- Anomaly panel vẫn honesty-first khi thiếu series.

### Task sau cải thiện

#62 đọc được `lightgbm_importance.json` cho narrative; #63 có thể track thêm model nếu mở rộng candidates.

---

## Task #59 — Product categorizer seed model

**Một câu:** Map tên sản phẩm marketplace → mã VSIC 4 số (Section C), hoặc bỏ trống nếu không chắc.

### Mục đích

Marketplace NLP: phân loại ngành từ tên SP với labeled sample nhỏ + precision report — không gắn FE/API marketplace trong task này.

### Bao gồm gì

- `ml/product_categorizer/` — TF-IDF (`char_wb` 3–5) + LogisticRegression.
- Seed nhãn `data/seeds/product_categorizer_labels.json` + artifact `data/models/product_categorizer.joblib`.
- Script `scripts/eval_product_categorizer.py`.
- Abstain: `__UNKNOWN__`, low confidence, ambiguous margin, empty input; không trả code ngoài whitelist.

**Ngưỡng mặc định:** `confidence_threshold=0.22`, `margin_threshold=0.04`.

**Không ship** `sentence-transformers` — để #60 quyết định embedding.

### Làm như thế nào

1. Baseline sklearn (đã có) thay vì embedding.
2. Train trên seed + paraphrase + OOV unknown.
3. Eval precision trên test split; pytest happy + abstain.

### Test đã chạy

| Lệnh | Kết quả |
|------|---------|
| `import sklearn` | ok (1.5.2) |
| `pytest -q tests/product_categorizer/` | **8 passed** |
| `scripts/eval_product_categorizer.py` | precision **1.0**, recall_labeled **1.0**, n_test=22, embedding_path=false |

Train: 122 rows, 14 classes (13 VSIC + `__UNKNOWN__`).

### Khoảng trống lúc đóng

- Sample nhỏ; chưa API/FE marketplace.
- Chưa embedding; #60 pin ST riêng.
- Ngưỡng tối ưu trên sample — production cần mở rộng nhãn.

### Task sau cải thiện

#60 thêm hybrid fuzzy+vector cho **shop name → ticker** (khác bài toán categorizer, nhưng cùng phase NLP).

---

## Task #60 — Shop matcher v2 (fuzzy + vector/rerank)

**Một câu:** Cải thiện ghép tên shop marketplace với ticker bằng RapidFuzz + vector cosine + rerank prefix ngắn.

### Mục đích

Fuzzy v1 bỏ sót shop gần đúng (prefix `rd_`, paraphrase). Hybrid tăng recall mà giữ precision gate.

### Bao gồm gì

- `HybridShopMatcher` (default): fuzzy ≥ 0.90 → trả sớm; mid-band fuse với vector; prefix brand boost 0.72; threshold **0.65** (CONTEXT).
- Embedder: ST khi train/eval `--backend sentence_transformers|auto`; runtime/CI mặc định **TF-IDF** (không tải Hub mỗi lần).
- Baseline đổi tên `FuzzyShopMatcher` để so QA.
- Pin `sentence-transformers==3.3.1`; call site mỏng `crawlers/marketplace/shop_finder.py`.
- QA sample + `scripts/eval_shop_matcher.py`.

### Làm như thế nào

1. Không reuse model #59 (TF-IDF classifier ≠ shop embedding).
2. Hybrid + evaluate gate vs fuzzy v1.
3. Pytest regression + gate; không đụng scraper Shopee/TikTok.

### Test đã chạy

| Lệnh | Kết quả |
|------|---------|
| RapidFuzz + SentenceTransformer import | ok |
| `pytest -q tests/shop_matcher/` | **50 passed** |
| `eval_shop_matcher.py --backend tfidf` | gate_pass **true** |

QA (n=22): fuzzy F1 0.833 → hybrid F1 **0.963**; recall 0.71 → **0.93**; precision giữ 1.0.

### Khoảng trống lúc đóng

- Default runtime vẫn TF-IDF; ST mạnh hơn khi train offline.
- Còn FN khó: `led_chieusang_congnghiep` (paraphrase semantic).
- Discovery vẫn gate Task #36 + allowlist — matcher chỉ score.

### Task sau cải thiện

Phase 4.4 chuyển sang narrative UX (#61–#62), không sửa matcher thêm trong chuỗi này.

---

## Task #61 — Benchmark narrative assistant

**Một câu:** Giải thích ROA/ROE/percentile tiếng Việt chỉ từ số `BenchmarkResult` — thiếu thì nói thiếu, không bịa.

### Mục đích

Assist UX: sau khi user compare, có đoạn narrative dễ đọc; rules-first, LLM polish optional.

### Bao gồm gì

- `backend/app/services/benchmark_narrative.py` — rules + honesty gate (mọi số trong text phải cite được từ input).
- `POST /api/benchmark/narrative` (không đụng math `/compare`).
- FE panel trong `Benchmark.jsx` sau kết quả compare.
- LLM optional qua `BENCHMARK_NARRATIVE_LLM_KEY` / `OPENAI_API_KEY`; lỗi/thiếu key → fallback rules.

### Làm như thế nào

1. Map metric → câu tiếng Việt + `omitted` khi thiếu.
2. Gate numeric tokens.
3. Pytest narrative; không bắt buộc FE unit test.

### Test đã chạy

```bash
PYTHONPATH=. pytest -q tests/benchmark/ -k narrative
# 5 passed, 42 deselected
```

### Khoảng trống lúc đóng

- Chưa narrative cho forecast (→ #62).
- Chưa lưu edit user thành training signal (→ #64).
- Không đổi peer math / DocAI extract.

### Task sau cải thiện

#62 copy pattern honesty cho ML Lab forecast; #64 soft-hook confirm sau prefill (không đụng panel narrative).

---

## Task #62 — Forecast narrative assistant

**Một câu:** Tóm tắt horizon dự báo, MAE/RMSE/MAPE và driver feature importance — không bịa nguyên nhân nhân quả.

### Mục đích

Đối xứng #61 cho ML Lab: user hiểu forecast bằng tiếng Việt từ API + artifact importance.

### Bao gồm gì

- `backend/app/services/forecast_narrative.py`.
- `POST /api/ml/narrative`.
- Đọc `xgboost_importance.json` / `lightgbm_importance.json` khi `load_importance=true`.
- FE panel cạnh forecast chart trong `MLLab.jsx`.
- ARIMA/LSTM: bỏ importance và nói rõ là thiếu.

### Làm như thế nào

1. Reuse pattern honesty #61.
2. Wire importance qua `ml_lab_service` (đã có LightGBM từ #58).
3. Optional LLM `FORECAST_NARRATIVE_LLM_KEY` / `OPENAI_API_KEY`.
4. Pytest + `npm run build` FE.

### Test đã chạy

```bash
PYTHONPATH=. pytest -q tests/ml/ -k narrative
# 6 passed, 50 deselected
cd frontend && npm run build  # OK
```

### Khoảng trống lúc đóng

- Importance = gain rank, copy tránh diễn giải nhân quả.
- LightGBM importance chỉ có sau train đã ghi artifact.
- Chưa monitoring drift UI đầy đủ (→ #63) / feedback loop (→ #64).

### Task sau cải thiện

#63 đưa metrics model lên Pipeline; #64 đóng vòng feedback DocAI (khác forecast narrative).

---

## Task #63 — ML monitoring contract

**Một câu:** API + counters theo dõi chất lượng model (MAE/RMSE/MAPE) và drift — chỉ tính drift khi có baseline file.

### Mục đích

Stage 8 pipeline: schema giám sát thống nhất, hiện trên Pipeline Monitor; chưa auto-retrain.

### Bao gồm gì

- Schemas/service/API: `GET /api/ml/monitoring`.
- Mỗi model: `metrics`, `as_of`, `drift_flag`/`drift_score`, `sample_count`, `warning`, `artifact_present`.
- Counters: `models_tracked`, `models_with_metrics`, `models_missing_metrics`, `models_with_drift`, `models_unknown_drift`, `artifacts_on_disk`, `baseline_available`.
- FE strip trên `Pipeline.jsx`.
- **Không** cài great-expectations / Prefect.

**Honesty:** thiếu registry/metrics → null + warning; thiếu `data/models/ml_monitoring_baseline.json` → drift null (không bịa). Có baseline: `drift_score = current_mape - baseline_mape`, flag khi `abs(score) >= 5.0`.

### Làm như thế nào

1. Contract schema SQLAlchemy/API hiện có.
2. So MAPE với baseline nếu file tồn tại.
3. Pytest monitoring; FE gọi `getMlMonitoring()`.

### Test đã chạy

```bash
PYTHONPATH=. pytest -q -k ml_monitoring
# 4 passed
```

### Khoảng trống lúc đóng

- Chưa auto-retrain / ingest feedback (#64).
- Baseline file chưa ship sẵn — ops phải tạo để bật drift.
- GE optional chưa dùng.

### Task sau cải thiện

#64 thêm counter `feedback_signals_count` vào monitoring + lưu JSONL khi user confirm DocAI.

---

## Task #64 — Feedback-to-training loop

**Một câu:** Lưu chỉnh sửa field sau DocAI/Benchmark prefill thành dòng JSONL an toàn (không PDF/secret) — chưa train lại model.

### Mục đích

Đóng phase 4.5: tín hiệu “user sửa gì sau extract” để sau này retrain/eval — không lưu raw document.

**Trạng thái git:** PR [#52](https://github.com/thanhhale288/data-economy/pull/52) **MERGED** vào `main` (2026-07-30). Handoff gốc: `.scratch/handoff-task64.md` (trên commit merge; local có thể cần `git pull` nếu chưa thấy file).

### Bao gồm gì

| Piece | Path |
|-------|------|
| Schema | `backend/app/schemas/feedback_signal.py` |
| Service + JSONL | `backend/app/services/feedback_signal.py` → `data/feedback/training_signals.jsonl` |
| API | `POST /api/benchmark/feedback` |
| FE | Checkbox confirm trên `Benchmark.jsx` → `api.benchmarkFeedback` |
| Monitoring | Counter `feedback_signals_count` (#63) |
| Scheduler | Job `feedback_ingest` đếm signal (không retrain) |
| Tests | `tests/benchmark/test_feedback_signal.py` |

**Field được phép lưu:** stock_code, vsic_code, doanh thu/LN/NV/chi phí/BS… (allowlist trong schema).  
**Không bao giờ lưu:** raw PDF, bytes, content, api_key, filename, token, base64.

### Làm như thế nào

1. Diff before/after field allowlisted → 1 dòng JSONL + uuid/timestamp/ticker/source_type.
2. Soft hook FE khi user tick xác nhận (không đụng narrative #61).
3. Scheduler thin count; **không** cài Prefect.
4. Pytest `-k feedback`.

### Test đã chạy (theo handoff branch)

```bash
PYTHONPATH=. pytest -q -k feedback
# 6 passed
```

### Khoảng trống lúc đóng / còn mở

- **Chưa train lại** model từ signal — chỉ lưu tín hiệu.
- CafeF prefill có thể snapshot nhưng POST signal gắn confirm DocAI; mở rộng source sau.
- Auto-retrain policy / Prefect batch OCR+retrain vẫn optional tương lai.
- Phase 4.5 (#63+#64) đã merge; bước tiếp theo ngoài scope chuỗi này là dùng signal để retrain/eval thật.

---

## 2. Thuật ngữ nhanh (từ CONTEXT / ADR — không mở knowledge.md)

| Thuật ngữ | Nghĩa ngắn trong project |
|-----------|---------------------------|
| **IIP / VA** | Chỉ số sản xuất công nghiệp / giá trị tăng thêm Section C (GSO macro) — đầu vào anomaly & forecast |
| **Isolation Forest** | Model bất thường không giám sát; score âm/dương quanh boundary 0 |
| **VSIC 4-digit** | Mã ngành chế biến-chế tạo chi tiết; categorizer chỉ trả whitelist Section C |
| **RapidFuzz / hybrid matcher** | So khớp chuỗi + vector; ngưỡng match shop 0.65 |
| **ROA / ROE / percentile** | Tỷ suất lợi nhuận / vị trí % so peer cùng VSIC 2 số — narrative #61 chỉ cite từ API |
| **MAE / RMSE / MAPE** | Sai số forecast; monitoring drift dựa MAPE vs baseline |
| **Feature importance** | Độ “đóng góp” feature (gain); narrative không biến thành nguyên nhân nhân quả |
| **Honesty / abstain** | Thiếu data → null + warning; không invent alert, percentile, hay VSIC |
| **Training signal** | Diff field user sửa sau prefill — JSONL an toàn, không document gốc |
| **Drift** | Lệch MAPE so baseline; không có file baseline → drift = null |

---

## 3. Khoảng trống còn mở sau #57–#64

1. **Retrain từ feedback** — #64 chỉ ingest; chưa pipeline học lại DocAI/mapper từ JSONL.
2. **Baseline drift** — cần tạo `ml_monitoring_baseline.json` để #63 báo drift thật.
3. **Sample NLP nhỏ** — categorizer & shop QA seed; production cần thêm nhãn / ST tuning FN còn lại.
4. **Anomaly sâu hơn** — chưa LSTM AE; chưa alert trên Dashboard ngành (chỉ ML Lab).
5. **LLM narrative** — optional; thiếu key thì rules-only (ổn cho demo, chưa polish production).
6. **Prefect / GE** — cố ý chưa cài; chỉ cân nhắc khi batch OCR + retrain phức tạp hơn `schedule`.
7. **Phase 4.5 đã đóng trên `main`** (#63+#64 merged) — còn lại là productize retrain từ signal, không phải ship contract nữa.

---

## 4. Lệnh kiểm chứng nhanh (toàn dải)

```bash
source .venv/bin/activate
PYTHONPATH=. pytest -q tests/ml/ -k 'anomaly or narrative or ml_monitoring or lightgbm'
PYTHONPATH=. pytest -q tests/product_categorizer/
PYTHONPATH=. pytest -q tests/shop_matcher/
PYTHONPATH=. pytest -q tests/benchmark/ -k 'narrative or feedback'
PYTHONPATH=. python3 scripts/eval_product_categorizer.py
PYTHONPATH=. python3 scripts/eval_shop_matcher.py --backend tfidf
```

(Feedback tests cần code #64 trên branch/merge hiện tại.)

---

## Tham chiếu

- Plan Epic 4: `.scratch/epic4-ai-ml-plan.md` (§ Phase 4.2–4.5)
- Handoff: `.scratch/handoff-task57.md` … `handoff-task63.md`; #64 trên branch task
- Domain: `CONTEXT.md`, `AGENTS.md`, `docs/adr/`
