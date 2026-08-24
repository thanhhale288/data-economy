# Evol-1 — Kế hoạch theo từng task, ưu tiên việc KHÔNG cần chờ dữ liệu

**Mục tiêu đợt này:** đến buổi gặp GVHD tuần sau, có **kết quả chạy thật + con số đo được**
để chứng minh dự án đang tiến, không phải chỉ có kế hoạch. Thiết kế tổng thể xem
`docs/proposal-v4.md` (v3 giữ lại làm lịch sử) — file này là bản chẻ nhỏ thành task thực thi,
làm tuần tự, mỗi task 1 branch 1 PR theo quy ước repo.

**Logic ưu tiên:** mọi task Nhóm A đều chạy được bằng dữ liệu công khai + 28 DN đã có
trong DB. Không có task nào chờ GSO, chờ công văn, hay chờ tuyển sinh viên.

---

## NHÓM A — Làm ngay tuần này (22/8 → trước buổi gặp GVHD)

### T01 — Gỡ số liệu không bảo vệ được khỏi web demo
- **Vì sao trước tiên:** nếu GVHD (hoặc ai đó ở lab) mở web và thấy "XGBoost MAPE 6.8%"
  hay "Tổng Digital VA", mọi thứ trình bày sau đó mất uy tín. Audit 20–21/8 đã chứng minh
  các số này sai (rò rỉ nhãn, thua naive baseline, 13 dòng listing + hằng số tự đặt).
