# Mẫu adjudicate gold (mắt người)

## Mục đích

Mẫu này (~23 URL duy nhất, phủ các strata A–I) dùng để **đo precision/recall thật** bằng mắt người trên cờ gold (`has_product_catalog`, `has_order_cart`, `payment_methods`, `social_links`, `marketplace_links`, `website_language`).

Phần còn lại của sheet `worksheet_89` được gắn nhãn / QA chủ yếu **có hỗ trợ AI** (machine pre_t1/pre_t2 + annotator). Mẫu này tách ra để human adjudication độc lập, không sửa sheet trong phiên này.

## Cách dùng

1. Mở **URL** trong trình duyệt (ưu tiên trang sống / www nếu apex lỗi).
2. So với mục **Cờ gold hiện tại** → tick **Đồng ý toàn bộ** hoặc **Sửa** từng cờ.
3. Ghi **Ghi chú** ngắn (bằng chứng: path `/gio-hang`, checkout, off-site store, parking, SPA trống, …).
4. Cột **Máy** chỉ tham chiếu — **không** copy máy thành gold.

**Số URL trong mẫu:** 23  
**Ngày cắt dữ liệu:** 2026-09-24  
**Sheet:** `worksheet_89` — spreadsheetId `1pRkyLjdX2RatlXbkd0SW_hzAFCJLm2oxlrz9ELbb40Q` (cột A:AH)

## Thống kê strata

- **A** (A cart gold=TRUE (giữ sau flips)): 3 URL
- **B** (B browser cart FALSE (từng TRUE)): 3 URL
- **C** (C máy cart TRUE vs gold FALSE (FP)): 2 URL
- **D** (D dead/blank/parking): 3 URL
- **E** (E catalog disagreement / flips gần đây): 3 URL
- **F** (F payment đã điền (không trống)): 3 URL
- **G** (G social/marketplace edge / bare-social KEEP FALSE): 2 URL
- **H** (H off-site cart KEEP FALSE): 2 URL
- **I** (I residual uncertain): 2 URL

## Mục lục

