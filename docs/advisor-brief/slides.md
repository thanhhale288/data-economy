# Slide / kịch bản 15 phút — buổi gặp GVHD

Mỗi khối = **một trang in** (hoặc một slide). Thời gian gợi ý khớp `docs/evol-1.md`.  
Số liệu cắt tại merge T05; chỗ trống ghi *chưa có*.

---

## Slide 1 — Mở đầu bằng cái đã làm (≈2′)

**Tiêu đề:** Em chủ động gỡ hướng cũ và tái định vị theo chuẩn đo lường web DN

- Audit hệ thống **20–21/8**: tầng dự báo rò rỉ nhãn + thua naive baseline; Digital VA đứng trên ít dòng listing / hằng số tự đặt.
- **Đã gỡ khỏi demo** các KPI không bảo vệ được trước phản biện; giữ crawler / matcher đóng băng cho pipeline đo website.
- Neo phương pháp: **Eurostat OBEC / Web Intelligence Network**, thống kê thực nghiệm Istat — không còn luận điểm “lần đầu ở VN” làm chỗ dựa chính.
- Tài liệu đưa tay: **proposal-v4** (in sẵn).

*Nói một câu:* “Em không xin lỗi bằng lời — em đưa file audit và bản đề xuất mới.”

---

## Slide 2 — Định vị một dòng (≈2′)

**Tiêu đề:** Thiết bị đo tham gia TMĐT từ web — hiệu chuẩn Nhật, triển khai Việt Nam

> Đo tỷ lệ DN chế tạo tham gia TMĐT từ website; hiệu chuẩn nơi có nhãn lớn (Nhật); triển khai nơi thiếu nhãn (VN); **định lượng độ chính xác mất khi không còn nhãn**.

Ba hệ quả (proposal-v4 §1):

1. Cái mới là *giá của việc thiếu nhãn*, không phải *địa lý mẫu*.  
2. Phần phương pháp **không treo một chữ ký** công văn VN.  
3. Bộ dò URL có thể chấm hàng trăm ca (Nhật) thay vì chỉ 28 ca (VN).

---

## Slide 3 — Kết quả chạy thật (1/2) (≈2.5′)

**Tiêu đề:** Đã có khung + bộ dò URL — toàn bộ từ dữ liệu công khai

| | |
|--|--|
| **Khung pilot (T02)** | **n = 800** DN · VSIC **10** (300), **22** (250), **25** (250) · nguồn masothue · có PROVENANCE |
| **URL-finder (T03)** | Blind **28** DN đã biết website: hit **12/28 = 42.9%** · precision khi quyết định **66.7%** · abstain **35.7%** |
| **So châu Âu** | Báo cáo URL-finding ~**83–88%** — mẫu/điều kiện khác; **không tuyên bố ngang hàng** |
| **Vì sao hit thấp** | Search HTML DuckDuckGo trả 202 → gần như chỉ suy domain; có phân tích ca wrong/related trong repo |

*Nhấn:* tất cả làm **không cần chờ** dữ liệu xin qua công văn.

---

## Slide 4 — Kết quả chạy thật (2/2) (≈2.5′)

**Tiêu đề:** Thác trích chỉ tiêu v0 — bảng thô, chưa suy rộng

Cohort **128** site (28 listed + 100 frame) · tải OK **89 (69.5%)**.

Trên **89 fetch_ok**, tầng luật (tầng 1) ước lượng mô tả:

| Chỉ tiêu (OBEC-style) | Tỷ lệ thô |
|------------------------|-----------|
| Có dấu hiệu danh mục SP | **74.2%** |
| Có dấu hiệu giỏ / đặt hàng | **51.7%** |
| Có link MXH | **52.8%** |
| Có dấu hiệu thanh toán / link sàn | **~6.7%** mỗi loại |

**Chú thích bắt buộc khi nói số:** chưa trọng số khảo sát, chưa khoảng tin cậy quốc gia; link sàn = outbound trên site DN, **không** cào listing Shopee/Lazada.

