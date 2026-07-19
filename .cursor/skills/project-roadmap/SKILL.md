---
name: project-roadmap
description: Chia dự án "Kinh tế số ngành Chế biến, Chế tạo" (docs/plan.md) thành các task tuần tự và dẫn dắt người dùng thực hiện từng task một. Dùng khi người dùng hỏi "task tiếp theo là gì", "làm gì bây giờ", "tiến độ dự án", "roadmap", hoặc muốn triển khai theo docs/plan.md.
disable-model-invocation: true
---

# Project Roadmap — Kinh tế số ngành Chế biến, Chế tạo

Skill này biến `docs/plan.md` thành một backlog tuần tự và dẫn dắt người dùng làm **từng task một**.

## Nguyên tắc

- **Nguồn sự thật**: `docs/plan.md` (lộ trình 5 giai đoạn, ~18 tuần) + `CONTEXT.md` (thuật ngữ, công thức) + `AGENTS.md` (ranh giới, stack).
- Backlog dưới đây bám theo Mục 6 của plan. Nếu plan thay đổi, đọc lại và cập nhật thứ tự task.
- Làm **tuần tự theo dependency**: chỉ mở task khi task chặn nó đã xong.
- Tôn trọng ranh giới trong `AGENTS.md`: không bịa số OECD/GSO, không đổi công thức Digital VA/VDEI khi chưa cập nhật `CONTEXT.md` + ADR, giữ nguyên 10 DN mẫu (RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BMP).

## Quy trình mỗi lần chạy

### 1. Xác định task hiện tại

- Đối chiếu backlog bên dưới với code thực tế (`backend/`, `crawlers/`, `pipeline/`, `ml/`, `frontend/`, `data/`) để biết task nào đã xong.
- Task hiện tại = task chưa hoàn thành đầu tiên mà mọi task chặn nó đã xong.
- Báo cho người dùng: task đang ở đâu trong 5 giai đoạn, còn task nào phía trước.

### 2. Trình bày task

Với task hiện tại, trình bày:

- **Mục tiêu**: task này làm hệ thống chạy được điều gì (góc nhìn end-to-end).
- **Việc cần làm**: các bước cụ thể, chạm những thư mục/file nào.
- **Acceptance criteria**: checklist nghiệm thu (chạy được, có test/kiểm chứng).
- **Blocked by**: task nào phải xong trước (nếu có).

### 3. Hỏi guide hay implement

Hỏi người dùng **một câu**: muốn skill chỉ **hướng dẫn** (đưa checklist + acceptance criteria để tự làm) hay **implement luôn** task này?

- Nếu **guide**: đưa hướng dẫn chi tiết, không sửa code, kết thúc bằng cách chỉ ra task kế tiếp.
- Nếu **implement**: tạo TODO list, thực hiện task, chạy/kiểm chứng theo acceptance criteria, rồi báo task kế tiếp.

### 4. Sau khi xong một task

- Tóm tắt đã làm gì, đối chiếu acceptance criteria.
- Chỉ ra task tiếp theo trong backlog và hỏi có làm tiếp không.

## Backlog tuần tự (theo docs/plan.md Mục 6)

Đánh số theo thứ tự dependency. Mỗi task là một lát cắt dọc, nghiệm thu độc lập được.

### Giai đoạn 1 — Nền tảng & Macro data (Tuần 1–5)

1. **Scaffold** — Docker Compose (db + redis + backend + frontend), PostgreSQL, FastAPI skeleton, React shell, cấu trúc thư mục theo Mục 7. *Blocked by:* none.
2. **VSIC/ISIC mapping + seed** — bảng ánh xạ ISIC Section C ↔ VSIC 10–33 (`data/mappings/`), seed 10 DN mẫu (`data/seeds/`), DB migrations. *Blocked by:* 1.
3. **GSO crawler** — IIP, chỉ số xuất hàng, chỉ số tồn kho cho Section C (SDMX/PX-Web), fallback rõ ràng khi crawl fail. *Blocked by:* 2.
4. **OECD SDMX ingestion** — MEI Industrial Production, INDIGO, ICT investment; nội suy quý → tháng. *Blocked by:* 2.

