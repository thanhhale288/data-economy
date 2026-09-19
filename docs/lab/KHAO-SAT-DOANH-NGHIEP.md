# Khảo sát doanh nghiệp — kênh số và khoảng % doanh thu trực tuyến

**Phiên bản:** 1.0 (19/9/2026)  
**Dùng để:** dán vào Google Form hoặc in giấy.  
**Không phải:** form đã gửi đi, bộ câu trả lời, hay ước GMV sàn / Digital VA.  
**Cột CSV (khóa):** join với dữ liệu website trong repo **phải** dùng đúng `id` cột ở mục 5. Đổi tên cột là gãy khớp.

Đây là việc cô từng hỏi: **MST, kênh, khoảng % doanh thu** — không lấy hướng đề xuất cũ (Digital VA, cào sàn, suy cả nước).

Thời gian điền dự kiến: **5–8 phút**.

---

## 1. Mục đích

Khảo sát đo **hai thứ**, trên **doanh nghiệp chế biến, chế tạo** (VSIC nhóm C — hệ thống ngành kinh tế Việt Nam, phần chế tạo):

1. **Kênh** — DN có website không; trên website (nếu có) có danh mục sản phẩm, giỏ/đặt hàng, thanh toán, liên kết mạng xã hội, liên kết/gian hàng sàn không.
2. **Khoảng % doanh thu trực tuyến** — DN tự xếp tỷ trọng doanh thu từ kênh số vào **một** khoảng cho sẵn (không hỏi số % chính xác).

**Có hỏi (tùy chọn):** doanh thu năm tài chính gần nhất (đồng Việt Nam), để sau này nhân `doanh thu × khoảng %` **chỉ khi DN khai**.

**Không hỏi / không ước trong form này:**

- GMV sàn (tổng giá trị hàng bán trên Shopee / TikTok Shop / Lazada do sàn công bố — không phải số DN khai).
- Digital VA (chỉ số “giá trị gia tăng số” trên demo cũ của repo — **không** dùng).
- Số liệu GSO / OECD, suy tỷ lệ cả nước, cào listing sản phẩm trên sàn.

Sáu cờ website khớp schema máy (`crawlers/extraction_cascade/schema.py` và sổ tay gán nhãn): `has_website`, `has_product_catalog`, `has_order_cart`, thanh toán (`payment_methods`), `has_social_links`, `has_marketplace_links`. Ngôn ngữ website (`website_language`) **không** đưa vào form — không có cột CSV.

---

## 2. Đối tượng và thời gian tham chiếu

| Mục | Quy định |
|-----|----------|
| Đối tượng | Doanh nghiệp **chế biến, chế tạo** (VSIC nhóm C). GVHD có thể gửi khoảng 100–200 DN — **chưa gửi** (xem mục 7). |
| Người điền | Người biết kênh bán và doanh thu: giám đốc, kế toán, phụ trách bán hàng / thương mại điện tử, IT… |
| Thời gian tham chiếu | **Năm tài chính gần nhất đã khóa sổ** (thường là **2025** nếu điền trong năm 2026). Ghi năm vào `revenue_year`. |
| Đơn vị | Một phiếu = **một MST** (kể cả MST chi nhánh có hậu tố, ví dụ `0101164727-001`). |

Nếu DN có nhiều website: khai **website chính** (trang DN dùng giới thiệu / bán hàng). Nếu không có website: vẫn điền kênh MXH, sàn và khoảng % doanh thu.

---

## 3. Bảo mật

- **MST chỉ để khớp** phiếu này với dữ liệu website đã thu thập sẵn trong repo (cùng một DN). Không dùng MST để công bố danh sách người trả lời.
- Email **không bắt buộc**. Chỉ dùng nếu cần làm rõ một ô (ví dụ MST thiếu hậu tố chi nhánh).
- Doanh thu và khoảng %: DN được chọn **Không tiện trả lời** / **Không biết**. Ô doanh thu để trống khi từ chối hoặc không biết — **không** bịa số.
- Không công bố từng phiếu kèm tên người điền. Phân tích chỉ dùng bản đã ẩn danh (MST có thể giữ để join nội bộ).

**Đoạn mô tả Google Form (copy nguyên):**

