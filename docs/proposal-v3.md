# Đề xuất v3 — Đo lường mức độ tham gia thương mại điện tử của doanh nghiệp chế biến, chế tạo Việt Nam từ dữ liệu web

**Trạng thái:** dự thảo trình GVHD duyệt · thay thế định hướng đo "Digital VA" của proposal-v2
**Thời hạn:** báo cáo NCKH trước tháng 12/2026 · bản thảo bài báo quốc tế nộp được
**Bối cảnh tổ chức:** thực hiện tại lab (HUST), định hướng phát triển thành đề tài cấp trường

---

## 1. Định vị một dòng

> Xây dựng và kiểm định phương pháp đo **tỷ lệ tham gia thương mại điện tử** của doanh nghiệp
> ngành chế biến, chế tạo (VSIC Section C) từ dữ liệu web — theo chuẩn thống kê thực nghiệm
> OBEC của châu Âu, thích ứng cho bối cảnh **không có điều tra ICT** làm nhãn huấn luyện và
> **sàn TMĐT chiếm ưu thế** — chứng minh tính khả thi của một kênh sản xuất số liệu
> **tần suất cao, chi phí biên gần bằng không** cho chỉ tiêu mà hệ thống hiện tại đo mỗi năm
> một lần hoặc chưa đo.

## 2. Khoảng trống nghiên cứu

- **Quốc tế:** Eurostat (ESSnet Big Data → Web Intelligence Network) và Istat đã sản xuất
  "thống kê thực nghiệm" từ web scraping website doanh nghiệp (OBEC). Thiết kế của họ
  **huấn luyện trên nhãn từ điều tra ICT** — không tái lập được ở nước thiếu điều tra này.
  Báo cáo phương pháp WIN tự thừa nhận khung website-only **đếm thiếu** nơi doanh nghiệp
  bán qua sàn thay vì website riêng, nhưng chưa ai định lượng mức thiếu đó.
- **Việt Nam:** không tìm thấy nghiên cứu OBEC nào. Nguồn hiện có (Sách trắng TMĐT iDEA,
  EBI của VECOM) chỉ công bố mức quốc gia, mẫu phi xác suất, không tách ngành; Sách Trắng
  CNTT-TT của Bộ TT&TT tái sử dụng số liệu VECOM. Điều tra doanh nghiệp GSO (phiếu 2/DN-MAU,
  mục A5.2) **có thu thập** tỷ trọng doanh thu online theo ngành nhưng **chưa thấy công bố**.

Tài liệu neo: ESSnet OBEC Starter Kit (github.com/EnterpriseCharacteristicsESSnetBigData/StarterKit);
Istat experimental statistics 2018 + bài SJIAOS doi:10.3233/sji-190553; báo cáo URL-finding WIN
(cros.ec.europa.eu, 2022); Bank Indonesia, BIS IFC Bulletin 62 (tiền lệ Đông Nam Á gần nhất).

## 3. Câu hỏi nghiên cứu và đóng góp

| # | Câu hỏi | Đóng góp |
|---|---------|----------|
| RQ1 | Dữ liệu web đo được tỷ lệ hiện diện số / tham gia TMĐT của doanh nghiệp Section C với độ chính xác định lượng được không? | Nghiên cứu OBEC đầu tiên cho Việt Nam |
| RQ2 | Khung đo chỉ dựa website đếm thiếu bao nhiêu điểm % so với khung website + hiện diện sàn? | Định lượng lần đầu cái chệch mà WIN thừa nhận, tại thị trường sàn-chiếm-ưu-thế điển hình |
| RQ3 | Kiểm định ước lượng OBEC thế nào khi không có điều tra ICT làm nhãn? | "Chồng kiểm định" (validation stack) dùng được cho mọi nước thiếu điều tra ICT |
| RQ4 (mở rộng) | Ước lượng web so với điều tra doanh nghiệp GSO (A5.2) lệch nhau ra sao — biên mở rộng vs biên thâm dụng? | Chỉ khả thi nếu xin được bảng GSO; nếu về sau tháng 12 → bản mở rộng cho journal |

