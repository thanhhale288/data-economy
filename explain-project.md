# Giải thích đề tài — dễ hiểu

**Viết ngày:** 22 tháng 9 năm 2026  
**Nguồn neo:** kế hoạch hiện tại trong `docs/plan.md`, bộ câu hỏi khảo sát, dàn ý báo cáo lab, sổ tay gán nhãn.  
**Không phải:** báo cáo nộp cô, hay kết quả nghiên cứu đã xong.

Tài liệu này trả lời bốn câu: đề tài **ban đầu muốn gì**, **đang hướng tới đâu**, **hỏi nghiên cứu gì**, và **làm bằng cách nào**.

---

## 1. Mục đích ban đầu (bạn đang làm gì?)

Đề tài gắn với doanh nghiệp **chế biến, chế tạo** ở Việt Nam (nhóm ngành sản xuất trong Hệ thống ngành kinh tế Việt Nam).

Cô hướng dẫn muốn thấy được, trên mẫu doanh nghiệp thật:

1. Từ **mã số thuế** tìm được **website** của doanh nghiệp (nếu có).
2. Trên website đó, doanh nghiệp có những dấu hiệu bán hàng số nào: danh mục sản phẩm, giỏ hàng / đặt hàng, thanh toán, mạng xã hội, liên kết tới sàn thương mại điện tử.
3. **Tỷ trọng doanh thu** đi qua kênh số khoảng bao nhiêu phần trăm (không lấy từ mã trang web — trang web không cho số doanh thu).
4. Máy đọc website có **lệch** so với người xem tay hay không.

Tóm một câu: **đo mức tham gia kênh số của doanh nghiệp sản xuất** — trước hết bằng cách nhìn website và hỏi doanh nghiệp — **không** phải dự báo chỉ số sản xuất cả nước, cũng **không** phải bịa “giá trị gia tăng số” từ công thức demo cũ.

### Những hướng đã từng làm rồi bỏ làm trọng tâm

Trong quá trình làm repo, có lúc hệ thống demo theo hướng khác (ví dụ ước “giá trị gia tăng số” của doanh nghiệp, dự báo chỉ số sản xuất công nghiệp, cào sản phẩm trên sàn). Những phần đó **còn trong code nền tảng học kỳ** nhưng **không còn là mục tiêu bảo vệ đề tài lab**. Hướng hiện tại chỉ giữ: đọc website, sáu dấu hiệu trên trang, khảo sát khoảng phần trăm doanh thu, khớp theo mã số thuế.

---

## 2. Định hướng hiện tại (đang đi về đâu?)

Người làm chính trên repo là **kỹ sư trí tuệ nhân tạo / hệ thống**, không phải người chuyên đo lường thống kê kinh tế. Phần đo lường đầy đủ (gửi form hàng trăm doanh nghiệp, dán nhãn tay đủ lớn, xin khung mẫu quốc gia từ Tổng cục Thống kê) cần người, kênh gửi form, và quyền dữ liệu.

Vì vậy kế hoạch hiện tại là:

- **Giữ** những gì đã dựng được: tìm web, đọc trang, sáu dấu hiệu máy đọc được, số chạy trên mẫu nhỏ, bộ câu hỏi và khung nhãn.
- **Làm nốt phần bề mặt trên repo** (tài liệu + mã khớp form với web trên dữ liệu giả) để cô thấy việc thật đã có chỗ.
- **Không** giả vờ nghiên cứu cả nước đã xong.
- **Không** mở nước rút “xong hết trước tháng mười hai”.
- **Không** bịa nhãn người, bịa số chạy mới, hay ước doanh thu sàn từ việc cào listing.

Khi có phiếu khảo sát thật và nhãn tay, mới nhân **doanh thu × khoảng phần trăm** và đo máy so với người. Chưa có hai thứ đó thì phần “ước số thật” vẫn dừng.

---

## 3. Câu hỏi nghiên cứu (đang cố trả lời gì?)