> Khảo sát ngắn (5–8 phút) về kênh bán hàng số và **khoảng** tỷ trọng doanh thu trực tuyến trong năm tài chính gần nhất.  
> MST dùng để khớp với dữ liệu website nghiên cứu, không công bố.  
> Không hỏi GMV sàn, không ước “giá trị gia tăng số”.  
> Có thể chọn “Không biết” hoặc “Không tiện trả lời” ở câu doanh thu.

**Đồng ý tham gia (không có cột CSV):** một câu đầu form, bắt buộc chọn “Đồng ý” mới tiếp tục. Không xuất vào file join.

---

## 4. Câu hỏi (đánh số)

Cách đọc mỗi câu: **lời hỏi** → kiểu trả lời Google Form → cột CSV (`id` khóa) → cách ghi khi xuất.

Giá trị boolean ghi thường: `true` / `false` / `unknown` (không viết Có/Không vào CSV).

Nếu **không có website** (Câu 5 = Không): Câu 6–9 chọn **Không** / để trống thanh toán; **không** suy rằng DN không có MXH hay gian hàng sàn — Câu 10–12 vẫn hỏi.

Ngôn ngữ website: **không hỏi**.

---

### Câu 1 — Tên doanh nghiệp

**Hỏi:** Tên doanh nghiệp (theo giấy đăng ký / tên giao dịch).

| | |
|--|--|
| Kiểu | Câu trả lời ngắn, bắt buộc |
| Cột | `company_name` |
| Ghi CSV | nguyên văn, không để trống |

---

### Câu 2 — Mã số thuế (MST)

**Hỏi:** Mã số thuế của doanh nghiệp. Nếu là chi nhánh, **giữ hậu tố** sau dấu gạch ngang (ví dụ `0101164727-001`). Không bỏ số 0 ở đầu.

| | |
|--|--|
| Kiểu | Câu trả lời ngắn, bắt buộc |
| Cột | `mst` |
| Ghi CSV | **chữ** (text), không để Excel đổi thành số. Một phiếu = một MST |

Gợi ý xác thực Google Form: độ dài khoảng 10–14 ký tự; cho phép số và dấu `-`.

---

### Câu 3 — Mã ngành VSIC 4 số (nếu biết)

**Hỏi:** Mã ngành kinh tế VSIC **4 chữ số** (ví dụ 2410). VSIC là hệ thống ngành kinh tế Việt Nam. Để trống nếu không nhớ. Chỉ cần 4 số; không bắt buộc mã cấp 5.

| | |
|--|--|
| Kiểu | Câu trả lời ngắn, không bắt buộc |
| Cột | `vsic_4digit` |
| Ghi CSV | 4 chữ số, hoặc trống |

---

### Câu 4 — Mã chứng khoán (nếu có)

**Hỏi:** Nếu doanh nghiệp niêm yết / đăng ký giao dịch, ghi mã cổ phiếu (HOSE / HNX / UPCoM). Để trống nếu không.

| | |
|--|--|
| Kiểu | Câu trả lời ngắn, không bắt buộc |
| Cột | `ticker` |
| Ghi CSV | viết hoa, hoặc trống |

---

### Câu 5 — Có website riêng không?

**Hỏi:** Doanh nghiệp có **website riêng** không? (Trang do DN vận hành, có địa chỉ kiểu `tencongty.vn` / `.com`. Không tính chỉ trang fanpage Facebook, không tính chỉ gian hàng trên sàn.)

| | |
|--|--|
| Kiểu | Trắc nghiệm 1 lựa chọn, bắt buộc |
| Cột | `has_website` |

| Hiện trên form | Ghi CSV |
|----------------|---------|
| Có | `true` |
| Không | `false` |

Không có lựa chọn “Không biết”: người điền thường biết DN có website hay không.

---

### Câu 6 — Địa chỉ website (DN tự khai)

**Hỏi:** Nếu có website, ghi địa chỉ đầy đủ (nên gồm `https://`). Để trống nếu không có website.

| | |
|--|--|
| Kiểu | Câu trả lời ngắn, không bắt buộc |
| Cột | `website_url_self_report` |
| Ghi CSV | URL nguyên văn, hoặc trống |

---

