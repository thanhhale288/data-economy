# Phase 2 checklist — Enterprise crawl & Digital detection

**Branch:** `cursor/phase2-enterprise-digital`  
**Nguồn:** `.cursor/skills/project-roadmap/SKILL.md` task 5–9 + `docs/plan.md` Giai đoạn 2  
**Ranh giới:** đúng 10 ticker (RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BMP); không đổi Digital VA; không bịa số crawl; không viết lại Phase 1 macro trừ bug có chứng cứ.

---

## Task 5 — Company crawler
*Blocked by: task 2 (done)*

- [x] Enrich/đồng bộ metadata 10 DN từ seed + nguồn công bố (tên, VSIC, website, …)
- [x] Website chính thức ghi vào `companies` / `digital_presence` (`channel_type=website`)
- [x] BCTC có cấu trúc → `financial_reports` (ưu tiên HTML/XBRL/API; PDF chỉ khi cần)
- [x] Field thiếu = `null` + provenance/fallback rõ — không nội suy bịa
- [x] Idempotent: chạy lại không nhân bản sai / không lệch 10 ticker
- [x] Tests parser/ingest (fixture) + chạy được trên 10 DN (live hoặc fallback có nguồn)

**Nghiệm thu:** DB có đủ 10 `companies` đã enrich; ít nhất một phần `financial_reports` có field cấu trúc thật hoặc null có lý do ghi rõ.

---

## Task 6 — Website digital detector
*Blocked by: task 5*

- [x] Rule-based detect ecommerce / giỏ hàng / checkout trên website DN
- [x] Cập nhật `has_ecommerce_site`, `digital_presence.has_checkout`
- [x] Khi HTTP fail / block: không đoán — ghi fail + giữ trạng thái cũ hoặc false có log
- [x] Tests với HTML fixture (có / không checkout)

**Nghiệm thu:** Detector chạy cho cả 10 DN; kết quả có thể kiểm chứng bằng fixture + spot-check vài site live.  
**Accepted:** 2026-07-18 — [Wave2 Task6](611ce245-a6d7-4ebc-9788-ac2a44141665); `tests/companies` 12 passed. Live spot-check optional.

---

## Task 7 — Marketplace crawler
*Blocked by: task 5* *(song song được với task 6)*

- [x] Tìm shop Shopee / TikTok (Lazada optional) gắn với 10 DN
- [x] Scrape listing: giá, units_sold (nếu có), revenue estimate khi đủ dữ liệu
- [x] Persist `digital_presence` + `marketplace_listings`
- [x] Rate limit; anti-bot: empty + log + fallback có provenance — **không** bịa sales
- [x] Tests parse/fixture; không phụ thuộc mạng cho unit test

**Nghiệm thu:** Crawl chạy được end-to-end cho seed set; listing/shop chỉ từ scrape hoặc seed đã có nguồn, không random.  
**Accepted:** 2026-07-18 — [Wave2 Task7](2472fe86-c0c7-472a-84e4-20abcc832252); `tests/marketplace` 15 passed. Matcher đầy đủ → Task 8.

---

## Task 8 — Shop-matcher
*Blocked by: task 7*

- [x] Matcher shop name ↔ tên DN (fuzzy / TF-IDF; threshold **0.65** theo CONTEXT)
- [x] Mục tiêu QA: precision > 90% trên 10 DN (ghi lại bảng match thủ công)
- [x] Chỉ link khi `is_match`; dưới ngưỡng → không gán company
- [x] Tests cặp positive/negative từ seed / fixture

**Nghiệm thu:** Bảng QA 10 DN; matcher có test; không gán shop sai với confidence cao.  
**Accepted:** 2026-07-18 — Wave3 Task8; QA precision 100% (19 pairs); `tests/shop_matcher` + `tests/marketplace` 46 passed. See `.scratch/phase2/shop-matcher-qa.md`.

---

## Task 9 — Digital metrics
*Blocked by: task 6, 8, 3 (GSO — done)*

- [x] `online_revenue_est` từ Σ(price × units_sold) listings (hoặc tỷ lệ ngành khi thiếu — ghi rõ nguồn)
- [x] Adoption / channel diversity từ website + marketplace đã verify
- [x] Digital VA theo đúng công thức CONTEXT — **không đổi công thức**
- [x] Persist `digital_metrics` per company (và industry_share nếu có trong plan)
- [x] Tests tính toán với fixture số liệu cố định

**Nghiệm thu:** 10 DN có digital metrics tính từ dữ liệu Phase 2; công thức Digital VA khớp CONTEXT.  
**Accepted:** 2026-07-18 — Wave4 Task9; marketplace Σ only (excludes platform=website); undocumented `×0.15` rejected; `tests/digital_metrics` 15 passed; Phase 2 regression 80 passed. See `.scratch/phase2/wave4-task9-report.md`.

---

## Phase 2 done khi

- [x] Task 5–9 đều tick
- [x] Không mở rộng ticker; không đụng crawler GSO/OECD trừ bug
- [ ] `docs/plan.md` Tiến độ: Giai đoạn 2 → hoàn thành (khi user yêu cầu cập nhật)
- [x] Tests liên quan Phase 2 pass (**80 passed** — companies/financial/marketplace/shop_matcher/digital_metrics)

**Phase 2 code complete:** 2026-07-18 on `cursor/phase2-enterprise-digital`. Chưa commit/push trừ khi user yêu cầu.

## Thứ tự làm

```
5 → (6 ∥ 7) → 8 → 9
```