**Chỉ tiêu đo (chỉ giữ cái quan sát được):** có website hoạt động · có danh mục sản phẩm ·
có chức năng đặt hàng/giỏ hàng · phương thức thanh toán hiển thị · liên kết mạng xã hội ·
liên kết/gian hàng sàn TMĐT (Shopee, TikTok Shop, Lazada) · ngôn ngữ website.
**Đã loại khỏi phạm vi:** Digital VA (tham số tự đặt, không có ground truth), dự báo IIP bằng
đặc trưng số hóa (dữ liệu digital chỉ có một kỳ — phương sai theo thời gian bằng không),
cào listing sàn hàng loạt (bị chặn anti-bot; rủi ro pháp lý Điều 289 BLHS nếu vượt chặn).

## 4. Thiết kế nghiên cứu

### 4.1. Khung chọn mẫu và mẫu

- **Khung chính:** trích xuất đăng bạ doanh nghiệp Section C đang hoạt động (tên, MST,
  VSIC 4 số, địa chỉ, quy mô lao động) — xin qua GVHD từ GSO/Cục Thống kê, song song mua
  "báo cáo tổng hợp danh sách doanh nghiệp" của Cổng ĐKKD (phí 150.000đ/báo cáo,
  Thông tư 47/2019/TT-BTC).
- **Khung dự phòng** (nếu cả hai kênh chậm): danh bạ MST công khai (masothue.com và tương
  đương, lọc theo VSIC) + danh bạ khu công nghiệp — ghi rõ hạn chế độ phủ trong báo cáo.
- **Mẫu:** phân tầng theo VSIC division (2 số) × quy mô lao động; đích **1.500–2.500 DN**
  (p≈0,4 → ±5đpt/tầng chính, ±2đpt toàn mẫu, 95%).
- **Pilot trước, mở rộng sau:** vòng 1 chạy 2–3 division có nhiều doanh nghiệp
  (gợi ý: 10 thực phẩm, 22 nhựa–cao su, 25/27 cơ khí–điện) để khớp pipeline; vòng 2 phủ
  Section C. Nếu tháng 12 mới xong vòng 1 + thiết kế vòng 2 → vẫn đủ cho báo cáo lab
  ("pilot có kết quả + kế hoạch cấp trường").
- **28 DN niêm yết hiện có:** không còn là quần thể nghiên cứu; giữ làm **tập con đối chiếu
  giàu dữ liệu** (có BCTC thật từ CafeF) cho case study mô tả.

### 4.2. Pipeline đo lường

```
Đăng bạ → Tìm URL (search + đối sánh thực thể) → Cào website (httpx/Playwright, chỉ trang công khai)
       → Trích chỉ tiêu (thác 3 tầng) → Dò hiện diện sàn (search + xác minh, KHÔNG cào listing)
       → Ước lượng có trọng số + hiệu chỉnh chệch → Bảng chỉ tiêu ± CI → Dashboard công bố
```

**Tìm URL** theo phương pháp ESSnet: truy vấn máy tìm kiếm "tên + MST + địa chỉ", chấm điểm
ứng viên bằng bằng chứng trên trang (tên/MST/địa chỉ ở footer, trang giới thiệu), LLM ra
quyết định cuối kèm trích dẫn bằng chứng, abstain khi mỏng.

**Trích chỉ tiêu — thác 3 tầng** (báo cáo đường cong chi phí–chất lượng của từng tầng):

1. Luật cứng: regex/DOM — giỏ hàng, logo cổng thanh toán (VNPay/Momo/COD), link sàn. Precision cao, recall thấp, miễn phí.
2. LLM local đọc text đã render → JSON có cấu trúc, mỗi trường kèm confidence + quyền từ chối.
3. Người: chỉ duyệt ca LLM từ chối hoặc tầng 1–2 mâu thuẫn.

**Hiện diện sàn (RQ2):** với từng DN trong mẫu, tìm gian hàng chính thức bằng truy vấn
site-restricted + đối sánh tên bằng LLM + xác minh tay trong gold standard. Chỉ ghi nhận
**có/không + URL gian hàng**, không cào sản phẩm — không đụng anti-bot, không rủi ro pháp lý.