### Giai đoạn 2 — Enterprise crawl & Digital detection (Tuần 6–10)

5. **Company crawler** — metadata 10 DN niêm yết (HOSE/HNX), website chính thức, BCTC có cấu trúc. *Blocked by:* 2.
6. **Website digital detector** — phát hiện có website bán hàng / giỏ hàng / checkout (rule-based). *Blocked by:* 5.
7. **Marketplace crawler** — tìm & scrape shop Shopee/TikTok, ước lượng units_sold/giá; rate limiting. *Blocked by:* 5.
8. **Shop-matcher ML** — classifier match shop ↔ DN (precision > 90%), QA thủ công cho 10 DN. *Blocked by:* 7.
9. **Digital metrics** — tính VDEI manufacturing: online_revenue_est, Digital VA, industry_share theo công thức trong `CONTEXT.md`. *Blocked by:* 6, 8, 3.

### Giai đoạn 3 — Clean, Features & ML (Tuần 11–14)

**Lưu bản sạch:** Phase 3 dùng artifact **Parquet** (`data/processed/cleaned_*.parquet`, `cleaning_report.json`, `features.parquet`). **Không** overwrite raw DB. Bảng **staging** Postgres (nếu cần) trì hoãn đến Module 3–4. Chi tiết: `docs/plan.md` §4.1.

10. **Cleaning pipeline** — missing values, outlier (IQR/Z-score), entity resolution hook, VSIC validation; job `data_cleaning` trước `feature_engineering`; ghi parquet + quality report (không overwrite raw). *Blocked by:* 9, 4. *(DONE trên branch Phase 3 — đối chiếu code/tests trước khi mở #11.)*
11. **Feature engineering** — lag (INDIGO/IIP/MEI_IP@EA20 peer), rolling, digital features, cross, financial; align CafeF quý→tháng; không bịa MEI_BCI; đọc từ cleaned parquet khi có. *Blocked by:* 10.
12. **ML models** — train & đánh giá ARIMA/SARIMAX, XGBoost/LightGBM, LSTM; MAE/RMSE/MAPE, walk-forward. Model registry + API endpoints. *Blocked by:* 11.

### Giai đoạn 4 — Web hoàn thiện & Demo (Tuần 15–17)

13. **Dashboard ngành (Module 1)** — IIP, giá trị gia tăng, forecast, heatmap VSIC, OECD vs GSO. *Blocked by:* 12.
14. **Company detail (Module 2)** — profile DN, kênh bán số, ước lượng online; case study Rạng Đông. *Blocked by:* 9.
15. **Pipeline monitor (Module 3)** — trạng thái job crawl + `data_cleaning`, log lỗi, lần crawl cuối, tóm tắt quality report; **tuỳ chọn** thêm staging Postgres cho bản sạch *song song* parquet nếu monitor/API cần SQL. *Blocked by:* 10.
16. **ML Lab (Module 4)** — so sánh 3 model, forecast vs actual, feature importance; mặc định đọc artifact/registry Phase 3; staging chỉ nếu API Lab cần query DB. *Blocked by:* 12.
17. **Integration testing end-to-end** — luồng crawl → clean → ML → API → FE chạy thông. *Blocked by:* 13, 14, 15, 16.

### Giai đoạn 5 — Benchmark & Báo cáo (Tuần 18)

18. **Benchmark module (Module 5)** — form nhập (doanh thu, LN, NV, chi phí) → ROA/ROE/Current/Equity ratio + percentile ngành (kiểu SingStat BITE). *Blocked by:* 17.
19. **Proposal v2** — cập nhật Mục 4 với schema, chỉ tiêu, công thức, kết quả thực tế (`docs/proposal-v2.md`). *Blocked by:* 18.

## Deliverable cuối (kiểm tra khi gần xong)

Đối chiếu Mục 9 của plan: web app 4 module chạy được, DB có macro + micro 10 DN, pipeline tự động, 3 model đã train, case study Rạng Đông, proposal v2, benchmark prototype.
