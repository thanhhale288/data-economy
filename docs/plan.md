# Kế hoạch — gói bề nổi để xin rút và bàn giao

**Cập nhật:** 14/9/2026  
**Mục tiêu:** không hoàn thiện đề tài. Làm **vừa đủ bề mặt** để GVHD thấy đã có việc thật, hiểu vì sao không hợp, và **nhận lại đề tài cho nhóm khác**.

Agent: **không** mở sprint 7 ngày, không dán 89 nhãn, không viết báo cáo lab đầy đủ trừ khi user đổi ý.

---

## 1. Quyết định

Người đang làm là **kỹ sư AI**, không phải người đo lường / kinh tế số. Đề tài (sau mọi lần refactor) vẫn là: khung mẫu, % doanh thu, khảo sát, thống kê. Chi phí chìm cao nhưng **tiếp tục sẽ đốt quan hệ và chất lượng**.

**Xin rút.** Bàn giao repo + số đã chạy + việc còn lại. Không xin “làm nốt tháng 12”.

---

## 2. Nói với cô một trang (copy gửi)

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
| % DT / GMV / 9000 tỷ | Không có từ HTML | Cần form cô gửi × DT nếu có; **không** cào sàn |
| Không nhãn thì lệch? | Chưa có bảng P/R người | Việc nhóm sau: dán ~20–89 site |
| Form 100–200 | Chưa gửi | Nhóm sau soạn + cô gửi |
| Nhật | Pilot 21/300, search chết | Phụ lục kỹ thuật, không phải thân đề tài |
| GSO | Chưa xin | Nhóm sau khi đề xuất đã rõ |
| Demo web | Đã gỡ Digital VA / MAPE không bảo vệ được | Còn nền tảng học kỳ (Epic 1–5) |

**Số mang miệng (có file):**

- Khung MST công khai: **800** (`data/raw/frame_pilot/`)  
- Tìm web VN: **12/28** (`data/processed/url_finder/`)  
- Đọc trang: **89/128 fetch_ok** (`data/processed/extraction_cascade/`)  
- Nhật: **21/300** (`data/processed/jp_calibration/`)  
- LLM: `qwen3:8b` ghim — ADR-0004  

---

## 4. Gói bàn giao (việc còn lại — bề nổi)

Một buổi hoặc một thư kèm repo:

1. **`docs/plan.md` (file này)** — quyết định rút + map artifact.  
2. **`README.md` / `AGENTS.md`** — cách chạy local.  
3. **Việc nhóm sau** (đúng ý cô, em không làm):  
   - Google Form: MST, kênh, khoảng % DT → cô gửi 100–200 DN chế tạo  
   - Dán nhãn tay 6 cờ (tối thiểu 20, đủ thì 89) → P/R  
   - Khớp form ↔ web nếu có MST  
   - Ước `DT × %` chỉ khi có doanh thu  
   - Báo cáo lab; GSO / Nhật sâu nếu nhóm muốn  
4. **Không làm / không khả thi như cũ:** GMV sàn, cào listing, Digital VA, dự báo IIP, suy tỷ lệ cả nước không có khung GSO.

Lịch sử đề xuất (v2 Digital VA → v3/v4 OBEC–Nhật): `docs/archive/`. **Không** lấy làm hướng nhóm mới trừ khi cô muốn.

---

## 5. Việc *bạn* làm trước khi gặp cô (tối đa nửa ngày)

Không vibe code tuần. Chỉ đóng gói:

- [ ] In / gửi đoạn mục 2  
- [ ] (Tuỳ) `docs/lab/BAN-GIAO.md` — copy bảng mục 3–4 ra file riêng nếu cô thích PDF  
- [ ] Repo trên GitHub, nhánh `main` + ghi chú branch docs này nếu chưa merge  
- [ ] 15 phút: mở 1–2 artifact JSON, không demo KPI cũ  

**Không:** dán 20 nhãn, viết 25 trang, soạn form đầy đủ trừ khi cô bảo “để em soạn form rồi rút”.

---

## 6. Việc *không* làm

- Sprint hoàn thiện tháng 12  
- Giả vờ đề tài đã “xong nghiên cứu”  
- Xóa repo / ẩn số đã chạy  
- Xin GSO hộ nhóm sau  

---

## 7. Agent / roadmap

Hết backlog xây mới. User hỏi “làm gì tiếp” → chỉ mục 5 (gói gửi cô) hoặc im. Không implement cascade/form/gold trừ khi user **nói rõ đổi ý, ở lại đề tài**.