### 4.3. Gold standard

- **Cỡ:** 500 DN phân tầng (400 tối thiểu), phủ đủ division × quy mô.
- **Người gán:** tuyển 2 sinh viên hỗ trợ + tác giả; **sổ tay chú giải** dịch–thích ứng từ
  annotation handbook của ESSnet trước khi gán.
- **Quy trình:** LLM tiền-gán toàn bộ → người duyệt/sửa; **150 DN gán đôi độc lập** để tính
  Cohen's kappa (người–người) và agreement người–LLM.
- **Sản phẩm phụ đăng được:** chi phí giờ-người tiết kiệm nhờ LLM tiền-gán ở cùng mức chất lượng.

### 4.4. Chồng kiểm định (RQ3) — không phụ thuộc nguồn nào đơn lẻ

| Lớp | Nguồn | Kiểm cái gì |
|-----|-------|-------------|
| 1 | Gold standard 500 DN | Precision/recall/F1 từng chỉ tiêu, từng tầng pipeline; so mốc châu Âu ~83–88% |
| 2 | Danh bạ website TMĐT đã thông báo/đăng ký của iDEA | Ground truth bán phần cho "có chức năng đặt hàng"; đo luôn **khoảng trống tuân thủ** (DN có đặt hàng nhưng chưa thông báo) |
| 3 | Mức quốc gia iDEA (44% có website; 42% trong đó có đặt hàng; 23% bán sàn) + chuỗi EBI/VECOM | Neo hợp lý (plausibility) — không phải kiểm định thống kê chặt |
| 4 (nếu có) | Bảng A5.2 điều tra DN GSO | Đối chiếu mạnh nhất: biên mở rộng (web) vs biên thâm dụng (điều tra) theo division × quy mô |

### 4.5. Ước lượng

Trọng số thiết kế theo tầng; phân tích chệch không-tìm-được-URL (thiên về DN nhỏ/cũ) —
mô hình hóa xác suất tìm được URL theo đặc điểm DN, hiệu chỉnh kiểu model-assisted
(tinh thần combined estimator của Istat). Báo cáo khoảng tin cậy mọi ước lượng;
tuyệt đối không công bố điểm ước lượng trần.

## 5. AI stack — AI là thiết bị đo, mỗi mảnh có sai số công bố

| Thành phần | Công nghệ | Baseline so sánh | Số đo | Vai trò trong bài |
|---|---|---|---|---|
| Đối sánh URL–DN | LLM đọc bằng chứng cấu trúc | Fuzzy matching (kế thừa shop matcher) | P/R trên gold standard | Phương pháp, mục 4.2 |
| Trích chỉ tiêu website | Thác luật→LLM→người | Từng tầng so với nhau | Đường cong chi phí–chất lượng | Kết quả chính RQ1 |
| Đối sánh gian hàng sàn | LLM + xác minh tay | Fuzzy | P/R | RQ2 |
| Phân loại VSIC từ web | LLM phân cấp 2→4 số | Mã trong đăng bạ | Agreement + phân tích lệch | Chất lượng khung mẫu |
| Tiền-gán nhãn (active learning) | LLM local + human review | Gán tay thuần | Kappa, giờ-người tiết kiệm | Đóng góp phương pháp phụ |
| Selective prediction | Confidence + abstain kèm lý do (nâng từ pattern có sẵn trong code) | Không abstain | Hiệu chuẩn (calibration) | Xuyên suốt |
| (Tùy chọn) VLM nhìn screenshot | Vision model dò nút đặt hàng trong ảnh | Text-only | Δrecall | Điểm nhấn mới nếu kịp — ngoài đường găng |

**Quy tắc tái lập (bắt buộc cho bài báo):** model open-weights chạy trên GPU lab
(cỡ Qwen-Instruct 7–32B là đủ cho phân loại có cấu trúc), **ghim phiên bản**, temperature 0,
toàn bộ prompt vào phụ lục, chạy lặp đo độ ổn định đầu ra. Không dùng API đóng cho các con
số vào bài; API chỉ dùng cho việc phụ trợ ngoài báo cáo.

