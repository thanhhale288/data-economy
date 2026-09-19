# Khớp form khảo sát ↔ cờ website (cascade)

**Ngày:** 19/9/2026  
**Phạm vi:** code khớp khóa + ước `DT × %` khi đã có doanh thu trên form. **Chưa có** 100–200 phiếu thật.

Đây không phải báo cáo lab. File này ghi rõ khóa khớp, khi nào **bỏ qua** ước doanh thu, và vì sao output chưa phải số nghiên cứu.

---

## 1. Việc này làm gì

Khi cô (hoặc nhóm sau) gửi CSV khảo sát, lệnh:

```bash
PYTHONPATH=. python3 -m crawlers.survey_join recode --src form.csv --dest locked.csv
PYTHONPATH=. python3 -m crawlers.survey_join --survey locked.csv --out dir
PYTHONPATH=. python3 -m crawlers.survey_join plan --survey locked.csv --out dir
```

ghép từng dòng form với cờ máy đã chạy trên website (`data/processed/extraction_cascade/indicators_raw.jsonl`) và, **chỉ khi form có doanh thu dương**, nhân với điểm giữa (midpoint) của khoảng `% doanh thu online`.

Không cào sàn. Không gọi mạng. Không lấy doanh thu từ `data/seeds/companies.json` (số demo cũ).

**Hiện chưa có file khảo sát thật** — không được nhét hàng khung MST (`frame_pilot`) giả làm “phiếu trả lời”. Test dùng 2–3 dòng giả (`0000000000`, ticker `TEST`) trong `tests/survey_join/fixtures/`.

---

## 2. Khóa khớp (thứ tự)

Chuẩn hóa **MST** (mã số thuế): xóa khoảng trắng, **giữ** hậu tố chi nhánh có gạch (`0101552800-003` ≠ `0101552800`).

Phía web: `firm_id` trong JSONL cascade = **mã cổ phiếu** với DN niêm yết (ví dụ `RAL`) hoặc **MST** với mẫu khung thí điểm (ví dụ `0101552800-003`). Cờ tầng luật (`tier1`) chỉ đọc khi `fetch_ok` (tải trang được).

1. `survey.mst` == `cascade.firm_id` (ghi `web_match_via=mst`; nếu MST cũng có trong khung `frame_pilot` thì bước 2 được ưu tiên ghi nhận)  
2. `survey.mst` == `frame_pilot.tax_code` rồi map sang cascade cùng MST đó (`web_match_via=frame_pilot`)  
3. nếu còn ticker: `survey.ticker` == `cascade.firm_id` (`web_match_via=ticker`)  
4. phiếu **chỉ MST**, không ticker: `survey.mst` → `tax_id` trong [`data/raw/url_finder/identity_28.json`](../../data/raw/url_finder/identity_28.json) → ticker → cascade (`web_match_via=listed_tax_id`). File identity thiếu thì bỏ bước này, không crash, không bịa URL.

Dòng form **không khớp** vẫn giữ trong file ra: `web_match=false`, cờ web = null — **không bịa URL**.

Hàm / lệnh `plan`: DN unmatched có URL tự khai `http(s)` → `cascade_self_report` (file `frame_urls_self_report.json` cho `--frame-urls`); có tên+MST không URL → `needs_url_finder` (không đoán domain); thiếu trường → `unactionable`.

Cột lệch form vs máy (chỉ khi đã khớp **và** `fetch_ok`): `disagree_has_order_cart` và các cờ tương ứng (catalog, MXH, link sàn, thanh toán, có website).

---

## 3. Ước DT × % — khi nào bỏ qua

`online_revenue_share_bin` ∈ {`zero`, `lt5`, `5to10`, `10to25`, `25to50`, `gt50`, `unknown`, `refuse`}.

Midpoint **chỉ** khi `revenue_vnd` là số **dương** và bin không phải `unknown` / `refuse`:

| bin | midpoint |
|-----|----------|
| zero | 0.0 |
| lt5 | 0.025 |
| 5to10 | 0.075 |
| 10to25 | 0.175 |
| 25to50 | 0.375 |
| gt50 | 0.75 (khoảng rộng; cột `estimate_caveat` ghi chú) |

Thiếu doanh thu, doanh thu ≤ 0, hoặc bin `unknown`/`refuse`/sai → `estimated_online_revenue` = null, điền `estimate_skipped_reason`. File khảo sát trống / không tồn tại → **lỗi rõ**, không đẻ hàng giả.

---

## 4. Việc cố ý chưa làm

- 100–200 phiếu DN chế tạo (Google Form) — chưa gửi.  
- Dán nhãn tay 6 cờ / P/R so người.  
- GSO, suy rộng cả nước, GMV sàn.
