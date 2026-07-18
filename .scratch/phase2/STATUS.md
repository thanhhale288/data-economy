# Phase 2 — Trạng thái thật (sau sửa review)

**Branch:** `cursor/phase2-enterprise-digital`  
**Ngày probe URL:** 2026-07-18  
**Tests:** `81 passed` (companies / financial / marketplace / shop_matcher / digital_metrics)

---

## 1. Đã sửa trong phiên này (theo review)

| Vấn đề | Sửa |
|--------|-----|
| Detector OR với seed (`live hoặc seed`) | Khi HTTP OK → **chỉ tin detector** |
| Shop seed bypass ngưỡng 0.65 | Seed cũng phải `is_match ≥ 0.65` mới gắn DN |
| `has_checkout` mặc định `True` | Đổi mặc định **`False`** (không đoán) |
| Marketplace crawl mọi company trong DB | Chỉ **10 ticker** `ALLOWED_TICKERS` |
| Adoption “verified” | Marketplace chỉ tính khi `match_confidence ≥ 0.65` |
| Detect sai URL (FPT corporate 403) | Detect trên **URL website channel** sẽ lưu (vd. fptshop) |
| Seed URL chết | HPG → `www.hoaphat.com.vn`; BWE → `binhminhplastic.com.vn` |

---

## 2. Đã làm những task gì — làm thế nào

### Task 5 — Company crawler
**Cách làm:** đọc seed 10 DN → upsert metadata → detect website → upsert `digital_presence` website → lấy BCTC (JSON/HTML parser; live URL templates **trống** → seed/fallback có provenance).  
**Được:** pipeline enrich idempotent + test fixture.  
**Chưa:** BCTC scrape live từ HOSE/CafeF (chưa gắn URL công bố có cấu trúc).

### Task 6 — Website detector
**Cách làm:** rule keyword + form/link checkout trong `website_detector.py`; fail HTTP → giữ flag cũ / seed lần đầu.  
**Được:** tách file + HTML fixtures; không OR seed khi live OK.  
**Chưa:** spot-check hàng ngày / detector JS-heavy SPA.

### Task 7 — Marketplace crawler
**Cách làm:** lấy shop từ **seed URL** → httpx scrape Shopee/TikTok → rate-limit → block thì seed/fallback listings.  
**Được:** parse offline + persist + provenance log.  
**Chưa:** tự **tìm** shop mới trên marketplace; live Shopee thường anti-bot (HTML captcha, không JSON listing thật).

### Task 8 — Shop-matcher
**Cách làm:** RapidFuzz + brand aliases trong `ml/shop_matcher/`; ngưỡng **0.65**.  
**Được:** QA precision 100% trên cặp gắn nhãn; seed cũng qua ngưỡng.  
**Chưa:** ML classifier / TF-IDF train thật; chưa có crawler discovery để matcher “tìm shop lạ”.

### Task 9 — Digital metrics
**Cách làm:** Σ listing shopee/tiktok/lazada; Digital VA đúng CONTEXT; bỏ `×0.15` bịa.  
**Được:** metrics + test fixture.  
**Chưa:** tỷ lệ ngành e-commerce có nguồn (VECOM/GSO) khi DN không có listing.

---

## 3. Data nào **chưa phải dữ liệu live thật**

| Loại | Nguồn hiện tại | Ghi chú |
|------|----------------|---------|
| BCTC / `financial_reports` | Chủ yếu **seed** `companies.json` + fallback copy | Không phải scrape BCTC năm thực từ sở GD |
| Listing Shopee/TikTok | Hầu hết **seed** (giá/sold demo) | Live bị captcha/anti-bot → không lấy được GMV thật |
| `online_revenue_est` | Tính từ listing seed ở trên | Không phải doanh thu TMĐT kiểm toán |
| Shop URL marketplace | Seed thủ công | Chưa discovery tự động |
| GSO/OECD | Phase 1 (thật / peer / fallback có provenance) | Không thuộc Phase 2 |

