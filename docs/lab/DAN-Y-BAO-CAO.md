# Dàn ý báo cáo lab — khung xương

**Ngày:** 19/9/2026  
**Vai trò:** skeleton cho «Báo cáo lab» — [`docs/plan.md`](../plan.md) §3.  
**Không phải:** bản 25 trang hay kết quả giả. Điền từ file neo khi viết bản thật. Số dưới đây đã có trên đĩa (đối chiếu 19/9/2026) và chỉ được gọi **pilot** (mẫu nhỏ) — không phải ước lượng cả nước. Không lấy `docs/archive/proposal-v*` làm claim hiện tại.

---

## Mục lục đề xuất — 7 mục

| # | Mục | File neo |
|---|-----|----------|
| 1 | Mở đầu | [`docs/plan.md`](../plan.md) |
| 2 | Phương pháp | ADR-0004, cascade PROVENANCE, handbook, khung form |
| 3 | Dữ liệu đã chạy | frame_pilot, url_finder, cascade summary, jp_calibration |
| 4 | Hạn chế | PROVENANCE / `caveat` từng artifact |
| 5 | Việc còn lại | plan §3 |
| 6 | Không viết ở đây | — (claim cấm) |
| 7 | Phụ lục tùy chọn | Nhật: README calibration; GSO: chưa có — **chặn** |

---

## 1. Mở đầu

Câu hỏi cô đặt (MST → web, cờ trên trang, % doanh thu) khác phần **đã dựng**: hệ thống đọc website + số chạy mẫu nhỏ. Đây là báo cáo **lab**, không công bố suy rộng. Không mở đầu Digital VA / IIP / đề xuất v2–v4.

**Cite:** [`docs/plan.md`](../plan.md).

---

## 2. Phương pháp

Chuỗi làm việc, không công thức mới: khung MST công khai (không phải khung GSO) → tìm URL → tải trang chủ → 6 cờ trên **chính website DN** (catalog, giỏ, thanh toán, MXH, link sàn, ngôn ngữ; tầng luật rồi LLM) → form khảo sát và nhãn tay (**thiết kế sẵn, chưa chạy đủ**).

| Bước | File |
|------|------|
| LLM lab `qwen3:8b` ghim | [`docs/adr/0004-local-llm-ollama.md`](../adr/0004-local-llm-ollama.md) (`ml/local_llm/pin.json`) |
| Đọc 6 cờ / so máy | [`data/processed/extraction_cascade/PROVENANCE.md`](../../data/processed/extraction_cascade/PROVENANCE.md) |
| Quy tắc nhãn người (chưa đóng) | [`docs/annotation-handbook-v1.md`](../annotation-handbook-v1.md) |
| Form (chưa gửi 100–200 DN) | [`docs/lab/KHAO-SAT-DOANH-NGHIEP.md`](KHAO-SAT-DOANH-NGHIEP.md) |

---

## 3. Dữ liệu đã chạy (pilot — không phải cả nước)

Chỉ **năm số** này. Không làm tròn, không suy Section C.

| Số | Định nghĩa đúng | File |
|----|-----------------|------|
| **800** | MST duy nhất listing masothue (VSIC 10/22/25); **không** khung GSO | [`data/raw/frame_pilot/PROVENANCE.md`](../../data/raw/frame_pilot/PROVENANCE.md) |
| **12/28** | URL-finder trúng domain vàng / 28 DN niêm yết đã biết có web | [`data/processed/url_finder/metrics.json`](../../data/processed/url_finder/metrics.json) |
| **89/128 `fetch_ok`** | 89 trang chủ tải được / 128 đã thử; tỷ lệ cờ máy **trên 89** | [`data/processed/extraction_cascade/summary.json`](../../data/processed/extraction_cascade/summary.json) |
| **21/300** | URL-finder trúng URL bạc gBizINFO / mẫu 300 công ty Nhật | [`data/processed/jp_calibration/README.md`](../../data/processed/jp_calibration/README.md) |
| **`qwen3:8b`** | Model local đã ghim — hạ tầng tái lập, chưa P/R nghiên cứu | ADR-0004 |

`fetch_ok` = tải được trang chủ (không bịa HTML khi HTTP/DNS lỗi). Search từng bị chặn (HTTP 202) — ghi trong `metrics.json`.

---

## 4. Hạn chế

800 / 12/28 / 89/128 / 21/300 đều **pilot**. Khung 800 không đại diện sản xuất cả nước. Chưa có P/R so người (handbook có quy tắc, nhãn chưa đóng). Không trọng số khảo sát; HTML không cho doanh thu.

**Cite:** `PROVENANCE.md` frame_pilot · `caveat` trong url_finder / cascade summary · [`docs/annotation-handbook-v1.md`](../annotation-handbook-v1.md).

---

## 5. Việc còn lại

Khớp [`docs/plan.md`](../plan.md) §3 (đang làm vs còn chặn). **Đang có trên repo:** bộ câu hỏi [`KHAO-SAT-DOANH-NGHIEP.md`](KHAO-SAT-DOANH-NGHIEP.md) (chưa gửi DN); khung nhãn 6 cờ + handbook (ô người trống); khớp form↔web và `DT × %` trên fixture khi code đã vào repo. **Còn chặn:** gửi form 100–200 DN; dán nhãn tay đủ (tối thiểu 20, đủ thì 89) → P/R; `DT × %` trên mẫu thật; GSO / Nhật sâu → mục 7.

---

## 6. Không viết ở đây

| Cấm | Vì sao |
|-----|--------|
| **GMV sàn** | Không cào listing; cascade chỉ thấy **link ra sàn** trên web DN |
| **Digital VA** | KPI demo cũ, đã gỡ khỏi luận điểm bảo vệ |
| **MAPE IIP** | Leftover dự báo chỉ số sản xuất; không bảo vệ được |
| **Suy rộng cả nước** | Không khung GSO; 800 ≠ Section C Việt Nam |
| **P/R người** | Nhãn chưa đóng — chưa có bảng so người |

Không bịa khoảng tin cậy quốc gia; không copy số từ `docs/archive/proposal-v*`.

---

## 7. Phụ lục tùy chọn — GSO / Nhật sâu

**Chặn** đến khi cô đồng ý và (với GSO) có giấy phép / số liệu chính thức. Không nhét vào thân «cho đủ trang».

- **Nhật sâu:** nếu cô muốn phụ lục kỹ thuật URL-finder — [`data/processed/jp_calibration/README.md`](../../data/processed/jp_calibration/README.md) rồi `metrics.json`. **21/300** vẫn là pilot, search đã chết; không so sánh quốc gia.  
- **GSO:** chưa có trên repo. Nhóm sau chỉ viết **sau khi** đề xuất rõ và đã xin khung — không bịa bảng GSO.

---

*Hết dàn ý (~1–2 trang). Điền thật: nhóm sau và cô chốt độ dài; file này cố ý không giả vờ đã có báo cáo.*