Dưới đây là các câu hỏi **thực chất** của đề tài lab hiện tại — viết bằng lời thường, không mã hóa thành ký hiệu.

### Câu hỏi 1 — Tìm được website không?

Từ danh sách doanh nghiệp (có mã số thuế, tên), máy tìm được địa chỉ website đúng bao nhiêu phần trên mẫu đã thử?

*Đã có số mẫu nhỏ:* trên hai mươi tám doanh nghiệp niêm yết đã biết có web, máy khớp đúng khoảng mười hai. Khung rộng hơn khoảng tám trăm mã số thuế công khai chỉ là khung thử, **không** phải khung Tổng cục Thống kê đại diện cả nước.

### Câu hỏi 2 — Trên website có những dấu hiệu bán số nào?

Với các trang chủ tải được, máy (và sau này người) ghi nhận có hay không:

- danh mục / danh sách sản phẩm;
- giỏ hàng hoặc đặt hàng **trên chính website**;
- phương thức thanh toán hiển thị;
- liên kết mạng xã hội;
- liên kết tới gian hàng trên sàn (Shopee, TikTok Shop, Lazada…);
- (phần máy còn ghi ngôn ngữ trang; form khảo sát không hỏi mục này).

*Đã có số mẫu nhỏ:* đã thử khoảng một trăm hai mươi tám địa chỉ; khoảng tám mươi chín trang tải được. Tỷ lệ dấu hiệu máy đưa ra chỉ tính trên tám mươi chín trang đó. **Chưa** có bảng so với nhãn người vì ô nhãn tay vẫn trống.

### Câu hỏi 3 — Doanh thu online khoảng bao nhiêu?

Doanh nghiệp tự xếp **khoảng** tỷ trọng doanh thu từ kênh số trong năm tài chính gần nhất (không bắt buộc khai số phần trăm chính xác). Nếu doanh nghiệp chịu khai doanh thu năm đó, có thể nhân doanh thu với khoảng phần trăm — **chỉ khi có số khai**, không suy từ mã trang web.

*Trạng thái:* bộ câu hỏi đã soạn trên repo; **chưa gửi** doanh nghiệp. Vì vậy chưa có ước trên mẫu thật.

### Câu hỏi 4 — Máy có lệch so với người không?

Nếu người xem cùng các website và điền nhãn theo sổ tay quy tắc, máy đúng / sai thế nào (độ chính xác và độ bao phủ)?

*Trạng thái:* sổ tay và bảng trống cho tám mươi chín site đã có; người chưa dán đủ nhãn (mục tiêu tối thiểu khoảng hai mươi dòng đã duyệt, đủ thì cả tám mươi chín).

### Những câu **không** còn là câu hỏi trung tâm của lab

- Doanh thu sàn do sàn công bố (không cào listing sản phẩm hàng loạt).
- “Giá trị gia tăng số” theo công thức demo cũ.
- Dự báo chỉ số sản xuất công nghiệp làm chỉ tiêu bảo vệ.
- Suy tỷ lệ cho **cả nước** khi chưa có khung mẫu chính thức từ Tổng cục Thống kê.

---

## 4. Phương pháp (làm tuần tự thế nào?)

Chuỗi làm việc cố ý đơn giản — không invent công thức kinh tế mới:

```text
1. Lấy danh sách doanh nghiệp (mã số thuế + tên) từ nguồn công khai thử nghiệm
        ↓
2. Tìm địa chỉ website (tìm kiếm / quy tắc / tùy chọn khóa tìm kiếm nếu có)
        ↓
3. Tải trang chủ; ghi nhận tải được hay lỗi mạng
        ↓
4. Máy đọc sáu dấu hiệu trên trang
   - tầng luật (mẫu chữ, liên kết, cấu trúc trang)
   - tầng mô hình ngôn ngữ lớn chạy máy local (đã ghim một phiên bản để chạy lại được)
        ↓
5. Người xem lại một phần trang → nhãn chuẩn (theo sổ tay)
   → so máy với người
        ↓
6. Gửi khảo sát ngắn: kênh + khoảng phần trăm doanh thu (+ doanh thu tùy chọn)
        ↓
7. Khớp phiếu khảo sát với dữ liệu website bằng mã số thuế
        ↓
8. Khi có doanh thu và khoảng phần trăm: ước doanh thu × phần trăm
        ↓
9. (Chỉ khi có khung mẫu chính thức) mới nói chuyện suy rộng / đối chiếu thống kê quốc gia
```

