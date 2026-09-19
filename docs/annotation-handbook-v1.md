# Sổ tay gán nhãn v1 — Chỉ tiêu TMĐT trên website DN sản xuất

**Phiên bản:** v1 (Evol-1 T06)  
**Đối tượng:** người gán nhãn (annotator) — hiện là bạn; sau này SV theo T10/T13  
**Mục đích:** tạo **nhãn vàng** (gold standard) để đo precision/recall của tầng 1 (luật) và tầng 2 (LLM). Nhãn vàng **không** được lấy từ AI.

Tài liệu neo tinh thần: Eurostat ESSnet / OBEC (định nghĩa chỉ tiêu quan sát được trên web, ca biên, quyền abstain). Định nghĩa trường khớp schema T04/T05 trong repo.

---

## 1. Bạn đang làm gì?

Máy đã chạy sẵn trên **89 website tải được** (T05). Mỗi dòng trong bảng có cột **pre_*** = gợi ý từ máy. Việc của bạn:

1. Mở `website_url` trên trình duyệt.
2. Quan sát theo quy tắc dưới đây (trang chủ + trang menu rõ ràng: Sản phẩm, Giỏ hàng, Liên hệ…).
3. Điền cột **gold_*** theo sự thật bạn thấy.
4. Đặt `reviewed=true` khi xong dòng đó.

**Không** copy nguyên cột pre nếu chưa tự kiểm. Pre chỉ giúp bạn nhanh hơn.

**Không** cào / mở gian hàng Shopee–TikTok–Lazada để đếm sản phẩm — chỉ xem **có link ra sàn trên website DN** hay không.

---

## 2. Sáu chỉ tiêu (cùng schema máy)

| Trường | Ý nghĩa ngắn |
|--------|----------------|
| `has_product_catalog` | Có danh mục / danh sách sản phẩm để xem (không chỉ tin tức) |
| `has_order_cart` | Có giỏ hàng / đặt hàng / checkout / mua ngay **trên chính website này** |
| `payment_methods` | Phương thức thanh toán hiển thị (token: `vnpay`, `momo`, `cod`, `other`, `none`) |
| `social_links` | Có liên kết mạng xã hội chính thức (fanpage / kênh) |
| `marketplace_links` | Có liên kết tới gian hàng trên sàn (Shopee / TikTok Shop / Lazada / khác) |
| `website_language` | Ngôn ngữ trang: `vi` / `en` / `ja` / `mixed` / `unknown` |

### Giá trị hợp lệ khi gán

| Loại trường | Cách ghi trong CSV |
|-------------|-------------------|
| Bool (`has_product_catalog`, `has_order_cart`) | `true` / `false` / `abstain` |
| Presence list (`social_links`, `marketplace_links`) | `true` / `false` / `abstain` (chỉ hỏi **có/không**, không bắt buộc liệt kê URL) |
| `payment_methods` | Danh sách token cách nhau bằng dấu phẩy, ví dụ `vnpay,cod` — hoặc rỗng nếu không thấy — hoặc `abstain` — hoặc `none` nếu trang **nói rõ** không nhận thanh toán online |
| `website_language` | `vi` / `en` / `ja` / `mixed` / `unknown` / `abstain` |

`abstain` = bạn **không đủ bằng chứng** trên phạm vi đã xem (trang lỗi một phần, nội dung mơ hồ, không chắc). Abstain hợp lệ và tốt hơn đoán bừa.

---

## 3. Định nghĩa chi tiết + ca biên

### 3.1. `has_product_catalog`

**Có (`true`)** khi trang có danh mục / lưới / danh sách sản phẩm (hoặc dòng sản phẩm) để khách xem — ví dụ menu “Sản phẩm”, trang catalog, thẻ sản phẩm có tên/ảnh.

**Không (`false`)** khi chỉ có giới thiệu công ty, tin tức, hoặc từ “sản phẩm” trong khẩu hiệu mà không có danh sách xem được.

**Ca biên**

| Tình huống | Quyết định |
|------------|------------|
| Chỉ brochure PDF “sản phẩm” không có trang danh mục | `false` (trừ khi PDF mở ngay như catalog rõ) |
| B2B liệt kê dòng hàng (thép cuộn, ống…) không bán lẻ | `true` nếu là danh mục xem được |
| Chỉ dự án / case study không phải hàng bán | `false` |
| Từ khóa “sản phẩm” trong footer/tin tức, không có trang catalog | `false` |

### 3.2. `has_order_cart`

**Có (`true`)** khi trên **chính domain website DN** có giỏ hàng, nút mua/đặt hàng, checkout, “thêm vào giỏ”, form đặt hàng giao hàng.

**Không (`false`)** khi chỉ có “liên hệ báo giá”, “đại lý”, “điểm bán”, hoặc chỉ link ra sàn mà không đặt được trên site.

**Ca biên**

| Tình huống | Quyết định |
|------------|------------|
| Nút “Mua tại Shopee” (rời site) | `false` cho cart trên site; có thể `true` cho `marketplace_links` |
| Form “đặt hàng” B2B gửi email / sales | `true` nếu là luồng đặt hàng trên site; nếu chỉ “liên hệ” → `false` |
| “Cửa hàng / showroom” danh sách địa chỉ | `false` |

### 3.3. `payment_methods`

