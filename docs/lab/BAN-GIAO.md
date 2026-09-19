# Gói xin rút và bàn giao đề tài lab

> **TẠM HOÃN GỬI** (19/9/2026). File này **vẫn đúng** khi sau này bàn giao. **Đừng gửi cô hôm nay.** Việc đang làm: bề nổi còn lại trên repo — xem [`docs/plan.md`](../plan.md).

**Ngày soạn:** 19/9/2026  
**Người gửi:** sinh viên đang phụ trách repo  
**Người nhận:** cô giáo hướng dẫn (GVHD) — **chưa gửi**  
**Nguồn sự thật trên repo:** [`docs/plan.md`](../plan.md) (cập nhật 19/9/2026)

Đây **không** phải báo cáo lab 25 trang. Đây là **gói một buổi** (bản nháp): đoạn xin rút, chỗ đã có trên repo, số đã chạy (đã đối chiếu file trên đĩa, 19/9/2026), việc nhóm sau, và checklist gặp 15 phút.

---

## 1. Mục đích

Em xin **rút khỏi đề tài đo lường** (khung mẫu, khảo sát, % doanh thu, suy rộng) và **bàn giao** code + dữ liệu + danh sách việc còn mở, để cô giao nhóm khác (hoặc sinh viên đo lường).

Em không xin “làm nốt đến tháng 12”. Em cũng không bỏ dở im lặng: các mục dưới đây chỉ đúng chỗ trên repo.

Lịch sử đề xuất cũ (Digital VA → OBEC–Nhật) nằm ở `docs/archive/`. **Không** lấy làm hướng nhóm mới trừ khi cô muốn.

---

## 2. Đoạn xin rút

*(Copy gửi email hoặc in một trang.)*

Em đã dựng được hệ thống đọc website doanh nghiệp sản xuất (tìm URL, 6 đặc trưng trên trang, LLM lab) và có số chạy thật trên mẫu nhỏ. Phần còn lại cô muốn — khảo sát 100–200 DN, ước % doanh thu online, nhãn tay đủ lớn, suy rộng / GSO — là **đề tài đo lường**, không phải thế mạnh của em (AI / hệ thống).

Em xin **rút khỏi đề tài** và **bàn giao** code, dữ liệu, tài liệu để cô giao nhóm khác (hoặc SV đo lường). Em sẵn sàng gặp 15 phút để chỉ chỗ chạy và việc còn mở.

Em không bỏ dở im lặng: có danh sách artifact và việc chưa làm ở dưới.

---

## 3. Bảng artifact

Không làm thêm cho “đẹp”. Chỉ **chỉ đúng chỗ**.

| Cô từng hỏi | Đã có trên repo | Đường dẫn | Nói thẳng |
|-------------|-----------------|-----------|-----------|
| MST → tìm web | URL-finder, **12/28** hit; search từng chết | `data/processed/url_finder/` (`metrics.json`, `predictions.json`, `manifest.json`) | Không phải SERP châu Âu 83–88% |
| Có web / catalog / giỏ / thanh toán / MXH / link sàn | Cascade 128 DN, **89 trang tải được** (`fetch_ok`); tỷ lệ tầng luật trên 89 | `data/processed/extraction_cascade/` (`summary.json`, `manifest.json`, `PROVENANCE.md`) | Máy nói; **chưa** P/R so người (nhãn tay chưa đóng) |
| % DT / GMV / 9000 tỷ | Không có từ HTML | — | Cần form cô gửi × doanh thu nếu có; **không** cào sàn |
| Không nhãn thì lệch? | Chưa có bảng P/R người | — | Việc nhóm sau: dán ~20–89 site |
| Form 100–200 | Chưa gửi | — | Nhóm sau soạn + cô gửi |
| Nhật | Pilot **21/300**, search chết | `data/processed/jp_calibration/` (`README.md`, `metrics.json`) | Phụ lục kỹ thuật, không phải thân đề tài |
| GSO | Chưa xin | — | Nhóm sau khi đề xuất đã rõ |
| Demo web | Đã gỡ Digital VA / MAPE không bảo vệ được | `frontend/` + `README.md` | Còn nền tảng học kỳ (Epic 1–5) |
| Khung MST công khai | **800** DN (thư mục thuế công khai, **không** phải khung GSO) | `data/raw/frame_pilot/` (`frame_pilot.csv`, `PROVENANCE.md`) | Không đại diện cả nước Section C |
| LLM lab | Model `qwen3:8b` ghim, temperature 0 | `docs/adr/0004-local-llm-ollama.md`, `ml/local_llm/pin.json` | Hạ tầng tái lập; chưa phải số P/R nghiên cứu |

---

## 4. Số mang miệng (có file) — đã đối chiếu đĩa 19/9/2026

Các số dưới đây trùng [`docs/plan.md`](../plan.md) §3 và **đã đếm lại từ file đóng băng trên disk** (không crawl lại). Không dùng số từ thí nghiệm nháp chưa commit.