**Đang làm (T06):** sổ tay gán nhãn + mini gold trên 89 DN → P/R tầng 1 / tầng 2 vs nhãn tay (*chưa có số hôm nay*).

---

## Slide 5 — Điểm mới v4: hiện trường Nhật (≈3′)

**Tiêu đề:** Vì sao thêm Nhật — không phải “cho đẹp hồ sơ”

- Nhật có đăng bạ pháp nhân mở + trường **URL website** trong dữ liệu chính phủ (国税庁 + gBizINFO) → chấm bộ dò trên **hàng trăm** ca có nhãn thay vì 28.
- Mục tiêu phương pháp: đo *chồng kiểm định không nhãn của mình sai bao nhiêu* (RQ thiết bị đo).
- **Ngân sách cứng:** tối đa ~1 tuần công cho pilot T08; nếu phình → cắt còn bảng P/R rồi dừng.
- Dữ liệu tải công khai → **không phát sinh xin phép** cho nhánh này.
- **T08 chưa chạy:** nếu kịp sẽ có P/R n≈300 phân tầng; nếu không, thiết kế vẫn nằm trong proposal + Phụ lục C.

*Câu hỏi thật (không lễ phép):* nhánh so sánh quốc tế **nằm trong đề tài cấp trường**, hay giữ thân bài thuần VN và để Nhật ở hướng phát triển / Phụ lục C?

---

## Slide 6 — Ba đề nghị cụ thể (≈2′)

**Tiêu đề:** Xin quyết định hôm nay — không xin “ủng hộ chung chung”

| # | Đề nghị | Tài liệu sẵn |
|---|---------|--------------|
| **(a)** | Thầy/cô **ký 2 công văn** | `cong-van-a-gso.md`, `cong-van-b-idea.md` — điền tên lab / đầu mối rồi in giấy tiêu đề |
| **(b)** | **Làm rõ thể thức nghiệm thu tháng 12** của lab | Ghi vào checklist cuối buổi |
| **(c)** | **Ý kiến nhánh Nhật** (trong / ngoài đề tài cấp trường) | proposal-v4 mục 9 đã có phương án thuần VN |

Hỏi thêm: lab có **SV** tham gia gán nhãn sau khi handbook T06 xong không? (T10)

---

## Slide 7 — Bộ tối thiểu & việc tuần tới (≈1′)

**Tiêu đề:** Trạng thái Nhóm A trước / sau buổi gặp

| Task | Trạng thái (cắt T05) |
|------|----------------------|
| T01 Ẩn KPI không bảo vệ được | Xong (nền tảng buổi gặp) |
| T02 Khung pilot n=800 | Xong |
| T03 URL-finder 12/28 | Xong (có error analysis) |
| T04 LLM local | Xong (dùng cho tầng 2 T05) |
| T05 Thác trích cohort 128 | Xong (số mô tả) |
| **T07 Gói GVHD** | **Gói này** |
| T06 Mini gold P/R | Đang gán tay (có thể thu nhỏ 20 DN nếu gấp) |
| T08 Pilot Nhật | Chưa — cố nếu kịp |

**Nguyên tắc buổi gặp:** mọi câu khẳng định có số hoặc file; điểm yếu nói trước + bằng chứng vì sao bỏ hướng cũ là đúng.

---

## Checklist ghi quyết định (điền tay sau buổi)

- [ ] Duyệt proposal-v4: có / có chỉnh mục …  
- [ ] Công văn GSO: ký ngày … / chờ sửa chỗ …  
- [ ] Công văn iDEA: ký ngày … / chờ sửa chỗ …  
- [ ] Nghiệm thu T12: sản phẩm bắt buộc là …  
- [ ] Nhánh Nhật: trong đề tài cấp trường / chỉ Phụ lục C / quyết định sau  
- [ ] SV gán nhãn: có nguồn / chưa / không  
- [ ] Việc ưu tiên tuần sau: …