**Không làm:** chatbot, fine-tune LLM không lý do, deep learning trên chuỗi 112 điểm,
narrative sinh văn trong báo cáo.

## 6. Dữ liệu: xin gì, giá trị gì, dự phòng gì

| Ưu tiên | Nguồn | Xin qua | Giá trị chính | Dự phòng nếu không có |
|---|---|---|---|---|
| 1 | Trích xuất đăng bạ Section C | GVHD → GSO/Cục Thống kê; song song mua Cổng ĐKKD (TT 47/2019) | Khung mẫu → suy diễn quốc gia; phân tích chất lượng đăng bạ | Danh bạ MST công khai + KCN (ghi hạn chế độ phủ) |
| 2 | Bảng A5.2 phiếu 2/DN-MAU (2022–2024, VSIC 2 số × quy mô) | GVHD → GSO, công văn | Mốc kiểm định mạnh nhất; tự thân là số liệu chưa công bố; RQ4 biên mở rộng vs thâm dụng | Chồng kiểm định vẫn đứng bằng lớp 1–3 |
| 3 | Xuất danh bạ website TMĐT đã thông báo | Công văn → Cục TMĐT & KTS (iDEA); có tra cứu công khai | Ground truth bán phần + đo khoảng trống tuân thủ | Tra cứu thủ công trên cổng công khai cho riêng mẫu |
| 4 | Xác nhận miễn trừ NCKH, Luật BVDLCN 91/2025 (hiệu lực 01/01/2026) | GVHD/khoa luật | Mục đạo đức nghiên cứu | Thiết kế đã tự vệ: chỉ trang công khai, bỏ/băm định danh cá nhân khi thu thập |

Dữ liệu đã có: GSO macro live (829 dòng — chương bối cảnh), CafeF BCTC 28/28 mã
(case study đối chiếu), bộ dò website chạy live (phôi của tầng 1 pipeline).

## 7. Tận dụng hệ thống hiện có

| Giữ nguyên | Đổi vai | Cắt |
|---|---|---|
| Crawler GSO/OECD (chương bối cảnh) | Bộ dò website → tầng 1 của thác trích chỉ tiêu | KPI Digital VA + heatmap VA khỏi UI |
| CafeF BCTC + benchmark form/OCR | Shop matcher → đối sánh URL–DN và gian hàng–DN | Bảng MAPE 4 model (rò rỉ nhãn, thua naive — đã kiểm chứng 21/8) |
| Kiến trúc provenance/abstain (→ mục "khung chất lượng" của bài) | Product categorizer → phân loại VSIC từ nội dung web | Pipeline cào listing sàn (đóng băng, giữ code + ADR làm phụ lục bài học) |
| PostgreSQL + FastAPI + frontend | Dashboard → trang công bố chỉ tiêu mới ± CI (demo chạy thật khi nghiệm thu) | Forecast IIP khỏi phạm vi khoa học (gỡ hoặc gắn nhãn demo) |

## 8. Roadmap 14 tuần (25/8 → 01/12)

Người thực hiện: **B** = bạn · **AG** = AI agent · **SV** = 2 sinh viên hỗ trợ · **GV** = GVHD