- [1. Son Hà — sonha.com.vn](#son-ha)
- [2. Lugia — lugia.com.vn](#lugia)
- [3. QNS — qns.com.vn](#qns)
- [4. Hưng Phát — hungphat.com.vn](#hung-phat)
- [5. Mạnh Thắng — manhthang.com.vn](#manh-thang)
- [6. An Phát Bioplastics — anphatbioplastics.com](#an-phat-bioplastics)
- [7. Biển Đông — biendong.com.vn](#bien-dong)
- [8. Đình Vũ — dinhvu.com.vn](#dinh-vu)
- [9. Hợp Thành — hopthanh.com.vn](#hop-thanh)
- [10. Đạt Phát — datphat.vn](#dat-phat)
- [11. An Nhơn (parking) — annhon.com](#an-nhon)
- [12. Giải Phóng — giaiphong.com.vn](#giai-phong)
- [13. Thương mại Dịch vụ — thuongmaidichvu.com.vn](#thuong-mai-dich-vu)
- [14. FPT — fpt.com.vn](#fpt)
- [15. Kim Long — kimlong.vn](#kim-long)
- [16. Điện Quang — dienquang.com](#dien-quang)
- [17. Vinamilk — vinamilk.com.vn](#vinamilk)
- [18. Đức Thịnh — ducthinh.com](#duc-thinh)
- [19. Taya — taya.com.vn](#taya)
- [20. Rạng Đông — rangdong.com.vn](#rang-dong)
- [21. Đức Giang — ducgiangchem.vn](#duc-giang)
- [22. Tiến Lên Group — tienlengroup.vn](#tien-len-group)
- [23. An Hà — anha.vn](#an-ha)

---

## 1. Son Hà — sonha.com.vn

- **firm_id(s):** 106069682
- **URL:** https://sonha.com.vn
- **Stratum:** B browser cart FALSE (từng TRUE)
- **source_cohort:** frame_pilot
- **row_number(s):** 4
- **reviewed / annotator / labeled_at:** TRUE / browser-cursor / 2026-09-24T16:30:00+07:00
- **notes (rút gọn):** BATCH-03 B: catalog TRUE; cart FALSE (t2); social FB/Zalo/YT; payment trống | FULLQA-2026-09-24: uncertain cart — KEEP TRUE | BROWSER-2026-09-24: cart FALSE — product pages only Shopee/ngoinhasonha; /cart 404

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=abstain cart=abstain payment=abstain social=FALSE mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 2. Lugia — lugia.com.vn

- **firm_id(s):** 318193000
- **URL:** https://lugia.com.vn
- **Stratum:** B browser cart FALSE (từng TRUE)
- **source_cohort:** frame_pilot
- **row_number(s):** 48
- **reviewed / annotator / labeled_at:** TRUE / browser-cursor / 2026-09-24T16:30:00+07:00
- **notes (rút gọn):** BATCH-04: catalog TRUE; cart FALSE; social FB; payment trống | FULLQA KEEP TRUE | BROWSER-2026-09-24: cart FALSE — Đặt mua = contact form; /cart 404

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=cod social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=null cart=null payment=(trống) social=FALSE mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 3. QNS — qns.com.vn

- **firm_id(s):** QNS
- **URL:** https://qns.com.vn
- **Stratum:** B browser cart FALSE (từng TRUE)
- **source_cohort:** listed28
- **row_number(s):** 83
- **reviewed / annotator / labeled_at:** TRUE / browser-cursor / 2026-09-24T16:30:00+07:00
- **notes (rút gọn):** BATCH-02 B: catalog TRUE; social FB/YT; payment abstain | FULLQA KEEP TRUE | BROWSER-2026-09-24: cart FALSE — only Liên hệ/phone/Zalo; /cart 404

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=TRUE cart=abstain payment=abstain social=abstain mkt=abstain lang=vi

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 4. Hưng Phát — hungphat.com.vn

- **firm_id(s):** 108501682, 0309129626-001, 0314342318-001
- **URL:** https://hungphat.com.vn
- **Stratum:** A cart gold=TRUE (giữ sau flips)
- **source_cohort:** frame_pilot
- **row_number(s):** 13, 24, 42
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T09:10:00+07:00
- **notes (rút gọn):** BATCH-03 B: catalog TRUE; cart FALSE; social FB/YT; payment trống | FULLQA-2026-09-24: lang KEEP vi (VN content despite html lang=en)

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: TRUE
- payment_methods: (trống) (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=null cart=null payment=(trống) social=FALSE mkt=FALSE lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 5. Mạnh Thắng — manhthang.com.vn

- **firm_id(s):** 0304531098-001, 0304531098-002
- **URL:** https://manhthang.com.vn
- **Stratum:** A cart gold=TRUE (giữ sau flips)
- **source_cohort:** frame_pilot
- **row_number(s):** 20, 21
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T08:10:00+07:00
- **notes (rút gọn):** CALIB-01: catalog có; cart FALSE (mua ngay→Zalo, /gio-hang 404); payment ĐỂ TRỐNG chờ Codebook (footer logo MoMo/COD/cards nhưng không checkout); social Zalo; no marketplace | FULLQA-2026-09-24: uncertain cart — KEEP TR…

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: TRUE
- payment_methods: (trống) (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=TRUE cart=TRUE payment=other social=abstain mkt=abstain lang=vi

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 6. An Phát Bioplastics — anphatbioplastics.com

- **firm_id(s):** AAA
- **URL:** https://anphatbioplastics.com
- **Stratum:** A cart gold=TRUE (giữ sau flips)
- **source_cohort:** listed28
- **row_number(s):** 64
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T09:12:00+07:00
- **notes (rút gọn):** BATCH-05: catalog TRUE; cart FALSE (t2); social LI/YT; payment trống (không copy cod)

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: TRUE
- payment_methods: (trống) (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=cod social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=null cart=abstain payment=abstain social=FALSE mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 7. Biển Đông — biendong.com.vn

- **firm_id(s):** 601171842
- **URL:** https://biendong.com.vn
- **Stratum:** C máy cart TRUE vs gold FALSE (FP)
- **source_cohort:** frame_pilot
- **row_number(s):** 53
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T09:15:00+07:00
- **notes (rút gọn):** BATCH-04: t2 không bằng chứng — FALSE; payment trống

### Cờ gold hiện tại
- has_product_catalog: FALSE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: FALSE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=FALSE mkt=FALSE lang=vi
- pre_t2: catalog=abstain cart=abstain payment=abstain social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 8. Đình Vũ — dinhvu.com.vn

- **firm_id(s):** 110454750
- **URL:** https://dinhvu.com.vn
- **Stratum:** C máy cart TRUE vs gold FALSE (FP)
- **source_cohort:** frame_pilot
- **row_number(s):** 15
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T09:10:00+07:00
- **notes (rút gọn):** BATCH-03 B: catalog TRUE; cart FALSE; social Zalo (bỏ sharer FB/X/LI); payment trống

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=null cart=null payment=(trống) social=FALSE mkt=FALSE lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 9. Hợp Thành — hopthanh.com.vn

- **firm_id(s):** 106898305
- **URL:** https://hopthanh.com.vn
- **Stratum:** D dead/blank/parking
- **source_cohort:** frame_pilot
- **row_number(s):** 7
- **reviewed / annotator / labeled_at:** TRUE / fullqa-mac / 2026-09-24T16:17:33+07:00
- **notes (rút gọn):** BATCH-03 B: t2 không bằng chứng catalog/cart — FALSE; payment trống | FULLQA-2026-09-24: dead/unreachable Mac http=000; gold blanked

### Cờ gold hiện tại
- has_product_catalog: (trống)
- has_order_cart: (trống)
- payment_methods: (trống) (blank = abstain)
- social_links: (trống)
- marketplace_links: (trống)
- website_language: (trống)

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=FALSE mkt=FALSE lang=vi
- pre_t2: catalog=abstain cart=abstain payment=abstain social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 10. Đạt Phát — datphat.vn

- **firm_id(s):** 201133137
- **URL:** https://datphat.vn
- **Stratum:** D dead/blank/parking
- **source_cohort:** frame_pilot
- **row_number(s):** 18
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-24T15:45:00+07:00
- **notes (rút gọn):** RECHECK-DEAD: vẫn chết — HTTPS TLS EOF, HTTP 403; gold_* trống | FULLQA-2026-09-24: reconfirm dead/unreachable Mac; gold already blank OK

### Cờ gold hiện tại
- has_product_catalog: (trống)
- has_order_cart: (trống)
- payment_methods: (trống) (blank = abstain)
- social_links: (trống)
- marketplace_links: (trống)
- website_language: (trống)

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=FALSE cart=FALSE payment=(trống) social=FALSE mkt=FALSE lang=vi
- pre_t2: catalog=abstain cart=abstain payment=abstain social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 11. An Nhơn (parking) — annhon.com

- **firm_id(s):** 0304152188-003
- **URL:** https://annhon.com
- **Stratum:** D dead/blank/parking
- **source_cohort:** frame_pilot
- **row_number(s):** 19
- **reviewed / annotator / labeled_at:** TRUE / fullqa-mac / 2026-09-24T16:17:33+07:00
- **notes (rút gọn):** RECHECK-DEAD: parking HugeDomains (http live); catalog/cart/social/mkt FALSE; payment trống | FULLQA-2026-09-24: parking HugeDomains/for-sale (http confirmed); ecommerce FALSE

### Cờ gold hiện tại
- has_product_catalog: FALSE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: FALSE
- marketplace_links: FALSE
- website_language: unknown

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=FALSE mkt=FALSE lang=en
- pre_t2: catalog=abstain cart=null payment=(trống) social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 12. Giải Phóng — giaiphong.com.vn

- **firm_id(s):** 105494187, 1801488750
- **URL:** https://giaiphong.com.vn
- **Stratum:** E catalog disagreement / flips gần đây
- **source_cohort:** frame_pilot
- **row_number(s):** 3, 62
- **reviewed / annotator / labeled_at:** TRUE / fullqa-mac / 2026-09-24T16:17:33+07:00
- **notes (rút gọn):** BATCH-03 B: copy t1 FALSE/FALSE; payment trống | FULLQA-2026-09-24: catalog TRUE — /san-pham vehicle product pages

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: FALSE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=FALSE cart=FALSE payment=(trống) social=FALSE mkt=FALSE lang=vi
- pre_t2: catalog=null cart=abstain payment=abstain social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 13. Thương mại Dịch vụ — thuongmaidichvu.com.vn

- **firm_id(s):** 105196007, 312761024
- **URL:** https://thuongmaidichvu.com.vn
- **Stratum:** E catalog disagreement / flips gần đây
- **source_cohort:** frame_pilot
- **row_number(s):** 2, 34
- **reviewed / annotator / labeled_at:** TRUE / fullqa-mac / 2026-09-24T16:17:33+07:00
- **notes (rút gọn):** BATCH-03 B: copy t1 catalog+social(Zalo); cart FALSE; payment trống | FULLQA-2026-09-24: catalog FALSE — service brochure not product catalog

### Cờ gold hiện tại
- has_product_catalog: FALSE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=FALSE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=abstain cart=abstain payment=abstain social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 14. FPT — fpt.com.vn

- **firm_id(s):** FPT
- **URL:** https://fpt.com.vn
- **Stratum:** E catalog disagreement / flips gần đây
- **source_cohort:** listed28
- **row_number(s):** 74
- **reviewed / annotator / labeled_at:** TRUE / fullqa-mac / 2026-09-24T16:17:33+07:00
- **notes (rút gọn):** CALIB-01: corporate catalog/solutions; no on-site cart (retail off-site); payment abstain; social FB/YT/LinkedIn; no marketplace; final fpt.com/vi | FULLQA-2026-09-24: catalog FALSE — corporate/services not SKU catalog

### Cờ gold hiện tại
- has_product_catalog: FALSE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=FALSE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=abstain cart=abstain payment=abstain social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 15. Kim Long — kimlong.vn

- **firm_id(s):** 106459280
- **URL:** https://kimlong.vn
- **Stratum:** F payment đã điền (không trống)
- **source_cohort:** frame_pilot
- **row_number(s):** 6
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T09:10:00+07:00
- **notes (rút gọn):** BATCH-03 B: catalog+cart; social TRUE; payment backfill checkout COD+CK

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: TRUE
- payment_methods: cod,other (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=null cart=null payment=(trống) social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 16. Điện Quang — dienquang.com

- **firm_id(s):** DQC
- **URL:** https://dienquang.com
- **Stratum:** F payment đã điền (không trống)
- **source_cohort:** listed28
- **row_number(s):** 73
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T07:52:00+07:00
- **notes (rút gọn):** CALIB-01: catalog+cart+checkout; social FB/LinkedIn/YT; no marketplace; Zalo widget no URL

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: TRUE
- payment_methods: cod,other (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=TRUE cart=TRUE payment=cod social=abstain mkt=abstain lang=vi

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 17. Vinamilk — vinamilk.com.vn

- **firm_id(s):** VNM
- **URL:** https://vinamilk.com.vn
- **Stratum:** F payment đã điền (không trống)
- **source_cohort:** listed28
- **row_number(s):** 90
- **reviewed / annotator / labeled_at:** TRUE / fullqa-mac / 2026-09-24T16:17:33+07:00
- **notes (rút gọn):** FULLQA-2026-09-24: lang vi (html lang=vi)

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: TRUE
- payment_methods: cod,other (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=cod social=TRUE mkt=TRUE lang=vi
- pre_t2: catalog=null cart=null payment=(trống) social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 18. Đức Thịnh — ducthinh.com

- **firm_id(s):** 313063960
- **URL:** https://ducthinh.com
- **Stratum:** G social/marketplace edge / bare-social KEEP FALSE
- **source_cohort:** frame_pilot
- **row_number(s):** 36
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T09:15:00+07:00
- **notes (rút gọn):** BATCH-04: catalog TRUE; cart FALSE; social FALSE (domain trần); payment trống

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: FALSE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=null cart=null payment=(trống) social=FALSE mkt=FALSE lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 19. Taya — taya.com.vn

- **firm_id(s):** TYA
- **URL:** https://taya.com.vn
- **Stratum:** G social/marketplace edge / bare-social KEEP FALSE
- **source_cohort:** listed28
- **row_number(s):** 88
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T09:12:00+07:00
- **notes (rút gọn):** BATCH-05: catalog TRUE; cart FALSE; social FALSE (zalo trần); payment trống

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: FALSE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=FALSE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=null cart=abstain payment=abstain social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 20. Rạng Đông — rangdong.com.vn

- **firm_id(s):** RAL
- **URL:** https://rangdong.com.vn
- **Stratum:** H off-site cart KEEP FALSE
- **source_cohort:** listed28
- **row_number(s):** 84
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T08:45:00+07:00
- **notes (rút gọn):** BATCH-02 B: catalog TRUE; cart FALSE (điểm mua hàng≠cart); social FB/YT; marketplace FALSE | FULLQA-2026-09-24: cart KEEP FALSE — off-site rangdongstore (labeled host)

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: TRUE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=TRUE mkt=FALSE lang=vi
- pre_t2: catalog=null cart=null payment=(trống) social=abstain mkt=FALSE lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 21. Đức Giang — ducgiangchem.vn

- **firm_id(s):** DGC
- **URL:** https://ducgiangchem.vn
- **Stratum:** H off-site cart KEEP FALSE
- **source_cohort:** listed28
- **row_number(s):** 71
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T09:12:00+07:00
- **notes (rút gọn):** BATCH-05: catalog TRUE; cart FALSE (t2); payment trống

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: FALSE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=FALSE mkt=FALSE lang=vi
- pre_t2: catalog=null cart=abstain payment=abstain social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 22. Tiến Lên Group — tienlengroup.vn

- **firm_id(s):** TLH
- **URL:** https://www.tienlengroup.vn
- **Stratum:** I residual uncertain
- **source_cohort:** listed28
- **row_number(s):** 87
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T09:12:00+07:00
- **notes (rút gọn):** BATCH-05: catalog TRUE; cart FALSE (t2); payment trống | FULLQA-2026-09-24: uncertain catalog — KEEP TRUE (brochure vs listing)

### Cờ gold hiện tại
- has_product_catalog: TRUE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: FALSE
- marketplace_links: FALSE
- website_language: vi

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=TRUE cart=TRUE payment=(trống) social=FALSE mkt=FALSE lang=vi
- pre_t2: catalog=abstain cart=abstain payment=abstain social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 

---

## 23. An Hà — anha.vn

- **firm_id(s):** 313344351
- **URL:** https://anha.vn
- **Stratum:** I residual uncertain
- **source_cohort:** frame_pilot
- **row_number(s):** 40
- **reviewed / annotator / labeled_at:** TRUE / Annotator / 2026-09-23T09:10:00+07:00
- **notes (rút gọn):** BATCH-03 A: empty — FALSE | FULLQA-2026-09-24: SPA/vite shell ~667B; lang remains unknown (insufficient content)

### Cờ gold hiện tại
- has_product_catalog: FALSE
- has_order_cart: FALSE
- payment_methods: (trống) (blank = abstain)
- social_links: FALSE
- marketplace_links: FALSE
- website_language: unknown

### Máy (tham chiếu, không phải gold)
- pre_t1: catalog=FALSE cart=FALSE payment=(trống) social=FALSE mkt=FALSE lang=unknown
- pre_t2: catalog=abstain cart=abstain payment=abstain social=abstain mkt=abstain lang=(trống)

### Checklist mắt người
- [ ] Đồng ý toàn bộ gold
- [ ] Sửa: catalog → ___
- [ ] Sửa: cart → ___
- [ ] Sửa: payment → ___
- [ ] Sửa: social → ___
- [ ] Sửa: marketplace → ___
- [ ] Sửa: language → ___
- Ghi chú: 