**Seed demo vẫn hữu ích** để chạy pipeline/test — nhưng **không** được báo cáo như số liệu thị trường đã crawl.

---

## 4. URL probe (live HTTP, 2026-07-18)

### Website

| Ticker | URL | Kết quả | Ghi chú |
|--------|-----|---------|---------|
| RAL | https://rangdong.com.vn | **200** OK | |
| HPG | https://hoaphat.com.vn (cũ) | Timeout | **Đã đổi seed** → `www.hoaphat.com.vn` (200) |
| VNM | https://vinamilk.com.vn | **200** OK | |
| FPT | https://fpt.com.vn | **403** | Corporate chặn bot; shop https://fptshop.com.vn **200** — detector dùng URL shop |
| GVR | https://gvr.com.vn | **ConnectError** | Domain seed có vẻ sai/niche; thử vài alias vẫn lỗi — **cần URL chính thức mới** |
| DGC | https://ducgiangchem.vn | **200** OK | |
| MSN | https://masangroup.com | **200** OK | Channel shop: winmart.vn **200** |
| PNJ | https://pnj.com.vn | **200** OK | |
| REE | https://reecorp.com | **200** OK | |
| BWE | https://bmp.com.vn (cũ) | Timeout | **Đã đổi seed** → `binhminhplastic.com.vn` (200) |

### Marketplace (seed)

| URL mẫu | HTTP | Thực chất |
|---------|------|-----------|
| shopee.vn/*_official | 200 | Body có **captcha** — không parse được listing JSON thật |
| tiktok.com/@vinamilk, @pnj | 200 | Body rất nhỏ (~1.5KB) — gần như shell/block |

→ Crawl marketplace **mắc ở anti-bot**, không phải thiếu URL handle (với 5 DN có shop trong seed).

### DN khó / không có shop seed

| Ticker | Lý do |
|--------|--------|
| HPG, GVR, DGC, REE, BWE | Seed **không** có Shopee/TikTok (B2B / ít TMĐT) — matcher **không bịa** shop |
| GVR | Website seed lỗi DNS/connect — cần tìm domain đúng (Cao su VN) |
| FPT | URL corporate ≠ URL bán hàng — đã xử lý bằng detect trên channel website |

---

## 5. Crawl đang **mắc** chỗ nào

```
[OK] Seed metadata → DB
[OK] Website detect (khi URL 200) → flags
[PARTIAL] BCTC → chỉ seed/fallback (chưa live HOSE)
[STUCK] Shopee/TikTok live listings → captcha / empty JSON → fallback seed
[MISSING] Live shop discovery (search by brand)
[MISSING] Industry e-commerce ratio có nguồn khi không có listing
[STUCK] GVR website — **đã đổi seed → vrg.vn** (2026-07-19)
[DEFER] Shopee/TikTok — user tạm bỏ qua
```

---

## 6. Tóm tắt một dòng

Phase 2 = **khung crawl + test + provenance seed/fallback chạy được**; số liệu micro (BCTC/listing/GMV) **chưa phải data live thị trường**. Đã vá checklist + URL GVR/`www` HPG; Shopee/TikTok tạm bỏ; còn **BCTC live** + quyết định **BWE nhựa vs Biwase**.

---

## 7. URL corrections (2026-07-19)

| Ticker | Quyết định |
|--------|------------|
| GVR | `https://vrg.vn` (thay `gvr.com.vn`) — probe 200 |
| HPG | Giữ `https://www.hoaphat.com.vn` — apex `hoaphat.com.vn` timeout từ crawler |
| BWE | Chờ user: seed = Nhựa Bình Minh (plan); `biwase.com.vn` = DN nước cùng ticker HOSE |
| FPT | Dual URL: IR/BCTC tập đoàn; ecommerce = fptshop |
| Shopee/TikTok | Tạm bỏ qua |