### Câu 7 — Danh mục sản phẩm trên website

**Hỏi:** Trên website của doanh nghiệp, có **danh mục / danh sách sản phẩm để xem** không? (Menu “Sản phẩm”, lưới hàng, thẻ sản phẩm có tên hoặc ảnh — kể cả hàng B2B như thép, ống… nếu là danh mục xem được.)

**Không tính:** chỉ giới thiệu công ty / tin tức; chỉ khẩu hiệu có chữ “sản phẩm”; chỉ file PDF brochure nếu không mở như catalog; chỉ mục “dự án / case study” không phải hàng bán.

Nếu không có website: chọn **Không**.

| | |
|--|--|
| Kiểu | Trắc nghiệm 1 lựa chọn, bắt buộc |
| Cột | `has_product_catalog` |

| Hiện trên form | Ghi CSV |
|----------------|---------|
| Có | `true` |
| Không | `false` |
| Không biết | `unknown` |

---

### Câu 8 — Giỏ hàng / đặt hàng trên chính website

**Hỏi:** Trên **chính website doanh nghiệp**, khách có **giỏ hàng, nút mua / đặt hàng, thanh toán đơn, hoặc form đặt hàng giao hàng** không?

**Không tính:** chỉ nút “Mua tại Shopee / Lazada / TikTok Shop” (rời site); chỉ “liên hệ báo giá”, “đại lý”, “điểm bán”, danh sách showroom. Form “đặt hàng” B2B trên site **tính là Có**; chỉ form “liên hệ” **tính là Không**.

Nếu không có website: chọn **Không**.

| | |
|--|--|
| Kiểu | Trắc nghiệm 1 lựa chọn, bắt buộc |
| Cột | `has_order_cart` |

| Hiện trên form | Ghi CSV |
|----------------|---------|
| Có | `true` |
| Không | `false` |
| Không biết | `unknown` |

---

### Câu 9 — Phương thức thanh toán (trên website)

**Hỏi:** Website doanh nghiệp **hiển thị rõ** phương thức thanh toán nào? (Logo VNPay / MoMo, chữ COD / thanh toán khi nhận hàng, cổng khác.) Chỉ đánh dấu cái **thấy trên site**, không đoán.

- Nút “Mua trên sàn” rồi thanh toán **trên sàn** → **không** ghi vào câu này.
- Không thấy gì / không có website → không chọn dòng nào (CSV để trống). **Không** ghi `none` chỉ vì không thấy.
- `Không nhận thanh toán trên website` (**none**) chỉ khi trang **nói rõ** không hỗ trợ thanh toán trên site.

| | |
|--|--|
| Kiểu | Nhiều lựa chọn (checkbox), không bắt buộc |
| Cột | `payment_methods` |
| Ghi CSV | token cách nhau bằng dấu phẩy, **không** khoảng trắng thừa, thứ tự không quan trọng. Trống nếu không chọn |

| Hiện trên form | Token CSV |
|----------------|-----------|
| VNPay | `vnpay` |
| MoMo | `momo` |
| COD (thanh toán khi nhận hàng) | `cod` |
| Cổng / cách khác | `other` |
| Không nhận thanh toán trên website | `none` |

Ví dụ hợp lệ: `vnpay,cod` · `momo` · `none` · (trống).  
Nếu chọn `none` thì **không** chọn thêm token khác.

*(Không có lựa chọn “Không biết” trên checkbox: không chọn gì = trống, khác `none`.)*

---

### Câu 10 — Mạng xã hội chính thức

**Hỏi:** Doanh nghiệp có **trang / kênh mạng xã hội chính thức** không? (Fanpage Facebook, Zalo OA, YouTube, Instagram, LinkedIn công ty, kênh TikTok, X/Twitter…)

**Không tính:** nút “Share / Chia sẻ” bài viết; icon Facebook không mở được trang DN; video YouTube nhúng mà không có link kênh.

Có website hay không đều trả lời câu này (kênh của DN, không chỉ “có icon trên web”). Máy đọc web chỉ thấy **link trên website** — lệch với câu này là bình thường.

| | |
|--|--|
| Kiểu | Trắc nghiệm 1 lựa chọn, bắt buộc |
| Cột | `has_social_links` |

