# Mini gold (T06) — hướng dẫn nhanh

1. Đọc [`docs/annotation-handbook-v1.md`](../../../docs/annotation-handbook-v1.md).
2. Mở [`worksheet_89.csv`](worksheet_89.csv) (Excel / Google Sheets / Numbers).
3. Với mỗi dòng: mở `website_url` → điền `gold_*` → `reviewed=true` → ghi `annotator` + `labeled_at`.
4. Cột `pre_t1_*` / `pre_t2_*` chỉ là gợi ý máy — không phải nhãn vàng.
5. Khi đã `reviewed=true` tối thiểu ~20 dòng (đủ thì cả 89), báo agent hoặc chạy:

```bash
PYTHONPATH=. python3 -m crawlers.mini_gold eval
```

Artifact T05 nguồn: `../extraction_cascade/` (89 `fetch_ok`).
