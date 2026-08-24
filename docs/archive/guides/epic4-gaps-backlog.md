# Epic 4 — Những gì chưa làm được (backlog để xem xét & lên plan)

Tổng hợp từ toàn bộ Task #52–#64 (Phase 4.1 DocAI → 4.5 Monitoring/Feedback) + kiểm tra thực tế trên workspace ngày 2026-07-31.
Tất cả 13 task đã ship và merge — danh sách dưới đây là **khoảng trống còn lại**, không phải task fail.

**Cách đọc:** mỗi mục có Hiện trạng → Ảnh hưởng → Việc cần làm → Ước lượng cỡ (S/M/L). Bảng ưu tiên đề xuất ở cuối.

---

## 1. DocAI Benchmark (#52–#56)

### 1.1 PDF tiếng Anh chưa parse được field
- **Hiện trạng:** `_LABEL_ALIASES` trong `backend/app/services/bctc_extract.py` toàn nhãn tiếng Việt (đã bỏ dấu). PDF tiếng Anh đọc text được nhưng map 0 field → tất cả `null` + `missing_field:*`. Detect đơn vị ("nghìn/triệu VND") và PaddleOCR (`lang="vi"`) cũng chỉ tiếng Việt.
- **Ảnh hưởng:** BCTC bản tiếng Anh (nhiều DN niêm yết công bố song ngữ) không dùng được đường upload.
- **Việc cần làm:** thêm alias tiếng Anh ("net revenue", "profit before tax", "total assets", "owner's equity", "employees"…) + regex đơn vị ("in millions of VND/USD"); cân nhắc OCR `lang="en"` hoặc song ngữ; thêm fixture + golden case tiếng Anh.
- **Cỡ:** S–M (cùng pipeline, chỉ mở rộng rules + test).

### 1.2 Golden set eval quá nhỏ
- **Hiện trạng:** 3 case synthetic / 15 slots (`tests/benchmark/golden/extract_golden_cases.json`). Accuracy 1.0 là trên sample tự tạo.
- **Ảnh hưởng:** chưa nói được gì về accuracy trên BCTC HOSE thật (layout phức tạp, scan mờ).
- **Việc cần làm:** mở rộng golden set với BCTC thật (giữ ngoài git nếu có PII — đường dẫn local + fixture đã khử nhạy cảm); đo per-field accuracy/coverage lại.
- **Cỡ:** M (chủ yếu công thu thập + gán nhãn).

### 1.3 Manual UI click-through chưa chạy
- **Hiện trạng:** flow upload → prefill → highlight confidence thấp → confirm → compare mới có test backend + `vite build`; chưa có phiên click thử tay / e2e.
- **Việc cần làm:** một phiên smoke UI (hoặc Playwright e2e) với fixture PDF text + scan.
- **Cỡ:** S.

### 1.4 OCR model chưa đóng gói cho deploy
- **Hiện trạng:** PaddleOCR tải model về `~/.paddlex` lần chạy đầu; `requirements-ocr.txt` là optional extra.
- **Ảnh hưởng:** lần OCR đầu tiên trên máy mới chậm / cần mạng; Docker image chưa bake model.
- **Việc cần làm:** quyết định pre-download trong Dockerfile hoặc chấp nhận lazy-load + ghi rõ ops note.
- **Cỡ:** S.

### 1.5 PDF scan không extract được khi thiếu OCR extra (case thật: BCTC DQC)
- **Hiện trạng (xác nhận 2026-07-31):** `BCTC DQC.pdf` 19 trang toàn scan (0 ký tự text) → router chuyển `pdf_ocr` đúng, nhưng môi trường chưa cài PaddleOCR → warning `ocr_unavailable`, tất cả field null. Người dùng chỉ thấy "không fill được gì".
- **Ảnh hưởng:** mọi BCTC bản scan (rất phổ biến với báo cáo kiểm toán HOSE) đều không dùng được upload trên máy chưa cài OCR extra.
- **Việc cần làm (chọn 1 hoặc kết hợp):**
  1. Cài OCR extra theo `requirements-ocr.txt` (không sửa code);
  2. Thêm tầng **vision-LLM extract** (vd. Gemini multimodal): rasterize bằng pypdfium2 (đã có) → LLM trả JSON field theo whitelist + confidence, giữ honesty gate + human confirm — giải luôn gap 1.1 tiếng Anh; lưu ý PII khi gửi tài liệu ra API ngoài (plan §7);
  3. FE hiển thị rõ thông báo "OCR chưa khả dụng trên server" thay vì form trống im lặng.
- **Ghi chú:** với DN niêm yết có sẵn trong seed (như DQC) — dùng prefill CafeF thay upload là workaround ngay.
- **Cỡ:** (1) S · (2) M · (3) S.