| Tuần | Việc | Ai | Mốc chốt |
|---|---|---|---|
| 1 (25–31/8) | Gặp GVHD: duyệt proposal này, **làm rõ thể thức nghiệm thu tháng 12 với lab**, ký 2 công văn (Phụ lục A, B); mua báo cáo Cổng ĐKKD; dựng LLM local trên GPU lab | B+GV, AG hỗ trợ | Công văn đã gửi |
| 2 | Sổ tay chú giải (dịch–thích ứng ESSnet); gỡ KPI sai khỏi web; chốt danh mục chỉ tiêu + schema | AG+B | Handbook v1 |
| 3–4 | Khung mẫu (chính hoặc dự phòng) + rút mẫu phân tầng; pipeline tìm URL; tuyển & tập huấn 2 SV | B+AG, SV | Mẫu đã rút; URL pipeline chạy |
| 4–5 | Cào vòng pilot (2–3 division); khớp danh bạ iDEA | AG | ≥80% mẫu pilot xử lý xong URL |
| 5–7 | Thác trích chỉ tiêu tầng 1+2; LLM tiền-gán; SV gán gold standard (150 gán đôi) | AG+SV | Gold standard xong, có kappa |
| 7–8 | Dò hiện diện sàn cho mẫu; tính P/R từng tầng; sửa pipeline theo lỗi tìm thấy | AG+B | Bảng chất lượng thiết bị đo |
| 8–9 | Mở rộng cào toàn mẫu Section C (nếu khung chính đã về; nếu chưa → chốt phạm vi pilot) | AG | Dữ liệu đủ chạy ước lượng |
| 9–10 | Ước lượng + trọng số + hiệu chỉnh chệch; RQ2 (mức đếm thiếu); khoảng trống tuân thủ iDEA | B+AG | Bảng kết quả chính ± CI |
| 10–12 | Viết báo cáo NCKH (VN) + bản thảo tiếng Anh (đích: SJIAOS); dashboard thành trang công bố chỉ tiêu | B viết, AG nháp/red-team | Nháp đủ gửi GV |
| 12–13 | GV phản biện; sửa; red-team bằng AI (giả lập hội đồng) | B+GV+AG | Bản gần cuối |
| 14 (24/11–01/12) | Hoàn thiện, nộp; đóng gói dataset + codebook + code tái lập | B | **Nộp** |

**Đường găng:** công văn tuần 1 (trễ nhất) → khung mẫu tuần 3–4 → gold standard tuần 5–7.
Mọi thứ khác trượt được, ba mắt xích này thì không.

## 9. Rủi ro và phương án

| Rủi ro | Xác suất | Phương án |
|---|---|---|
| GSO không trả lời kịp | Cao | Khung dự phòng (mục 4.1) + chồng kiểm định lớp 1–3; A5.2 dời sang bản journal |
| Tìm URL kém với DN nhỏ | Chắc chắn một phần | Chính là phân tích chệch của bài — đo và mô hình hóa, không giấu |
| Search engine chặn truy vấn hàng loạt | Vừa | API tìm kiếm trả phí liều lượng nhỏ + giãn nhịp + cache; ghi vào phần chi phí |
| SV gán nhãn không đều tay | Vừa | Handbook + buổi hiệu chuẩn chung + kappa trên tập gán đôi, bất đồng thì phân xử |
| Thể thức nghiệm thu khác dự kiến | Vừa | Làm rõ với lab ngay tuần 1 (đã đưa vào roadmap) |
| Luật 91/2025 diễn giải chặt hơn | Thấp | Chỉ trang công khai; bỏ/băm định danh cá nhân khi thu thập; hỏi GVHD tuần 1 |

## 10. Sản phẩm đầu ra tháng 12

1. **Báo cáo NCKH** (tiếng Việt) — pilot có kết quả thật + thiết kế mở rộng cấp trường.
2. **Bản thảo tiếng Anh** nộp được (đích: Statistical Journal of the IAOS hoặc hội nghị thống kê chính thức khu vực; vòng phản biện chạy sang 2027 là bình thường).
3. **Bộ dữ liệu + codebook** có phiên bản: chỉ tiêu theo DN (ẩn danh hóa), bảng ước lượng ± CI.
4. **Web demo chạy thật:** trang công bố chỉ tiêu, phương pháp, chất lượng nguồn — tái sử dụng hạ tầng hiện có.
5. **Pipeline tái lập:** code + prompt + model version ghim + hướng dẫn chạy lại.

---

## Phụ lục A — Dự thảo công văn gửi GSO / Cục Thống kê (GVHD đứng tên, in trên giấy tiêu đề đơn vị)