| Hiện trên form | Ghi CSV |
|----------------|---------|
| Có | `true` |
| Không | `false` |
| Không biết | `unknown` |

---

### Câu 11 — Gian hàng trên sàn

**Hỏi:** Doanh nghiệp có **gian hàng trên sàn thương mại điện tử** không? (Shopee, TikTok **Shop**, Lazada, hoặc sàn khác.)

**Không tính:** chỉ kênh TikTok video (`tiktok.com/@…`) nếu **không** phải shop bán hàng; chỉ nhắc tên sàn trong tin PR.

Đây là câu **kênh** (DN có shop hay không). Máy đọc web chỉ thấy **link ra sàn trên website DN** — DN có shop nhưng không gắn link trên web vẫn ghi **Có** ở đây.

| | |
|--|--|
| Kiểu | Trắc nghiệm 1 lựa chọn, bắt buộc |
| Cột | `has_marketplace_links` |

| Hiện trên form | Ghi CSV |
|----------------|---------|
| Có | `true` |
| Không | `false` |
| Không biết | `unknown` |

---

### Câu 12 — Tên sàn (nếu có)

**Hỏi:** Nếu có gian hàng, chọn sàn. Có thể chọn nhiều. Để trống nếu không có hoặc không biết tên.

| | |
|--|--|
| Kiểu | Nhiều lựa chọn (checkbox), không bắt buộc |
| Cột | `marketplace_names` |
| Ghi CSV | tên hiển thị, cách nhau bằng dấu phẩy |

| Hiện trên form | Ghi CSV |
|----------------|---------|
| Shopee | `Shopee` |
| TikTok Shop | `TikTok Shop` |
| Lazada | `Lazada` |
| Khác | `khác` |

Nếu “Khác”, có thể ghi tên sàn ở Câu 18 (`notes`).

---

### Câu 13 — Khoảng tỷ trọng doanh thu trực tuyến

**Hỏi:** Trong **năm tài chính gần nhất đã khóa sổ**, khoảng bao nhiêu **phần trăm doanh thu** của doanh nghiệp đến từ kênh trực tuyến?

**Doanh thu trực tuyến** ở đây = tiền DN thu từ bán qua website (kể cả đặt hàng trên site) + gian hàng sàn + kênh số khác mà DN coi là bán online (ví dụ chốt đơn qua mạng xã hội nếu DN hạch toán như vậy).

**Không** điền GMV do sàn công bố. **Không** cần số % exact — chọn **đúng một** khoảng.

| | |
|--|--|
| Kiểu | Trắc nghiệm 1 lựa chọn, bắt buộc |
| Cột | `online_revenue_share_bin` |

| Hiện trên form (đúng chữ này) | Mã lưu CSV |
|------------------------------|------------|
| 0% | `zero` |
| Trên 0% đến dưới 5% | `lt5` |
| 5% đến dưới 10% | `5to10` |
| 10% đến dưới 25% | `10to25` |
| 25% đến dưới 50% | `25to50` |
| 50% trở lên | `gt50` |
| Không biết | `unknown` |
| Không tiện trả lời | `refuse` |

CSV **chỉ** nhận đúng một mã trong cột phải. Không ghi chữ tiếng Việt vào cột này.

---

### Câu 14 — Năm tài chính vừa khai

**Hỏi:** Năm tài chính dùng cho Câu 13 (và Câu 15, nếu có) là năm nào? Ví dụ `2025`.

| | |
|--|--|
| Kiểu | Câu trả lời ngắn, không bắt buộc |
| Cột | `revenue_year` |
| Ghi CSV | 4 chữ số (ví dụ `2025`), hoặc trống |

Nên điền dù DN chọn “Không tiện trả lời” ở Câu 13/15 — để biết mốc thời gian của khoảng %.

---

### Câu 15 — Doanh thu năm đó (VND)

**Hỏi:** Tổng doanh thu năm tài chính ở Câu 14, đơn vị **đồng (VND)**, số nguyên. Ví dụ một tỷ rưỡi đồng ghi `1500000000` (không dấu chấm, phẩy, không ghi “tỷ”).

Để trống nếu không biết hoặc không tiện trả lời. **Không** bắt buộc. **Không** suy doanh thu từ website.