- **Việc làm:** ẩn bảng MAPE model ở Dashboard + ML Lab (hoặc gắn nhãn "demo kỹ thuật —
  không phải kết quả nghiên cứu"); gỡ KPI "Tổng Digital VA" + heatmap VA + card "Cơ cấu
  Digital VA"; giữ IIP/VA_C macro (dữ liệu GSO thật) và trang Companies/Benchmark.
- **DoD:** web chạy, không còn con số nào không bảo vệ được trước một người phản biện.
- **Effort:** 0.5 ngày (agent làm, bạn duyệt). Branch: `cursor/evol1-task01-remove-invalid-kpis`.
- **Cho GVHD xem:** web demo sạch + 1 đoạn giải thích "em đã audit và chủ động gỡ số sai".

### T02 — Khung mẫu pilot từ nguồn công khai (không cần GSO)
- **Vì sao:** chứng minh thiết kế không bị "treo" chờ công văn; đây là khung dự phòng
  trong proposal-v4 mục 4.4, làm luôn thành khung pilot.
- **Việc làm:** thu thập danh sách DN sản xuất từ danh bạ MST công khai (masothue.com
  hoặc tương đương, lọc theo VSIC) cho 2–3 division pilot (gợi ý: 10 thực phẩm,
  22 nhựa–cao su, 25 cơ khí); trường: tên, MST, VSIC 4 số, địa chỉ, năm thành lập nếu có.
  Đích ≥800 DN. Lưu vào `data/raw/frame_pilot/` kèm PROVENANCE.md (nguồn, ngày, giới hạn).
- **DoD:** CSV khung pilot + bảng thống kê phân bố division × địa phương + ghi chú độ phủ.
- **Effort:** 1–1.5 ngày (agent). Branch: `cursor/evol1-task02-pilot-frame`.
- **Cho GVHD xem:** "em đã có khung mẫu pilot n=XXX doanh nghiệp, phân bố như sau".

### T03 — URL-finder v0, chấm điểm ngay trên 28 DN đã biết website
- **Vì sao:** 28 DN trong DB có sẵn website đã xác minh = **ground truth miễn phí**.
  Đây là con số khoa học đầu tiên của đề tài, có được mà không cần bất kỳ ai cho dữ liệu.
- **Việc làm:** pipeline truy vấn tìm kiếm "tên + MST/địa chỉ" → chấm ứng viên bằng
  bằng chứng trên trang (tên/MST ở footer, trang giới thiệu) → LLM quyết định kèm abstain.
  Chạy blind trên 28 DN (che website đã biết), so kết quả với ground truth.
- **DoD:** bảng accuracy/precision/recall trên 28 DN + phân tích ca sai.
- **Effort:** 1–2 ngày (agent + bạn duyệt ca sai). Branch: `cursor/evol1-task03-url-finder-v0`.
- **Cho GVHD xem:** "URL-finder của em đạt X/28, các nước châu Âu công bố 83–88% — em đang ở đâu và vì sao".

### T04 — Dựng LLM local trên GPU lab
- **Việc làm:** chọn model open-weights cỡ 7–32B instruct, ghim phiên bản, script inference
  batch (temperature 0, JSON schema output, retry/abstain), đo tốc độ trang/giờ trên GPU lab.
- **DoD:** phân loại thử 10 trang web ra JSON đúng schema, có log phiên bản model + tham số.
- **Effort:** 0.5–1 ngày. Branch: `cursor/evol1-task04-local-llm-setup`.
- **Cho GVHD xem:** "hạ tầng AI tái lập được: model X phiên bản Y chạy trên GPU lab, Z trang/giờ, chi phí ~0".

### T05 — Thác trích chỉ tiêu v0 (tầng 1 luật + tầng 2 LLM)
- **Việc làm:** mở rộng bộ dò website hiện có (đang chạy live) thành tầng 1: giỏ hàng,
  logo thanh toán (VNPay/Momo/COD), link Shopee/TikTok/Lazada, link MXH. Tầng 2: LLM (T04)
  đọc text đã render, trả các trường chỉ tiêu + confidence + abstain. Chạy trên 28 site
  quen + ~100 site tìm được từ khung T02.
- **DoD:** bảng chỉ tiêu thô cho ~128 DN + bảng so khớp/mâu thuẫn tầng 1 vs tầng 2.
- **Effort:** 2 ngày (agent). Branch: `cursor/evol1-task05-extraction-cascade-v0`.
- **Cho GVHD xem:** bảng "X% DN pilot có website, Y% có chức năng đặt hàng, Z% link sàn" —
  kèm chú thích rõ *chưa suy rộng, chưa có trọng số* — và ca mâu thuẫn thú vị giữa luật và LLM.

### T06 — Sổ tay gán nhãn v1 + mini gold standard 50 DN
- **Việc làm:** dịch–thích ứng annotation handbook của ESSnet OBEC sang tiếng Việt
  (định nghĩa từng chỉ tiêu, ca biên, quy tắc quyết định); tự gán tay 50 DN từ tập T05;
  tính precision/recall của tầng 1, tầng 2 so với nhãn tay.
- **DoD:** `docs/annotation-handbook-v1.md` + bảng P/R đầu tiên của pipeline.
- **Effort:** 1 ngày (agent nháp handbook + tiền-gán, bạn duyệt 50 ca ~2–3 giờ).
  Branch: `cursor/evol1-task06-handbook-mini-gold`.
- **Cho GVHD xem:** con số P/R đầu tiên — bằng chứng em làm khoa học đo lường, không phải demo chay.

### T07 — Gói trình bày cho buổi gặp GVHD
- **Việc làm:** one-pager + 5–7 slide theo kịch bản ở cuối file; in sẵn `proposal-v4.md`
  và 2 dự thảo công văn (Phụ lục A–B của proposal-v3, giữ nguyên nội dung) chỉ chờ điền tên + ký.
- **DoD:** bộ tài liệu in được, kể được trong 15 phút.
- **Effort:** 0.5 ngày (agent nháp, bạn sửa giọng). Branch: `cursor/evol1-task07-advisor-brief`.

### T08 — Pilot hiệu chuẩn Nhật: chấm URL-finder trên nhãn quy mô lớn
- **Vì sao:** T03 chấm bộ dò URL trên 28 ca — đủ để có con số đầu tiên, không đủ để nói gì
  về độ chính xác theo phân tầng. Nhật có **nhãn website ở quy mô hàng nghìn, tải công khai**:
  đăng bạ pháp nhân đầy đủ từ 国税庁法人番号公表サイト (CSV/XML, miễn phí, không cần token) khớp
  với gBizINFO của METI (5tr+ pháp nhân, API v2 + tải hàng loạt, có mã ngành JSIC, số lao động,
  vốn, và **trường URL website**). Đây là hiện trường hiệu chuẩn của proposal-v4 mục 4.1.
- **Việc làm:**
  1. Tải khung 国税庁 (lọc vài tỉnh cho gọn) + đăng ký token gBizINFO, khớp theo mã pháp nhân.
  2. Lọc ngành chế tạo theo JSIC (kỳ vọng Division E — **xác nhận lại cấp division**), rút
     **300 DN** phân tầng theo quy mô lao động.
  3. **Tách trường URL ra `data/raw/jp_labels/` ngay khi tải.** Bảng khung mà pipeline đọc chỉ
     gồm tên pháp nhân, địa chỉ, mã ngành. Ghi hash bảng đầu vào để chứng minh không rò rỉ
     (proposal-v4 mục 4.3) — đây đúng là loại lỗi audit 20–21/8 đã bắt được một lần.
  4. Chạy URL-finder của T03 nguyên trạng, chỉ đổi cấu hình ngôn ngữ. **Không sửa logic**; nếu
     buộc phải sửa thì ghi lại sửa gì — đó là dữ liệu cho RQ3 về tính chuyển giao.
  5. Mở nhãn, tính P/R/abstain-rate theo phân tầng. Xác minh tay ~30 ca lệch để biết bao nhiêu
     phần là lỗi pipeline và bao nhiêu phần là **nhãn gBizINFO sai/cũ** (nhãn bạc, không phải vàng).
- **DoD:** bảng P/R trên n≈300 theo phân tầng + tỷ lệ nhãn bạc tự sai + so sánh cạnh nhau với
  con số T03 trên 28 DN Việt Nam + PROVENANCE.md cho cả hai nguồn Nhật.
- **Effort:** 1–1.5 ngày (agent; bạn duyệt ~30 ca lệch, khoảng 1 giờ).
  Branch: `cursor/evol1-task08-jp-calibration-pilot`.
- **Cho GVHD xem:** "cùng một pipeline, ở Việt Nam em chấm được trên 28 ca, ở Nhật em chấm được
  trên 300 ca có nhãn chính phủ — và đây là chênh lệch giữa hai nước." Đây cũng là con số duy
  nhất trong bộ tài liệu **chạy trên dữ liệu Nhật**, tức thứ đính được vào thư gửi giáo sư Nhật.
- **Giới hạn tự đặt:** đúng một tuần công sức. Nếu phình ra, cắt còn bảng P/R và dừng
  (proposal-v4 mục 8, "chốt cứng về phạm vi").

**Bộ tối thiểu phải xong trước buổi gặp:** T01, T02, T03, T07.
**Cố thêm nếu kịp:** T04, T05, T08; T06 có thể thu nhỏ còn 20 DN vẫn có giá trị.
**Lưu ý về T08:** giá trị của nó phụ thuộc T03 đã chạy (dùng lại đúng pipeline đó). Nếu T03
chưa xong thì T08 chưa có gì để chấm — đừng đảo thứ tự.

---

## NHÓM B — Ngay sau buổi gặp (cần chữ ký / quyết định của GVHD)

Đánh số dồn một bậc so với bản trước vì T08 đã chuyển thành task Nhóm A.

| Task | Việc | Phụ thuộc |
|---|---|---|
| T09 | Hoàn thiện + gửi 2 công văn (GSO, iDEA); mua báo cáo tổng hợp Cổng ĐKKD (150k) | GVHD ký |
| T10 | Tuyển 2 SV hỗ trợ, tập huấn bằng handbook T06, buổi hiệu chuẩn chung | GVHD giới thiệu nguồn SV |
| T11 | Làm rõ thể thức nghiệm thu tháng 12 với lab → chỉnh đích sản phẩm nếu cần | Buổi gặp |
| T12 | Mở rộng khung mẫu VN (ưu tiên khung chính thức nếu dữ liệu về) + rút mẫu phân tầng đầy đủ | T09 hoặc dùng khung T02 mở rộng |
| T13 | Gold standard 500 DN Việt Nam, trong đó 150 gán đôi độc lập → Cohen's kappa | T10, T12 |
| T14 | Dò hiện diện sàn cho toàn mẫu (search + xác minh, không cào listing) | T12 |
| T15 | Khớp danh bạ iDEA (bulk nếu công văn về, tra cứu cổng công khai nếu chưa) | T09/T05 |
| T16 | Gold standard Nhật ~100 DN xác minh tay → **đo sai số của chính nhãn bạc gBizINFO**, hiệu chỉnh lại mọi con số của T08 | T08 |
| T17 | Chạy thác trích chỉ tiêu (T05) trên ~300 site Nhật, chỉ đổi cấu hình không đổi logic → **Δ P/R giữa hai nước, tách theo tầng = RQ3**; kèm bảng ánh xạ VSIC↔JSIC cấp division | T05, T08, T16 |
| T18 | **Phép đo RQ1:** tính sai số thiết bị đo ở Nhật bằng lớp kiểm định không nhãn (`ê_không_nhãn`) vs bằng nhãn thật (`e_thật`), báo cáo hiệu số theo phân tầng | T16, T17 |
| T19 | Ước lượng có trọng số + phân tích chệch URL-finding + khoảng tin cậy (Việt Nam) | T13, T14 |
| T20 | Viết báo cáo NCKH + bản thảo tiếng Anh; dashboard thành trang công bố chỉ tiêu, có tab so sánh VN–JP | T18, T19 |
| T21 | Viết Phụ lục C của proposal-v4 thành 研究計画書 hoàn chỉnh, dẫn bằng số thật của T08/T16/T18 | T18 |

**Nhánh Nhật (T08, T16, T17, T18) có ngân sách cứng: tối đa 2,5 ngày công cộng lại.** Nếu vượt,
giữ T08 và bỏ phần còn lại sang Giai đoạn 2 — báo cáo tháng 12 và thư giới thiệu quan trọng hơn.

Chi tiết lịch tuần và rủi ro: xem roadmap mục 8–9 của `proposal-v4.md`.

---

## Kịch bản 15 phút với GVHD (chống bị mắng bằng kết quả)

1. **Mở đầu bằng cái đã làm, không phải lời xin lỗi** (4'): audit toàn hệ thống ngày 20–21/8
   phát hiện tầng dự báo rò rỉ nhãn và thua naive baseline, chỉ số Digital VA đứng trên
   13 dòng dữ liệu — *em chủ động gỡ và tái định vị đề tài* theo chuẩn quốc tế
   (Eurostat OBEC / Istat experimental statistics). Đưa proposal-v4.
2. **Kết quả chạy thật** (5'): khung mẫu pilot n=XXX từ nguồn công khai; URL-finder đạt X/28
   trên tập kiểm chứng; bảng chỉ tiêu thô cho ~128 DN; (nếu kịp) P/R đầu tiên trên mini
   gold standard. Nhấn: *tất cả làm không cần chờ dữ liệu xin*.
3. **Đề xuất mới của v4 so với v3** (3'): thêm hiện trường hiệu chuẩn Nhật Bản, vì Nhật có đăng
   bạ pháp nhân mở và trường website trong dữ liệu chính phủ — nghĩa là **chấm được thiết bị đo
   trên hàng trăm ca có nhãn thay vì 28 ca**, và đo được *chồng kiểm định không nhãn của mình
   sai bao nhiêu*. (Nếu T08 đã chạy: đưa luôn bảng P/R trên n≈300 DN Nhật.) Nhấn hai điểm:
   dữ liệu tải công khai nên **không phát sinh xin phép**, và ngân sách nhánh này là *một tuần*,
   không lấn phần Việt Nam.
4. **Ba đề nghị cụ thể** (3'): (a) thầy/cô ký 2 công văn đã soạn sẵn — GSO (khung mẫu + bảng
   A5.2) và iDEA (danh bạ website TMĐT); (b) làm rõ thể thức nghiệm thu tháng 12 của lab để em
   chỉnh đích sản phẩm; (c) **xin ý kiến về nhánh Nhật**: đề tài cấp trường có nên có nhánh so
   sánh quốc tế, hay nên giữ thân bài thuần Việt Nam và để nhánh Nhật ở phần hướng phát triển.
   Hỏi thêm: lab có SV nào tham gia gán nhãn được không.

**Về câu (c):** đây là câu hỏi thật, không phải câu hỏi lễ phép — nhánh so sánh quốc tế có thể
nâng tầm đề tài, cũng có thể làm loãng hồ sơ xin kinh phí trong nước. Nếu GVHD nghiêng về giữ
thuần Việt Nam thì phương án đã có sẵn trong proposal-v4 mục 9: giữ toàn bộ nhánh Nhật trong
Phụ lục C như đề cương cá nhân, thân bài về đúng v3. Đừng bảo vệ nhánh Nhật quá mức trong buổi
gặp; giá trị của nó với hồ sơ học bổng không phụ thuộc việc nó có nằm trong đề tài cấp trường.

Nguyên tắc: mọi câu khẳng định trong buổi gặp đều phải có con số hoặc file đứng sau.
Điểm yếu (delay, phải bỏ hướng cũ) chủ động nói trước, kèm bằng chứng vì sao bỏ là đúng.