### 1.6 Narrative LLM hardcode endpoint OpenAI
- **Hiện trạng:** `benchmark_narrative.py` / `forecast_narrative.py` gọi thẳng `https://api.openai.com/v1/chat/completions`; key Gemini không dùng được dù Gemini có endpoint OpenAI-compatible.
- **Việc cần làm:** thêm env `*_LLM_BASE_URL` + model name để cắm Gemini/provider khác; test honesty gate với provider mới.
- **Cỡ:** S.

---

## 2. Forecast & anomaly (#57–#58)

### 2.1 LightGBM chưa từng train trên DB hiện tại
- **Hiện trạng (kiểm tra 2026-07-31):** không có `data/models/lightgbm_*`, không có dòng `lightgbm` trong `model_registry`. ARIMA/XGB/LSTM train lần cuối 2026-07-28 (trước khi #58 ship). Code + deps sẵn sàng (`lightgbm 4.5.0`, `train_all_models` đã gọi `train_lightgbm`).
- **Ảnh hưởng:** ML Lab hiện "Chưa có trong registry", không có metrics/importance/forecast cho LightGBM; forecast narrative (#62) thiếu driver LightGBM.
- **Việc cần làm:** chạy train (nút ML Lab / `POST /api/ml/train` / Pipeline job) → xác nhận artifact + card metrics; cân nhắc đưa vào `make bootstrap`.
- **Cỡ:** S (chỉ vận hành).

### 2.2 Anomaly chỉ có Isolation Forest
- **Hiện trạng:** plan nêu Isolation Forest **hoặc** LSTM AE; v1 ship Isolation Forest.
- **Việc cần làm (nếu muốn):** LSTM autoencoder làm tầng so sánh; chỉ đáng làm khi chuỗi dài hơn.
- **Cỡ:** M–L, ưu tiên thấp.

### 2.3 Anomaly chưa lên Dashboard ngành
- **Hiện trạng:** timeline chỉ ở ML Lab; Dashboard không có badge/alert khi kỳ mới nhất là anomaly.
- **Việc cần làm:** chip cảnh báo nhỏ trên Dashboard đọc `GET /api/ml/anomaly` (honesty: thiếu series thì ẩn).
- **Cỡ:** S.

---

## 3. Marketplace NLP (#59–#60)

### 3.1 Sample nhãn quá nhỏ để tin production
- **Hiện trạng:** categorizer 122 dòng train / 22 test; shop matcher QA n=22. Precision 1.0 / F1 0.963 là trên seed.
- **Việc cần làm:** mở rộng labeled sample từ crawl marketplace thật; re-tune `confidence_threshold=0.22` / `margin_threshold=0.04` trên sample mới.
- **Cỡ:** M (đa phần là công gán nhãn).

### 3.2 Categorizer chưa gắn vào API/FE marketplace
- **Hiện trạng:** model offline + script eval (`scripts/eval_product_categorizer.py`); chưa endpoint / chưa hiển thị VSIC dự đoán trên trang marketplace.
- **Việc cần làm:** endpoint infer + cột "VSIC dự đoán (confidence)" trên FE, giữ abstain → hiển thị trống.
- **Cỡ:** M.

### 3.3 Shop matcher: đường sentence-transformers chưa dùng lúc runtime
- **Hiện trạng:** runtime/CI mặc định TF-IDF; MiniLM chỉ khi train/eval `--backend sentence_transformers`. Còn 1 FN khó (`led_chieusang_congnghiep`).
- **Việc cần làm:** thử ST cho mid-band offline, đo lại QA gate; quyết định có bật ST runtime không (trade-off tải model).
- **Cỡ:** S–M.

---

## 4. Narrative (#61–#62)

### 4.1 LLM polish chưa bật / chưa đánh giá
- **Hiện trạng:** không có `BENCHMARK_NARRATIVE_LLM_KEY` / `FORECAST_NARRATIVE_LLM_KEY` / `OPENAI_API_KEY` → chạy rules-only (đúng thiết kế fallback).
- **Việc cần làm:** nếu muốn văn mượt hơn: cấp key qua env, chạy thử vài case, xác nhận honesty gate chặn số bịa; ghi chi phí/latency.
- **Cỡ:** S (config + thử nghiệm).

### 4.2 ARIMA/LSTM narrative không có driver
- **Hiện trạng:** đúng thiết kế (không có feature importance) — narrative nói rõ "thiếu importance".
- **Việc cần làm:** chấp nhận, hoặc thêm giải thích thay thế (hệ số ARIMA / attention proxy) — nghiên cứu, ưu tiên thấp.
- **Cỡ:** L, optional.

---

## 5. Monitoring & feedback (#63–#64) — khoảng trống lớn nhất

### 5.1 Chưa có retrain từ feedback (loop chưa khép)
- **Hiện trạng:** #64 chỉ **lưu + đếm** signal (`data/feedback/training_signals.jsonl`, counter `feedback_signals_count`, scheduler job count-only). Chưa có gì tiêu thụ signal để cải thiện extractor/mapper.
- **Việc cần làm:** pipeline đọc JSONL → cập nhật alias/rules hoặc train mapper; định nghĩa ngưỡng (vd. ≥N signal cùng field) trước khi đổi behavior; cân nhắc Prefect nếu batch phức tạp.
- **Cỡ:** L — ứng viên epic/phase mới.

### 5.2 Drift monitoring chưa hoạt động thật
- **Hiện trạng:** thiếu `data/models/ml_monitoring_baseline.json` → `drift_flag`/`drift_score` luôn null (đúng honesty, nhưng nghĩa là chưa giám sát được drift).
- **Việc cần làm:** tạo baseline từ lần train tốt (MAPE per model); quyết định quy trình cập nhật baseline sau mỗi retrain đạt chuẩn.
- **Cỡ:** S.

### 5.3 Feedback chỉ bắt đường DocAI confirm
- **Hiện trạng:** POST signal chỉ khi user tick confirm sau DocAI extract; đường CafeF prefill / nhập tay chưa gửi.
- **Việc cần làm:** mở rộng nguồn signal (`source_type` đã có sẵn trong schema) nếu muốn dữ liệu dày hơn.
- **Cỡ:** S.

---

## 6. Ý tưởng P2/P3 trong plan chưa đụng tới (ghi nhận, chưa cam kết)

- Peer similarity bằng embedding (ngoài VSIC 2-digit)
- Website digital-signal classifier (brochure vs commerce-ready)
- BCTC consistency check (extract vs lịch sử cùng ticker; flag lệch)
- RAG trên docs GSO/OECD
- GRU / multimodal; auto-retrain policy đầy đủ

---

## 7. Ngoài Epic 4 nhưng chặn chất lượng AI

- **`VA_C` vẫn là `GSO_FALLBACK`, chỉ 2023-01 → 2024-12 (24 điểm)** — anomaly/forecast trên VA bị giới hạn bởi chuỗi ngắn; cần crawl SDMX thật dài hơn nếu muốn kết quả có ý nghĩa.
- Epic 3 paused (#19b, #41, #48, #49) vẫn đóng băng — chỉ mở lại khi user yêu cầu.

---

## 8. Đề xuất ưu tiên (để lên plan)

| # | Việc | Cỡ | Lý do ưu tiên |
|---|------|----|----------------|
| 0 | 1.5 Mở khóa PDF scan (OCR extra và/hoặc vision-LLM Gemini) | S–M | Đang chặn use case thật (BCTC DQC); nếu chọn vision-LLM thì giải luôn 1.1 |
| 1 | 2.1 Train LightGBM (vận hành) | S | Mở khóa ngay card ML Lab + driver narrative, không cần code |
| 2 | 5.2 Tạo drift baseline | S | Bật giám sát thật cho #63 với chi phí nhỏ nhất |
| 3 | 1.1 Alias tiếng Anh cho extract | S–M | Mở rộng phạm vi BCTC dùng được; thay đổi khu trú |
| 4 | 1.3 Smoke UI upload flow | S | Đóng nốt verify #55 còn thiếu |
| 5 | 2.3 Anomaly badge trên Dashboard | S | Giá trị demo cao, code nhỏ |
| 6 | 1.2 Golden set BCTC thật | M | Điều kiện để tin accuracy production |
| 7 | 3.1 + 3.2 Mở rộng nhãn NLP + wire API/FE | M | Đưa categorizer ra khỏi trạng thái offline |
| 8 | 5.1 Retrain từ feedback | L | Khép loop — nên là phase/epic riêng, cần thiết kế trước |

Mục 4.1 (LLM key) và 3.3 (ST runtime) làm khi tiện — phụ thuộc quyết định chi phí. Mục 6 giữ ở backlog ý tưởng.

---

## Tham chiếu

- Tour chi tiết #57–#64: `docs/guides/tasks-57-64-catchup.md`
- Plan gốc Epic 4: `.scratch/epic4-ai-ml-plan.md`
- Handoffs: `.scratch/handoff-task5[3-9].md`, `handoff-task6[0-3].md`; #64 trong commit merge PR #52
- Extract service: `backend/app/services/bctc_extract.py` (+ `_ocr.py`, `_eval.py`)