Chỉ ghi token **thấy rõ** trên trang (logo VNPay/MoMo, chữ COD / thanh toán khi nhận hàng, cổng khác → `other`).

- Không thấy gì → để **rỗng** (không phải `none`).
- `none` **chỉ** khi trang nói rõ không nhận thanh toán online / không hỗ trợ thanh toán.
- Không chắc đã xem đủ → `abstain`.

**Ca biên:** logo cổng thanh toán mờ / chỉ trong footer đối tác chung → chỉ ghi nếu gắn với mua hàng trên site; nếu nghi → `abstain`.

### 3.4. `social_links` (có / không)

**Có (`true`)** khi có link tới trang/kênh MXH **của DN** (Facebook fanpage, YouTube channel, Zalo OA, Instagram, LinkedIn company, TikTok **cá nhân/kênh**, X/Twitter…).

**Không (`false`)** khi không có.

**Ca biên — rất hay gặp**

| Tình huống | Quyết định |
|------------|------------|
| Nút **Share** Facebook/Twitter (chia sẻ bài viết) | `false` — đó không phải fanpage DN |
| Icon MXH trỏ `facebook.com/` hoặc URL rỗng / generic | `false` hoặc `abstain` nếu không mở được trang DN |
| YouTube embed video nhưng không có link kênh | `false` (không đếm là social link chính thức) |
| TikTok chỉ là kênh MXH, không phải shop | `true` cho social; **không** tự ghi marketplace trừ khi là shop/sàn |

### 3.5. `marketplace_links` (có / không)

**Có (`true`)** khi website DN có link tới gian hàng trên sàn: Shopee, Lazada, TikTok **Shop** / gian hàng bán, hoặc sàn khác rõ ràng.

**Không (`false`)** khi không có.

**Ca biên**

| Tình huống | Quyết định |
|------------|------------|
| `tiktok.com/@brand` chỉ là kênh video | social `true`, marketplace `false` trừ khi trang nói rõ shop / bán hàng trên TikTok |
| Banner “mua trên Shopee” có URL shop | `true` |
| Chỉ nhắc tên sàn trong bài PR, không có URL | `false` |

### 3.6. `website_language`

Ngôn ngữ **nội dung chính** trang bạn xem:

- `vi` — chủ yếu tiếng Việt  
- `en` — chủ yếu tiếng Anh  
- `ja` — chủ yếu tiếng Nhật  
- `mixed` — hai ngôn ngữ trở lên đều đáng kể (không chỉ vài từ)  
- `unknown` — không xác định được  
- `abstain` — trang lỗi / không đọc được đủ

Nút chuyển ngữ (VI/EN) mà nội dung đang mở là tiếng Việt → ghi `vi` (ngôn ngữ trang đang xem).

---

## 4. Tầng 1, tầng 2, và bạn

| Lớp | Là gì | Vai trò với bạn |
|-----|--------|-----------------|
| **Tầng 1** | Luật cứng trên HTML (từ khóa giỏ hàng, logo thanh toán, regex link…) | Cột `pre_t1_*` — gợi ý |
| **Tầng 2** | LLM local đọc text trang → JSON | Cột `pre_t2_*` — gợi ý; **có thể sai hoặc để trống** |
| **Bạn** | Quan sát website | Cột `gold_*` — **chuẩn** |

Khi tầng 1 và tầng 2 mâu thuẫn: **bạn thắng**. Ghi `notes` ngắn (ví dụ: “t1 bắt share Facebook; không có fanpage”).

Cảnh báo T05: nhiều ô tầng 2 có `value` trống dù không abstain — **đừng tin**; chỉ nhìn website.

---

## 5. Phạm vi xem trang

1. Trang chủ (URL trong bảng).  
2. Nếu cần: 1–2 trang trong menu rõ (“Sản phẩm”, “Mua hàng”, “Liên hệ”).  
3. Không bắt buộc duyệt toàn bộ site.  
4. Nếu sau vài phút vẫn không chắc một trường → `abstain` + `notes`.

Thời gian gợi ý: **~2–3 phút / DN** × 89 ≈ 3–4,5 giờ.

---

## 6. Cách điền worksheet

File: `data/processed/mini_gold/worksheet_89.csv`

Cột bắt buộc khi xong một dòng:

- Tất cả `gold_*` đã điền theo mục 2–3  
- `reviewed` = `true`  
- `annotator` = tên hoặc initials của bạn  
- `labeled_at` = ngày ISO (`2026-08-25`)  
- `notes` = tùy chọn (ca biên, lý do abstain)

Khi **đã `reviewed=true` tối thiểu ~20 dòng** (đủ thì cả 89), báo agent chạy:

```bash
PYTHONPATH=. python -m crawlers.mini_gold eval
```

Script chỉ đọc nhãn đã `reviewed`; không bịa thêm nhãn. Dưới 20 dòng thì khoảng tin cậy (Wilson) rất rộng — chưa nên kết luận.

---

## 7. Giới hạn v1

- Mini gold trên cohort pilot T05 (`fetch_ok`), **không** suy rộng quốc gia.  
- Không đo Cohen’s kappa (cần gán đôi — T13).  
- Không thay thế điều tra ICT / GSO.  
- Handbook này thích ứng cho Việt Nam + schema hiện có; không phải bản dịch nguyên văn StarterKit ESSnet.