| | |
|--|--|
| Kiểu | Câu trả lời ngắn, không bắt buộc |
| Cột | `revenue_vnd` |
| Ghi CSV | số nguyên VND, hoặc **trống** nếu từ chối / không biết |

Không ghi chữ “không tiện trả lời” vào cột số — để trống.

---

### Câu 16 — Vai trò người trả lời

**Hỏi:** Bạn đang trả lời với vai trò nào tại doanh nghiệp?

| | |
|--|--|
| Kiểu | Trắc nghiệm 1 lựa chọn + “Khác” (hoặc câu ngắn), không bắt buộc |
| Cột | `respondent_role` |

Gợi ý lựa chọn: Giám đốc / chủ DN · Kế toán / tài chính · Bán hàng / marketing / thương mại điện tử · IT / phụ trách website · Khác.

---

### Câu 17 — Email liên hệ (không bắt buộc)

**Hỏi:** Email để nghiên cứu hỏi lại nếu MST hoặc website chưa khớp. Để trống nếu không muốn để lại.

| | |
|--|--|
| Kiểu | Câu trả lời ngắn (email), không bắt buộc |
| Cột | `respondent_email` |
| Ghi CSV | email, hoặc trống |

---

### Câu 18 — Ghi chú

**Hỏi:** Ghi chú thêm (nhiều website, bán qua đại lý, sàn “Khác”, chi nhánh khác MST…). Để trống nếu không có.

| | |
|--|--|
| Kiểu | Đoạn văn, không bắt buộc |
| Cột | `notes` |
| Ghi CSV | nguyên văn, hoặc trống |

---

**Tổng: 18 câu có cột CSV** (Câu 1–18). Câu đồng ý tham gia ở mục 3 không đếm.

---

## 5. Google Form → cột CSV

Xuất Google Form sẽ ra tiêu đề tiếng Việt. **Đổi tên cột** sang đúng `id` dưới đây trước khi đưa vào repo. Thứ tự cột khuyến nghị = thứ tự bảng.

| Câu | Tiêu đề gợi ý trên Google Form | Kiểu Form | Cột CSV | Bắt buộc | Giá trị sau recode |
|-----|--------------------------------|-----------|---------|----------|--------------------|
| 1 | Tên doanh nghiệp | Short answer | `company_name` | có | text |
| 2 | Mã số thuế (giữ hậu tố chi nhánh nếu có) | Short answer | `mst` | có | text |
| 3 | Mã VSIC 4 số (nếu biết) | Short answer | `vsic_4digit` | không | 4 số hoặc trống |
| 4 | Mã chứng khoán (nếu có) | Short answer | `ticker` | không | text hoặc trống |
| 5 | Doanh nghiệp có website riêng không? | Multiple choice | `has_website` | có | `true` / `false` |
| 6 | Địa chỉ website | Short answer | `website_url_self_report` | không | URL hoặc trống |
| 7 | Website có danh mục sản phẩm để xem không? | Multiple choice | `has_product_catalog` | có | `true` / `false` / `unknown` |
| 8 | Có giỏ / đặt hàng trên chính website không? (không tính chỉ nút ra sàn) | Multiple choice | `has_order_cart` | có | `true` / `false` / `unknown` |
| 9 | Phương thức thanh toán hiển thị trên website | Checkboxes | `payment_methods` | không | `vnpay`,`momo`,`cod`,`other`,`none` hoặc trống |
| 10 | Doanh nghiệp có kênh mạng xã hội chính thức không? | Multiple choice | `has_social_links` | có | `true` / `false` / `unknown` |
| 11 | Doanh nghiệp có gian hàng trên sàn không? | Multiple choice | `has_marketplace_links` | có | `true` / `false` / `unknown` |
| 12 | Tên sàn (nếu có) | Checkboxes | `marketplace_names` | không | `Shopee`, `TikTok Shop`, `Lazada`, `khác` hoặc trống |
| 13 | Khoảng % doanh thu trực tuyến (năm tài chính gần nhất) | Multiple choice | `online_revenue_share_bin` | có | đúng một: `zero` `lt5` `5to10` `10to25` `25to50` `gt50` `unknown` `refuse` |
| 14 | Năm tài chính vừa khai | Short answer | `revenue_year` | không | ví dụ `2025` hoặc trống |
| 15 | Doanh thu năm đó (VND, số nguyên) | Short answer | `revenue_vnd` | không | số nguyên hoặc trống |
| 16 | Vai trò người trả lời | Multiple choice / short | `respondent_role` | không | text hoặc trống |
| 17 | Email (không bắt buộc) | Short answer | `respondent_email` | không | email hoặc trống |
| 18 | Ghi chú | Paragraph | `notes` | không | text hoặc trống |