| Số | Ý nghĩa (đúng định nghĩa này) | Thư mục / file |
|----|-------------------------------|----------------|
| **800** | 800 MST duy nhất trên listing masothue (VSIC 10/22/25) — **không** phải khung GSO | `data/raw/frame_pilot/frame_pilot.csv` |
| **12/28** | URL-finder **trúng domain vàng** / 28 DN niêm yết đã biết có website (seed), không phải “12 trang tải được” | `data/processed/url_finder/metrics.json` |
| **89/128 `fetch_ok`** | 89 DN tải được trang chủ / 128 DN đã thử (28 niêm yết + 100 frame_pilot). Tỷ lệ cờ máy tính trên 89, không trên 128 | `data/processed/extraction_cascade/summary.json` |
| **21/300** | URL-finder **trúng URL bạc gBizINFO** / mẫu 300 công ty Nhật. Không lấy 299/300 NTA join làm số miệng | `data/processed/jp_calibration/metrics.json` |
| **`qwen3:8b` ghim** | LLM local lab, digest trong `ml/local_llm/pin.json` | ADR-0004 (`docs/adr/0004-local-llm-ollama.md`) |

`fetch_ok` = trang chủ tải được (không bịa nội dung khi HTTP/DNS lỗi).  
P/R = precision/recall so với người dán nhãn — **chưa có**.  
SERP = kết quả máy tìm kiếm; lần chạy ghi search bị chặn (HTTP 202).

---

## 5. Việc nhóm sau

Đúng ý cô; **em không làm** các việc này trong gói rút:

1. **Google Form** (MST, kênh, khoảng % doanh thu) → cô gửi **100–200** DN chế tạo.  
2. **Dán nhãn tay 6 cờ** (có catalog / giỏ / thanh toán / MXH / link sàn / …): tối thiểu **20**, đủ thì **89** → tính P/R.  
3. **Khớp form ↔ web** nếu có MST trùng.  
4. **Ước `DT × %`** chỉ khi đã có doanh thu (không suy từ HTML).  
5. **Báo cáo lab**; GSO / Nhật sâu **nếu nhóm muốn**.

**Không làm / không khả thi như hướng cũ:**

- GMV sàn, cào listing sản phẩm trên sàn  
- Digital VA (giá trị gia tăng số — KPI demo cũ trên web)  
- Dự báo IIP (chỉ số sản xuất công nghiệp)  
- Suy tỷ lệ cả nước khi **không** có khung GSO  

---

## 6. Checklist gặp 15 phút

- [ ] In / gửi **đoạn mục 2** (một trang).  
- [ ] Đưa cô **file này** (`docs/lab/BAN-GIAO.md`) và [`docs/plan.md`](../plan.md).  
- [ ] Chỉ repo GitHub [`thanhhale288/data-economy`](https://github.com/thanhhale288/data-economy): nhánh **`main`** (nền tảng đã giao). Gói tài liệu này đang trên nhánh **`cursor/lab-handoff-withdraw-pack`** (tách từ `cursor/evol1-docs-plan-reorient`) — nếu chưa merge vào `main` thì nói rõ nhánh khi gửi.  
- [ ] Mở **1–2 file JSON** (không lướt dashboard KPI cũ):  
      - `data/processed/extraction_cascade/summary.json` (89/128, tỷ lệ cờ máy trên 89)  
      - `data/processed/url_finder/metrics.json` (12/28, search blocked)  
      - Nếu cô hỏi từng ticker: `data/processed/url_finder/error_analysis.md`  
      - Nếu cô hỏi khung 800: `data/raw/frame_pilot/PROVENANCE.md`  
      - Nếu cô hỏi Nhật: `data/processed/jp_calibration/README.md` rồi `metrics.json`  
      - Nếu không chắc file: mở `README.md` / `PROVENANCE.md` **trong thư mục artifact** tương ứng.  
- [ ] **Không** demo KPI Digital VA / MAPE cũ.

---

## 7. Cách chạy local

Chi tiết đầy đủ: [`README.md`](../../README.md) (mục *Chạy local*). Rút gọn:

```bash
cp .env.example .env
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db redis
make bootstrap          # migrate + seed + pipeline
make api                # http://localhost:8000/docs
make fe                 # terminal khác → http://localhost:5173
```

Hoặc cả stack Docker: `docker compose up --build`.  
Quy tắc agent / cấu trúc repo: [`AGENTS.md`](../../AGENTS.md).

---

## 8. Không làm trong gói này

- Không sprint 7 ngày / “hoàn thiện tháng 12”.  
- Không dán 89 nhãn tay.  
- Không viết báo cáo lab 25 trang.  
- Không giả vờ đề tài đã xong nghiên cứu.  
- Không xóa repo / ẩn số đã chạy.  
- Không xin GSO hộ nhóm sau.
