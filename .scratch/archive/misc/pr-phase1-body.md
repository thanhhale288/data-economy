## Tóm tắt

Đóng **Giai đoạn 1** của nền tảng Kinh tế số ngành Chế biến, Chế tạo (VSIC Section C): database + seed 10 DN mẫu + crawler macro thật từ NSO/GSO và OECD — không bịa số liệu khi nguồn thiếu.

### Đã làm gì?

1. **Mapping & seed**
   - Bảng VSIC ↔ ISIC: Section C, divisions 10–33, mã 4-digit cho 10 DN
   - Seed cố định: RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BWE
   - Schema qua **Alembic** (không phụ thuộc `create_all`); seed chạy lại không trùng

2. **Crawler GSO/NSO (macro Việt Nam)**
   - **IIP Section C**: SDMX live từ `nsdp.nso.gov.vn` (host cũ `gso.gov.vn` đã chết)
   - **Shipment + Inventory**: PX-Web `E07.03` / `E07.04` (NSO chỉ công bố **theo năm** → step-hold sang tháng khi lưu)
   - Có fallback có nguồn dưới `data/raw/` khi mạng lỗi — **không random**

3. **Crawler OECD**
   - **INDIGO @ VNM**: dữ liệu thật (năm → step-hold tháng)
   - **MEI_IP @ EA20**: peer leading indicator (Việt Nam không có series này trên OECD)
   - MEI/BCI/ICT cho VNM: ghi **unavailable**, không bịa
   - Cột `oecd_indicators.source`: `OECD` / `OECD_FALLBACK` / `OECD_PEER`

4. **Hạ tầng & kiểm thử**
   - Migrations, pipeline trigger ghi log crawl, feature join IIP + INDIGO + MEI peer
   - Test crawler: `tests/gso` + `tests/oecd`
   - Cập nhật `docs/plan.md`, `CONTEXT.md`, ADR-0001

### Chưa nằm trong PR này (Phase 2+)

- Crawl micro DN / marketplace thật, ML train, dashboard hoàn chỉnh, benchmark

## Cách kiểm tra

- [ ] `alembic upgrade head`
- [ ] `PYTHONPATH=. python -m backend.app.seed`
- [ ] `PYTHONPATH=. python -m pytest tests -q`
- [ ] (tuỳ chọn) gọi crawl GSO/OECD và xem đủ `IIP_C`, `SHIPMENT_C`, `INVENTORY_C`, `INDIGO`, `MEI_IP@EA20`

## Ghi chú

Chi tiết tiến độ và URL nguồn: xem `docs/plan.md` mục **Tiến độ thực tế** và mục Luồng A/C.
