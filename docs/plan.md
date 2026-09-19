# Kế hoạch — tạm hoãn gửi xin rút; làm nốt bề nổi còn lại

**Cập nhật:** 19/9/2026  
**Mục tiêu:** **tạm hoãn gửi** xin rút cho GVHD. Làm nốt **bề nổi còn lại** trên repo: bộ câu hỏi form, khung nhãn 6 cờ, khớp MST form↔web, `DT × %` khi có số, dàn ý báo cáo. **Không** hoàn thiện nghiên cứu quốc gia. **Không** giả vờ đề tài đã xong.

Agent: làm các mục bề nổi còn mở (mục 4, cột “đang làm”). Không dán nhãn vàng giả, không bịa số chạy mới. Không mở sprint “xong tháng 12”.

---

## 1. Quyết định

Người đang làm là **kỹ sư AI**, không phải người đo lường / kinh tế số. Đề tài (sau mọi lần refactor) vẫn là: khung mẫu, % doanh thu, khảo sát, thống kê. Chi phí chìm cao; **gửi xin rút vẫn là hướng khi bàn giao**, nhưng **chưa gửi hôm nay**.

**Tạm hoãn gửi.** Giữ bản nháp bàn giao (`docs/lab/BAN-GIAO.md`, PR #88). Trong lúc đó làm nốt việc bề nổi còn làm được trên repo. Không xin “làm nốt tháng 12 cho xong nghiên cứu”.

---

## 2. Nói với cô một trang (bản nháp — **chưa gửi**)

> **Không copy gửi hôm nay.** Giữ nguyên khi sau này bàn giao.

> Em đã dựng được hệ thống đọc website doanh nghiệp sản xuất (tìm URL, 6 đặc trưng trên trang, LLM lab) và có số chạy thật trên mẫu nhỏ. Phần còn lại cô muốn — khảo sát 100–200 DN, ước % doanh thu online, nhãn tay đủ lớn, suy rộng / GSO — là **đề tài đo lường**, không phải thế mạnh của em (AI / hệ thống).  
> Em xin **rút khỏi đề tài** và **bàn giao** code, dữ liệu, tài liệu để cô giao nhóm khác (hoặc SV đo lường). Em sẵn sàng gặp 15 phút để chỉ chỗ chạy và việc còn mở.  
> Em không bỏ dở im lặng: có danh sách artifact và việc chưa làm ở dưới.

Giọng: trách nhiệm, không đổ lỗi, không tự hạ “em kém”.

---

## 3. Bề nổi cô cần thấy (đã có trên repo)

Không làm thêm cho “đẹp”. Chỉ **chỉ đúng chỗ** và, nếu cần, một file mục lục.

| Cô từng hỏi | Đã có | Nói thẳng |
|-------------|--------|-----------|
| MST → tìm web | URL-finder, 12/28 hit; search từng chết | Không phải SERP châu Âu 83–88% |
| Có web / catalog / giỏ / thanh toán / MXH / link sàn | Cascade 128 DN, **89 trang tải được**; tỷ lệ tầng luật trên 89 | Máy nói; **chưa** P/R so người (nhãn tay chưa đóng) |
| % DT / GMV / 9000 tỷ | Không có từ HTML | Cần form × DT nếu có; **không** cào sàn; `DT × %` mẫu thật vẫn chặn |
| Không nhãn thì lệch? | Chưa có bảng P/R người | Khung worksheet 89 đang có; **ô nhãn người trống** |
| Form 100–200 | Bộ câu hỏi bản thảo trên repo; **chưa gửi DN** | [`docs/lab/KHAO-SAT-DOANH-NGHIEP.md`](lab/KHAO-SAT-DOANH-NGHIEP.md) |
| Nhật | Pilot 21/300, search chết | Phụ lục kỹ thuật, không phải thân đề tài |
| GSO | Chưa xin | Nhóm sau khi đề xuất đã rõ |
| Demo web | Đã gỡ Digital VA / MAPE không bảo vệ được | Còn nền tảng học kỳ (Epic 1–5) |

**Số mang miệng (có file):**

- Khung MST công khai: **800** (`data/raw/frame_pilot/`)  
- Tìm web VN: **12/28** (`data/processed/url_finder/`)  
- Đọc trang: **89/128 fetch_ok** (`data/processed/extraction_cascade/`)  
- Nhật: **21/300** (`data/processed/jp_calibration/`)  
- LLM: `qwen3:8b` ghim — ADR-0004  

Bảng trên là artifact đã có (không bịa số mới). Việc đang làm tiếp / còn chặn: **mục 4**.

---

## 4. Việc bề nổi còn lại (đang làm vs còn chặn)

Không bỏ mục. Phân **đang làm được trên repo** và **vẫn chặn** (thiếu người / thiếu số khảo sát / thiếu quyền).

| Trạng thái | Việc | Ghi chú |
|------------|------|---------|
| [x] | Soạn bộ câu hỏi | [`docs/lab/KHAO-SAT-DOANH-NGHIEP.md`](lab/KHAO-SAT-DOANH-NGHIEP.md) — bản thảo trên repo; **chưa** gửi DN |
| [x] | Khung nhãn 6 cờ trên 89 site | [`docs/annotation-handbook-v1.md`](annotation-handbook-v1.md) + `data/processed/mini_gold/worksheet_89.csv`; **ô nhãn người vẫn trống** |
| [x] | Khớp form ↔ web theo MST | [`docs/lab/KHOP-FORM-WEB.md`](lab/KHOP-FORM-WEB.md) + `crawlers/survey_join/` — test fixture giả; **chưa** có form thật |
| [x] | Dàn ý báo cáo | [`docs/lab/DAN-Y-BAO-CAO.md`](lab/DAN-Y-BAO-CAO.md) — dàn ý, **không** phải báo cáo 25 trang |
| [x] | Glue form (recode + MST listed + unmatched plan + Serper tùy chọn) | `crawlers/survey_join` recode/plan; URL-finder `SERPER_API_KEY` — không phiếu thật |
| [blocked] | `DT × %` trên mẫu thật | Chưa có phiếu khảo sát / doanh thu DN khai |
| [blocked] | Gửi form 100–200 DN | Cần cô gửi / kênh phát form — không tự spam DN |
| [blocked] | Nhãn tay đủ (tối thiểu ~20, đủ thì 89) → P/R | Người dán; máy không thay |
| [blocked] | Xin GSO | Không xin hộ; chưa có đề xuất khung mẫu quốc gia |
| [blocked] | Báo cáo lab 25 trang đầy đủ | Dàn ý ≠ bản nộp |

**Vẫn cấm (không làm như hướng cũ):**

- GMV sàn, cào listing sản phẩm trên sàn  
- Digital VA / VDEI làm KPI lab  
- Dự báo IIP làm KPI lab  
- Suy tỷ lệ cả nước khi **không** có khung GSO  
- Bịa số chạy mới (giữ 800 / 12/28 / 89/128 / 21/300 / `qwen3:8b`)

Lịch sử đề xuất (v2 Digital VA → v3/v4 OBEC–Nhật): `docs/archive/`. **Không** lấy làm hướng “hoàn thiện lab tháng 12”.

---

## 5. Gửi cô / gặp 15 phút = **tạm hoãn**

- [ ] In / gửi đoạn mục 2 — **tạm hoãn** (19/9/2026)  
- [`docs/lab/BAN-GIAO.md`](lab/BAN-GIAO.md) — **giữ làm bản nháp**; file vẫn đúng khi sau này bàn giao; **đừng gửi cô hôm nay** (PR #88 đã có)  
- [ ] Repo trên GitHub, nhánh `main` + ghi chú branch docs nếu chưa merge — khi **bỏ hoãn**, không hôm nay  
- [ ] 15 phút: mở 1–2 artifact JSON, không demo KPI cũ — **tạm hoãn**

**Không:** dán 89 nhãn, viết 25 trang, gửi form 100–200, xin GSO.

---

## 6. Việc *không* làm

- Sprint hoàn thiện tháng 12 (giả vờ đề tài đã xong nghiên cứu)  
- Giả vờ đề tài đã “xong nghiên cứu” / nghiệm thu  
- Xóa repo / ẩn số đã chạy  
- Xin GSO hộ nhóm sau  
- Xóa `docs/lab/BAN-GIAO.md`

---

## 7. Agent / roadmap

User hỏi “làm gì tiếp” → **mục 4, dòng còn chặn** (gửi form, nhãn tay, DT×% mẫu thật, GSO, báo cáo đủ). Bề nổi làm được trên repo **đã có file**. Không tự gửi form / dán nhãn giả / xin GSO.

**Vẫn cấm:** nhãn vàng giả, bịa số chạy, GMV/Digital VA/IIP-lab/suy cả nước, gửi BAN-GIAO.md cho cô khi còn tạm hoãn, sprint “xong tháng 12”.
