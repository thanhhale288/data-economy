# plain-task-close — reference

## Ví dụ tốt vs xấu

**Xấu:**  
- Đã implement OCR path cho BCTC.  
- Tests pass. PR opened.

**Tốt:**  
- **Một câu:** Hệ thống giờ đọc được báo cáo tài chính dạng PDF scan (ảnh), không chỉ PDF có chữ copy được.  
- **Bạn sẽ thấy gì:** Khi nguồn là scan, pipeline thử OCR trước; nếu OCR fail vẫn báo lỗi rõ, không bịa số.  
- **Làm thế nào:** (1) Thêm nhánh nhận diện PDF scan vs text. (2) Gọi OCR cho scan. (3) Giữ luồng extract cũ cho text-PDF. (4) Test với file mẫu.  
- **Hạn chế:** Chưa chạy OCR trên toàn bộ 10 DN; chỉ spike task #53.

## Thuật ngữ hay gặp (giải thích inline khi dùng)

| Term | Giải thích ngắn (mẫu) |
|------|------------------------|
| PR (Pull Request) | Gói thay đổi trên GitHub chờ bạn review/merge |
| AC (Acceptance criteria) | Checklist “xong task” trong plan |
| E2E (end-to-end) | Test cả luồng từ API tới giao diện |
| Parquet | File bảng dữ liệu sạch sau bước cleaning (không phải DB) |
| Registry (model) | Chỗ lưu metadata model ML đã train (loại model, lỗi đo) |
| OCR | Nhận chữ từ ảnh/PDF scan |
| Fallback | Cách dự phòng khi nguồn chính thiếu — phải nói rõ có invent số không |
| VSIC / IIP | Mã ngành VN / chỉ số sản xuất công nghiệp — xem CONTEXT nếu cần sâu |
| Digital VA | Giá trị gia tăng số — công thức cố định trong CONTEXT |

Không copy cả bảng vào mọi task — chỉ giải thích term **xuất hiện** trong task đó.

## Mẫu đầy đủ

```markdown
## Task #53 — Đọc BCTC PDF dạng scan (OCR)

### Một câu
Demo có thêm đường đọc báo cáo tài chính khi file là PDF scan, không chỉ PDF chọn được chữ.

### Bạn sẽ thấy gì (đã làm được gì)
- Pipeline thử OCR khi phát hiện PDF scan; PDF text vẫn dùng luồng cũ.
- Lỗi OCR/thiếu file hiện rõ — không điền số giả vào dashboard.
- Branch: `cursor/epic4-phase1-task53-bctc-ocr-path`

### Làm thế nào (step-by-step, không code)
1. Xác định file PDF là scan hay text (heuristic / thư viện).
2. Nhánh scan: chạy OCR → đưa text vào bước extract hiện có.
3. Nhánh text: giữ spike task #52.
4. Chạy test với fixture scan + regression test text-PDF.

### Hạn chế / chưa làm được
- Chưa crawl live toàn bộ CafeF — chỉ spike + test local.
- Độ chính xác OCR phụ thuộc chất lượng scan; chưa có human QA hàng loạt.

### Thuật ngữ trong task này
- **OCR (nhận chữ từ ảnh)** — dùng cho PDF scan BCTC.
- **Extract (trích xuất)** — lấy số liệu tài chính từ text sau OCR/text-PDF.

### Git (một dòng)
Branch `cursor/...` · PR #… (nếu đã mở)
```

## Gắn vào handoff

Copy khối trên vào handoff section **Giải thích dễ hiểu** — không thay testing results.
