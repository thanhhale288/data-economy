# Gói trình bày buổi gặp GVHD (Evol-1 T07)

Bộ tài liệu **in được**, kể được trong **~15 phút**. Số liệu chỉ lấy từ artifact đã chạy
(T02–T05 trên `main`); chỗ chưa có số thì ghi rõ *chưa chạy / đang làm*.

## In trước buổi gặp (checklist)

| # | Tài liệu | File | Ghi chú in |
|---|----------|------|------------|
| 1 | One-pager (1 tờ A4) | [`one-pager.md`](one-pager.md) | In 1 bản cho GVHD + 1 bản cầm tay |
| 2 | Slide / kịch bản 15′ (7 trang) | [`slides.md`](slides.md) | In 1 bản / trang (hoặc trình chiếu PDF nếu convert) |
| 3 | Proposal v4 | [`../proposal-v4.md`](../proposal-v4.md) | In toàn bộ hoặc ít nhất mục 1–4 + lịch tuần |
| 4 | Công văn GSO (Phụ lục A) | [`cong-van-a-gso.md`](cong-van-a-gso.md) | **Giấy tiêu đề đơn vị**; điền chỗ `[…]` rồi ký |
| 5 | Công văn iDEA (Phụ lục B) | [`cong-van-b-idea.md`](cong-van-b-idea.md) | Cùng quy trình với A |

Nội dung công văn giữ nguyên proposal-v3 Phụ lục A–B (proposal-v4 chỉ tham chiếu lại).

## Thứ tự nói (khớp `docs/evol-1.md`)

1. Đã làm / tái định vị (4′) — slide 1–2  
2. Kết quả chạy thật (5′) — slide 3–4  
3. Điểm mới v4: hiệu chuẩn Nhật (3′) — slide 5  
4. Ba đề nghị cụ thể (3′) — slide 6–7  

## Nguồn số (đừng nhớ miệng)

| Chỉ số | Giá trị | Artifact |
|--------|---------|----------|
| Khung pilot | **n = 800** (VSIC 10: 300 · 22: 250 · 25: 250) | `data/raw/frame_pilot/` |
| URL-finder v0 | hit **12/28 (42.9%)**; precision khi đã quyết định **66.7%**; abstain **35.7%** | `data/processed/url_finder/metrics.json` |
| Thác trích v0 | cohort **128**; `fetch_ok` **89 (69.5%)** | `data/processed/extraction_cascade/summary.json` |
| Tầng 1 trên `fetch_ok` | catalog **74.2%** · cart **51.7%** · MXH **52.8%** · thanh toán / link sàn **~6.7%** | cùng summary — *mô tả pilot, chưa trọng số quốc gia* |
| Mini gold P/R | **chưa** (T06 đang gán tay) | — |
| Pilot Nhật n≈300 | **chưa** (T08) | — |

## Sau buổi gặp

Ghi quyết định GVHD vào checklist cuối [`slides.md`](slides.md) (ký công văn? nhánh Nhật trong đề tài cấp trường? SV gán nhãn?).