Cột Google Form thừa (`Timestamp`, câu đồng ý): **xóa** trước khi join — không có trong schema khóa.

Dòng tiêu đề CSV (một dòng, copy):

```text
mst,company_name,vsic_4digit,ticker,website_url_self_report,has_website,has_product_catalog,has_order_cart,payment_methods,has_social_links,has_marketplace_links,marketplace_names,online_revenue_share_bin,revenue_vnd,revenue_year,respondent_role,respondent_email,notes
```

---

## 6. Xuất CSV và gửi lại repo

**Chưa tạo** thư mục `data/processed/survey/` trên repo cho đến khi có phiếu thật. **Không** thêm dòng giả.

### 6.1. Google Form → Sheet

1. Tạo Form, dán mục 3 (mô tả) + Câu 1–18 đúng kiểu ở mục 5.
2. Câu 13: 8 lựa chọn **đúng chữ** mục 4 (để recode không lệch).
3. Responses → Link to Sheets (hoặc Tải câu trả lời .csv).
4. Cột MST, VSIC, năm: định dạng **Plain text** trước khi mở bằng Excel (tránh mất `0` đầu và hậu tố `-001`).

### 6.2. Recode → schema khóa

1. Đổi tên cột theo mục 5.
2. Recode Có/Không/Không biết → `true`/`false`/`unknown`.
3. Câu 13 → đúng một mã bin; không để nguyên chữ tiếng Việt.
4. Câu 9 → token viết thường, cách nhau bằng `,`.
5. `revenue_vnd`: chỉ còn chữ số; ô từ chối / không biết = trống (không ghi `0` trừ khi DN khai đúng 0 đồng).
6. UTF-8, dấu phẩy ngăn cột; ô có dấu phẩy thì bọc `"…"`.
7. Kiểm tra: không trùng MST nếu không cố ý (chi nhánh khác MST thì giữ nguyên); `has_website` không được `unknown`; `online_revenue_share_bin` ∈ tám mã trên.

In giấy: nhập tay vào Sheet cùng quy tắc, rồi xuất CSV.

### 6.3. Đặt file vào repo (khi đã có phiếu thật)

```text
data/processed/survey/
  responses.csv          # đúng header mục 5; mỗi dòng một DN
  PROVENANCE.md          # ngày gửi, ai gửi (GVHD / SV), số phiếu, năm tham chiếu
  README.md              # 1 đoạn: đây là tự khai, chưa phải nhãn vàng website
```

Không copy nhãn máy / mini-gold vào file này. Khớp form ↔ web: cùng `mst` (và `ticker` nếu có). Ước `doanh thu × %` **chỉ** khi `revenue_vnd` là số dương và bin **không** phải `unknown` / `refuse` (bin `zero` → ước 0). **Không** suy từ HTML hay từ số demo trong `data/seeds/companies.json`.

---

## 7. Giới hạn

- File này **chỉ là bộ câu hỏi**. **Chưa gửi** 100–200 DN. Không có số liệu khảo sát trên repo.
- Không thay điều tra ICT / GSO. Không suy tỷ lệ ngành cả nước từ form này.
- Sáu cờ website là **tự khai**; khác với máy đọc HTML và khác với nhãn tay trên sổ tay gán nhãn. Cột MXH / sàn trên form hỏi **kênh của DN**; máy chỉ thấy **link trên website**.
- Không ước GMV sàn, không Digital VA, không bịa GSO/OECD, không bịa phiếu.
- `website_language` có trong schema máy — **cố ý không** có trong CSV khảo sát.

Khi form đã gửi và có CSV thật: để vào `data/processed/survey/` kèm `PROVENANCE.md`, rồi mới viết bước join.
