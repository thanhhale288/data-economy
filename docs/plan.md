# Kế hoạch — làm nốt bề nổi còn lại

**Cập nhật:** 22/9/2026  
**Mục tiêu:** Làm nốt **bề nổi còn lại** trên repo: bộ câu hỏi form, khung nhãn 6 cờ, khớp MST form↔web, `DT × %` khi có số, dàn ý báo cáo. **Không** hoàn thiện nghiên cứu quốc gia. **Không** giả vờ đề tài đã xong. **Không** mở sprint “xong tháng 12”.

Agent: làm các mục bề nổi còn mở (mục 3, cột “đang làm”). Không dán nhãn vàng giả, không bịa số chạy mới.

---

## 1. Quyết định (đổi hướng)

Người đang làm là **kỹ sư AI**, không phải người đo lường / kinh tế số. Đề tài (sau mọi lần refactor) vẫn là: khung mẫu, % doanh thu, khảo sát, thống kê — phần đo lường đầy đủ cần người / kênh khảo sát / quyền GSO.

**Hướng hiện tại:** giữ phần hệ thống đã dựng (đọc web, 6 cờ, số pilot) và **làm nốt việc bề nổi còn làm được trên repo**. Không xin “làm nốt tháng 12 cho xong nghiên cứu”. Không giả vờ nghiên cứu quốc gia đã xong.

---

## 2. Bề nổi cô cần thấy (đã có trên repo)

Không làm thêm cho “đẹp”. Chỉ **chỉ đúng chỗ** và, nếu cần, một file mục lục.

| Cô từng hỏi | Đã có | Nói thẳng |
|-------------|--------|-----------|
| MST → tìm web | URL-finder, 12/28 hit; search từng chết | Không phải SERP châu Âu 83–88% |
| Có web / catalog / giỏ / thanh toán / MXH / link sàn | Cascade 128 DN, **89 trang tải được**; tỷ lệ tầng luật trên 89 | Máy nói; **chưa** P/R so người (nhãn tay chưa đóng) |
| % DT / GMV / 9000 tỷ | Không có từ HTML | Cần form × DT nếu có; **không** cào sàn; `DT × %` mẫu thật vẫn chặn |
| Không nhãn thì lệch? | Chưa có bảng P/R người | Khung worksheet 89 đang có; **ô nhãn người trống** |
| Form 100–200 | Bộ câu hỏi bản thảo trên repo; **chưa gửi DN** | [`docs/lab/KHAO-SAT-DOANH-NGHIEP.md`](lab/KHAO-SAT-DOANH-NGHIEP.md) |
| Nhật | Pilot 21/300, search chết | Phụ lục kỹ thuật, không phải thân đề tài |
| GSO | Chưa xin | Cần đề xuất khung mẫu rõ trước |
| Demo web | Đã gỡ Digital VA / MAPE không bảo vệ được | Còn nền tảng học kỳ (Epic 1–5) |

**Số mang miệng (có file):**

- Khung MST công khai: **800** (`data/raw/frame_pilot/`)  
- Tìm web VN: **12/28** (`data/processed/url_finder/`)  
- Đọc trang: **89/128 fetch_ok** (`data/processed/extraction_cascade/`)  
- Nhật: **21/300** (`data/processed/jp_calibration/`)  
- LLM: `qwen3:8b` ghim — ADR-0004  

Bảng trên là artifact đã có (không bịa số mới). Việc đang làm tiếp / còn chặn: **mục 3**.

---

## 3. Việc bề nổi còn lại (đang làm vs còn chặn)

Không bỏ mục. Phân **đang làm được trên repo** và **vẫn chặn** (thiếu người / thiếu số khảo sát / thiếu quyền).

| Trạng thái | Việc | Ghi chú |
|------------|------|---------|
| [x] | Soạn bộ câu hỏi | [`docs/lab/KHAO-SAT-DOANH-NGHIEP.md`](lab/KHAO-SAT-DOANH-NGHIEP.md) — bản thảo trên repo; **chưa** gửi DN |
| [x] | Khung nhãn 6 cờ trên 89 site | [`docs/annotation-handbook-v1.md`](annotation-handbook-v1.md) + `data/processed/mini_gold/worksheet_89.csv`; **ô nhãn người vẫn trống** |
| [x] | Khớp form ↔ web theo MST | [`docs/lab/KHOP-FORM-WEB.md`](lab/KHOP-FORM-WEB.md) + `crawlers/survey_join/` — test fixture giả; **chưa** có form thật |
| [x] | Dàn ý báo cáo | [`docs/lab/DAN-Y-BAO-CAO.md`](lab/DAN-Y-BAO-CAO.md) — dàn ý, **không** phải báo cáo 25 trang |
| [x] | Glue form (recode + MST listed + unmatched plan + Serper tùy chọn) | `crawlers/survey_join` recode/plan; URL-finder `SERPER_API_KEY` — không phiếu thật |
| [blocked] | `DT × %` trên mẫu thật | Chưa có phiếu khảo sát / doanh thu DN khai |
| [blocked] | Gửi form 100–200 DN | Cần kênh phát form — không tự spam DN |
| [blocked] | Nhãn tay đủ (tối thiểu ~20, đủ thì 89) → P/R | Người dán; máy không thay |
| [blocked] | Xin GSO | Chưa có đề xuất khung mẫu quốc gia |
| [blocked] | Báo cáo lab 25 trang đầy đủ | Dàn ý ≠ bản nộp |

**Vẫn cấm (không làm như hướng cũ):**

- GMV sàn, cào listing sản phẩm trên sàn  
- Digital VA / VDEI làm KPI lab  
- Dự báo IIP làm KPI lab  
- Suy tỷ lệ cả nước khi **không** có khung GSO  
- Bịa số chạy mới (giữ 800 / 12/28 / 89/128 / 21/300 / `qwen3:8b`)

Lịch sử đề xuất (v2 Digital VA → v3/v4 OBEC–Nhật): `docs/archive/`. **Không** lấy làm hướng “hoàn thiện lab tháng 12”.

---

## 4. Việc *không* làm

- Sprint hoàn thiện tháng 12 (giả vờ đề tài đã xong nghiên cứu)  
- Giả vờ đề tài đã “xong nghiên cứu” / nghiệm thu  
- Xóa repo / ẩn số đã chạy  
- Xin GSO hộ khi chưa có đề xuất khung  

---

## 5. Agent / roadmap

User hỏi “làm gì tiếp” → **mục 3, dòng còn chặn** (gửi form, nhãn tay, DT×% mẫu thật, GSO, báo cáo đủ). Bề nổi làm được trên repo **đã có file**. Không tự gửi form / dán nhãn giả / xin GSO.

**Vẫn cấm:** nhãn vàng giả, bịa số chạy, GMV/Digital VA/IIP-lab/suy cả nước, sprint “xong tháng 12”.