> **V/v: Đề nghị hỗ trợ dữ liệu phục vụ đề tài nghiên cứu khoa học về đo lường kinh tế số ngành chế biến, chế tạo**
>
> Kính gửi: [Cục Thống kê / đơn vị đầu mối theo quan hệ của GVHD]
>
> [Tên lab, Trường], đang thực hiện đề tài "[tên đề tài]" nhằm xây dựng phương pháp đo lường
> mức độ tham gia thương mại điện tử của doanh nghiệp ngành chế biến, chế tạo (VSIC ngành C)
> từ dữ liệu web, đối chiếu kiểm định với số liệu thống kê chính thức.
>
> Để bảo đảm tính đại diện và độ tin cậy khoa học, kính đề nghị Quý cơ quan hỗ trợ:
>
> **1. Danh sách doanh nghiệp ngành chế biến, chế tạo đang hoạt động** (trích xuất từ cơ sở
> dữ liệu đăng ký/đăng bạ doanh nghiệp), gồm các trường: tên doanh nghiệp, mã số thuế,
> mã ngành VSIC cấp 4, địa chỉ trụ sở, quy mô lao động (theo nhóm). Mục đích: khung chọn mẫu
> phân tầng.
>
> **2. Bảng số liệu tổng hợp từ Điều tra doanh nghiệp** (phiếu 2/DN-MAU, mục A5.2) về tỷ trọng
> doanh thu bán hàng trực tuyến, tổng hợp cho ngành C theo phân ngành cấp 2 và quy mô doanh
> nghiệp, các năm 2022–2024 (theo khả năng sẵn có). Mục đích: đối chiếu kiểm định ước lượng
> từ dữ liệu web — không đề nghị dữ liệu vi mô định danh.
>
> Nhóm nghiên cứu cam kết: sử dụng dữ liệu đúng mục đích nghiên cứu; không công bố thông tin
> định danh doanh nghiệp; trích dẫn nguồn đầy đủ; gửi Quý cơ quan báo cáo kết quả nghiên cứu
> khi hoàn thành.
>
> Đầu mối liên hệ: [GVHD, chức danh, điện thoại, email]

## Phụ lục B — Dự thảo công văn gửi Cục TMĐT và Kinh tế số (iDEA), Bộ Công Thương

> **V/v: Đề nghị hỗ trợ danh sách website/ứng dụng TMĐT đã thông báo, đăng ký phục vụ nghiên cứu khoa học**
>
> Kính gửi: Cục Thương mại điện tử và Kinh tế số, Bộ Công Thương
>
> [Tên lab, Trường] đang thực hiện đề tài nghiên cứu về đo lường mức độ tham gia thương mại
> điện tử của doanh nghiệp ngành chế biến, chế tạo từ dữ liệu web.
>
> Được biết Quý Cục vận hành hệ thống quản lý hoạt động TMĐT với công cụ tra cứu công khai
> các website/ứng dụng đã thông báo, đã đăng ký. Để phục vụ việc kiểm định độ chính xác của
> phương pháp đo, kính đề nghị Quý Cục hỗ trợ **bản trích xuất danh sách website/ứng dụng TMĐT
> bán hàng đã thông báo** (trường: tên đơn vị sở hữu, mã số thuế nếu có, địa chỉ website,
> ngày thông báo), ưu tiên các đơn vị thuộc lĩnh vực sản xuất nếu phân loại được.
>
> Nhóm nghiên cứu cam kết sử dụng đúng mục đích nghiên cứu, trích dẫn nguồn, và gửi Quý Cục
> kết quả nghiên cứu — trong đó có ước lượng độc lập về mức độ tuân thủ nghĩa vụ thông báo
> website TMĐT trong ngành chế biến, chế tạo, có thể hữu ích cho công tác quản lý của Quý Cục.
>
> Đầu mối liên hệ: [GVHD, chức danh, điện thoại, email]

---

*Ghi chú phiên bản: v3 thay thế trọng tâm "Digital VA / VDEI / dự báo IIP" của proposal-v2
sau audit 20–21/8/2026 (rò rỉ nhãn trong feature dự báo, 4/4 model thua naive baseline,
chỉ số Digital VA dựa trên 13 dòng listing và 3 hằng số tự đặt). Các công thức trong
CONTEXT.md thuộc phạm vi cũ sẽ cập nhật bằng ADR riêng khi bắt đầu triển khai.*