### Vai trò từng lớp dữ liệu

| Lớp | Vai trò | Giới hạn |
|-----|---------|----------|
| Website | Quan sát được từ ngoài: có kênh gì trên trang | Không cho doanh thu |
| Khảo sát | Doanh nghiệp tự khai khoảng phần trăm (và có thể doanh thu) | Cần gửi form; dễ từ chối |
| Nhãn người | Chuẩn để kiểm máy | Tốn thời gian người |
| Khung Tổng cục Thống kê | Muốn suy rộng cả nước thì cần | Chưa xin; chưa có trên repo |

### Đã chạy thử trên máy (mẫu nhỏ — nhớ đúng nghĩa)

Các số sau **đã có file**, chỉ được gọi là thử nghiệm mẫu nhỏ:

| Số | Nghĩa thường |
|----|----------------|
| Khoảng 800 | Số mã số thuế duy nhất trong khung thử từ danh sách công khai (một vài mã ngành sản xuất) — không phải cả nước |
| 12 trên 28 | Tìm web đúng trên mẫu doanh nghiệp niêm yết đã biết có website |
| 89 trên 128 | Số trang chủ tải được trên số địa chỉ đã thử đọc |
| 21 trên 300 | Thử tìm web trên mẫu công ty Nhật (phụ lục kỹ thuật, không phải thân đề tài) |
| Một mô hình ngôn ngữ lớn local đã ghim | Để tầng đọc trang chạy lại được cùng phiên bản |

### Việc đã có trên repo và việc vẫn chờ người

**Đã có (bề mặt hệ thống / tài liệu):** bộ câu hỏi khảo sát; sổ tay và bảng nhãn trống; mã khớp form với web trên dữ liệu giả; dàn ý báo cáo; glue mã hóa câu trả lời form.

**Vẫn chờ người / cô:** gửi form khoảng một trăm đến hai trăm doanh nghiệp; dán nhãn tay đủ; doanh thu × phần trăm trên mẫu thật; xin khung Tổng cục Thống kê; viết báo cáo lab đủ dài nếu cô yêu cầu.

---

## 5. Nhớ một hình ảnh

> **Website trả lời:** “doanh nghiệp *có vẻ* bán số thế nào trên trang của họ?”  
> **Khảo sát trả lời:** “họ *khai* khoảng bao nhiêu phần trăm doanh thu đi qua kênh số?”  
> **Nhãn người trả lời:** “máy nhìn trang có giống người không?”  
> **Tổng cục Thống kê (nếu sau này có khung):** “mẫu này có đại diện được ngành không?”

Ba câu đầu là thân đề tài lab hiện tại. Câu cuối **chưa** mở — và kế hoạch hiện tại **không** giả vờ đã mở.

---

## 6. Đọc thêm khi cần chi tiết

| File | Khi nào mở |
|------|------------|
| `docs/plan.md` | Việc đang làm / còn chặn / việc cấm |
| `docs/lab/KHAO-SAT-DOANH-NGHIEP.md` | Nội dung từng câu khảo sát |
| `docs/annotation-handbook-v1.md` | Quy tắc người nhìn website |
| `docs/lab/KHOP-FORM-WEB.md` | Cách khớp phiếu với dữ liệu web |
| `docs/lab/DAN-Y-BAO-CAO.md` | Khung xương báo cáo lab |
| `docs/archive/` | Lịch sử đề xuất cũ — **không** lấy làm hướng hiện tại |

*Hết file giải thích.*
