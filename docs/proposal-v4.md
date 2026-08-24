# Đề xuất v4 — Thiết bị đo tham gia thương mại điện tử từ dữ liệu web: hiệu chuẩn ở Nhật Bản, triển khai ở Việt Nam

**Trạng thái:** dự thảo trình GVHD duyệt · mở rộng proposal-v3 bằng hiện trường hiệu chuẩn thứ hai
**Thời hạn:** báo cáo NCKH trước tháng 12/2026 · bản thảo bài báo quốc tế nộp được
**Bối cảnh tổ chức:** thực hiện tại lab (HUST), định hướng phát triển thành đề tài cấp trường
**Khác gì v3:** v3 hỏi "dữ liệu web đo được không". v4 coi câu đó là tiền đề đã có tiền lệ châu Âu,
và hỏi câu khó hơn: **thiếu nhãn chuẩn thì thiết bị đo mất bao nhiêu độ chính xác, và đo được cái mất đó không.**

---

## 1. Định vị một dòng

> Xây dựng thiết bị đo **tỷ lệ tham gia thương mại điện tử** của doanh nghiệp ngành chế biến,
> chế tạo từ dữ liệu web; **hiệu chuẩn thiết bị ở nơi có nhãn chuẩn quy mô lớn** (dữ liệu mở
> doanh nghiệp Nhật Bản), **triển khai ở nơi không có** (Việt Nam), và **định lượng phần độ
> chính xác bị mất khi không còn nhãn** — cho ra một quy trình dùng được ở mọi nước thiếu
> điều tra ICT, thay vì một kết quả dùng được ở một nước.

Ba hệ quả của cách định vị này:

1. **Không còn dựa vào lập luận "lần đầu tiên áp dụng cho Việt Nam".** Cái mới là *đo được cái giá của việc thiếu nhãn*, không phải *địa lý của mẫu*.
2. **Dự án không còn treo vào một chữ ký.** Khung chọn mẫu Nhật tải công khai được ngay; nếu công văn Việt Nam về chậm, phần phương pháp vẫn chạy.
3. **Bộ dò URL được chấm ở quy mô hàng nghìn thay vì 28 ca**, vì phía Nhật có trường website trong dữ liệu mở của chính phủ.

## 2. Khoảng trống nghiên cứu

- **Châu Âu — gốc gác phương pháp, giữ nguyên trong bài.** Eurostat (ESSnet Big Data → Web
  Intelligence Network) và Istat đã sản xuất "thống kê thực nghiệm" từ cào website doanh
  nghiệp (OBEC). Thiết kế của họ **huấn luyện và kiểm định trên nhãn từ điều tra ICT** —
  điều kiện không tái lập được ở nước thiếu điều tra này. Báo cáo phương pháp WIN tự thừa
  nhận khung website-only **đếm thiếu** nơi doanh nghiệp bán qua sàn thay vì website riêng,
  nhưng chưa ai định lượng mức thiếu đó.
- **Chỗ chưa ai làm:** chưa có nghiên cứu nào **đo bằng thực nghiệm** chồng kiểm định không
  nhãn sai lệch bao nhiêu so với kiểm định có nhãn. Lý do đơn giản: muốn đo thì phải có một
  nước vừa có nhãn (để biết sự thật) vừa cho phép giả lập trạng thái không nhãn (để biết mình
  đoán sai bao nhiêu). Nhật Bản là hiện trường đó.
- **Nhật Bản — vừa là hiện trường hiệu chuẩn, vừa là bài toán chính sách sống.** Báo cáo
  *DX動向2025* của IPA so sánh Nhật – Mỹ – Đức và kết luận doanh nghiệp nhỏ và vừa Nhật tụt
  lại rõ rệt: hơn một nửa nói **không thấy rõ lợi ích của DX**, khoảng một nửa **thiếu người
  và kiến thức**; tỷ lệ SME đã hoặc sắp dùng AI sinh tạo chỉ khoảng hai mươi mấy phần trăm so
  với hơn 80% ở doanh nghiệp Mỹ và Đức. METI dự báo thiếu tới **790.000 nhân lực IT vào 2030**
  và đang chi tiền qua các chương trình như IT導入補助金 (hỗ trợ tới 4,5 triệu yên mỗi SME).
  Nghĩa là Nhật đang trợ cấp số hoá SME trong khi công cụ đo mức số hoá SME thì thưa và chậm.
- **Việt Nam — hiện trường triển khai.** Không tìm thấy nghiên cứu OBEC nào. Nguồn hiện có
  (Sách trắng TMĐT iDEA, EBI của VECOM) chỉ công bố mức quốc gia, mẫu phi xác suất, không
  tách ngành. Điều tra doanh nghiệp GSO (phiếu 2/DN-MAU, mục A5.2) **có thu thập** tỷ trọng
  doanh thu online theo ngành nhưng **chưa thấy công bố**.

Tài liệu neo: ESSnet OBEC Starter Kit (github.com/EnterpriseCharacteristicsESSnetBigData/StarterKit);
Istat experimental statistics 2018 + bài SJIAOS doi:10.3233/sji-190553; báo cáo URL-finding WIN
(cros.ec.europa.eu, 2022); IPA『DX動向2025』; METI DX Report (2025年の崖);
Bank Indonesia, BIS IFC Bulletin 62 (tiền lệ Đông Nam Á gần nhất).

## 3. Câu hỏi nghiên cứu và đóng góp

**Tiền đề (không còn là câu hỏi):** dữ liệu web đo được hiện diện số của doanh nghiệp — châu Âu
đã chứng minh, ta không chứng minh lại, ta đứng lên đó.

| # | Câu hỏi | Đóng góp | Trong đường găng? |
|---|---------|----------|---|
| **RQ1** | Chồng kiểm định **không nhãn** ước lượng sai số của thiết bị đo lệch bao nhiêu so với kiểm định **có nhãn chuẩn**? | Đo được *cái giá của việc thiếu điều tra ICT* — con số này dùng được cho mọi nước cùng hoàn cảnh | Có |
| **RQ2** | Khung đo chỉ dựa website đếm thiếu bao nhiêu điểm % so với khung website + hiện diện sàn? | Định lượng lần đầu cái chệch mà WIN thừa nhận, tại thị trường sàn-chiếm-ưu-thế điển hình | Có |
| **RQ3** | Thiết bị đo chuyển được qua ngôn ngữ và **chế độ pháp lý** khác không — tầng luật cứng mất bao nhiêu recall khi đổi nước? | Tính chuyển giao của thiết bị đo phụ thuộc chế độ công bố thông tin, không chỉ phụ thuộc chất lượng mô hình | Có (liều nhỏ) |
| RQ4 (mở rộng) | Ước lượng web so với điều tra doanh nghiệp GSO (A5.2) lệch nhau ra sao — biên mở rộng vs biên thâm dụng? | Chỉ khả thi nếu xin được bảng GSO | **Không** — bản mở rộng |
| RQ5 (mở rộng) | So sánh Việt Nam – Nhật Bản: cấu trúc tham gia TMĐT của SME sản xuất ở hai thị trường khác nhau thế nào? | Nội dung chính của **Giai đoạn 2** (Phụ lục C) | **Không** |

Thay đổi so với v3: RQ1 cũ ("web đo được không") hạ thành tiền đề; RQ3 cũ ("kiểm định thế nào
khi không có nhãn") **nâng lên RQ1 và chuyển từ dạng lập luận sang dạng đo được**; RQ4 rút khỏi
đường găng vì phụ thuộc công văn có thể không về.

**Chỉ tiêu đo (chỉ giữ cái quan sát được):** có website hoạt động · có danh mục sản phẩm ·
có chức năng đặt hàng/giỏ hàng · phương thức thanh toán hiển thị · liên kết mạng xã hội ·
liên kết/gian hàng sàn TMĐT · ngôn ngữ website.
**Đã loại khỏi phạm vi:** Digital VA (tham số tự đặt, không có ground truth), dự báo IIP bằng
đặc trưng số hóa (dữ liệu digital chỉ có một kỳ), cào listing sàn hàng loạt (anti-bot; rủi ro
pháp lý Điều 289 BLHS nếu vượt chặn).

## 4. Thiết kế nghiên cứu

### 4.1. Hai hiện trường, hai vai khác nhau

| | **Nhật Bản — hiệu chuẩn** | **Việt Nam — triển khai** |
|---|---|---|
| Khung chọn mẫu | 国税庁法人番号公表サイト: tải toàn bộ pháp nhân (mã pháp nhân, tên, địa chỉ), CSV/XML, toàn phần hằng tháng + khác biệt hằng ngày. **Miễn phí, không xin phép** | Xin GSO/Cục Thống kê hoặc mua Cổng ĐKKD (150k, TT 47/2019); dự phòng danh bạ MST công khai |
| Mã ngành | JSIC trong gBizINFO (chế tạo = Division E — *cần xác nhận cấp division khi triển khai*) | VSIC 4 số |
| Quy mô doanh nghiệp | Số lao động, vốn — có trong gBizINFO | Nhóm quy mô lao động (nếu khung chính về) |
| Nhãn website | **Trường URL trong gBizINFO** → nhãn bạc quy mô lớn | Không có; 28 DN niêm yết đã xác minh tay |
| Nhãn "có đặt hàng" | Trang công bố theo 特定商取引法 (*cần xác nhận phạm vi bắt buộc*) — dấu hiệu **trên trang** | Danh bạ website TMĐT đã thông báo với iDEA — dấu hiệu **phía đăng ký** |
| Chi phí tiếp cận | Bằng không, tức thời | Công văn, phí, độ trễ không kiểm soát được |

Đây không phải "thêm một nước cho oai". Cột Nhật cấp đúng bốn thứ mà cột Việt Nam đang thiếu:
khung đầy đủ, mã ngành, phân tầng quy mô, và nhãn để chấm điểm.

**Bất đối xứng chính là thiết kế:** ở Nhật ta *có* nhãn nên biết sự thật; ta cố ý **che nhãn đi**,
chạy đúng chồng kiểm định không nhãn dùng cho Việt Nam, rồi **mở nhãn ra so** — hiệu số đó là
câu trả lời cho RQ1.

### 4.2. Nhãn bạc và nhãn vàng — đừng nhầm hai thứ

Trường URL của gBizINFO là dữ liệu **doanh nghiệp tự khai với cơ quan quản lý**, nên tự nó có
sai số: thiếu, cũ, sai, hoặc trỏ tới công ty mẹ. Vì vậy:

- **Nhãn bạc (silver):** trường URL gBizINFO, quy mô hàng nghìn. Dùng để chấm bộ dò URL ở quy mô.
- **Nhãn vàng (gold):** ~100 doanh nghiệp Nhật xác minh tay. Dùng để **đo sai số của chính nhãn bạc**, rồi hiệu chỉnh mọi con số tính từ nhãn bạc.
- Kết quả phụ đăng được: **chất lượng đăng bạ website của chính phủ Nhật** — bao nhiêu phần trăm URL đã chết, đã đổi, trỏ sai. Cùng loại phân tích ta làm với danh bạ iDEA ở Việt Nam, nên hai nước so được với nhau.

Không có bước này thì cả RQ1 đứng trên một nhãn chưa được kiểm — tức lặp lại đúng lỗi
"tin vào nhãn có sẵn" mà audit 20–21/8 đã phát hiện ở tầng dự báo.

### 4.3. Kỷ luật chống rò rỉ nhãn (bắt buộc)

Audit tháng 8 cho thấy rò rỉ nhãn đã một lần làm sập tầng dự báo. Lần này rủi ro nằm đúng ở
trường URL của gBizINFO. Quy tắc cứng:

1. Trường URL tách khỏi bảng khung mẫu **ngay khi tải**, lưu ở đường dẫn riêng (`data/raw/jp_labels/`), **không nằm trong bảng nào mà pipeline đọc**.
2. Bộ dò URL nhận đúng ba trường: tên pháp nhân, địa chỉ, mã ngành. Không nhận gì khác.
3. Việc mở nhãn chỉ xảy ra trong script tính điểm, chạy **sau khi** kết quả dò đã ghi và đóng băng.
4. Ghi log hash của bảng đầu vào để chứng minh trong phụ lục bài báo rằng nhãn không có mặt lúc suy luận.

### 4.4. Khung chọn mẫu và mẫu

- **Nhật:** tải toàn bộ khung từ 国税庁, khớp mã pháp nhân sang gBizINFO để lấy JSIC + quy mô +
  URL. Rút mẫu phân tầng theo division chế tạo × quy mô lao động. Pilot **300–500 DN**, mở rộng
  1.000+ nếu Giai đoạn 2 được duyệt.
- **Việt Nam:** như proposal-v3 mục 4.1 — khung chính xin GSO / mua Cổng ĐKKD; khung dự phòng
  danh bạ MST công khai + danh bạ KCN, ghi rõ hạn chế độ phủ. Phân tầng VSIC division × quy mô,
  đích **1.500–2.500 DN**; pilot 2–3 division trước (10 thực phẩm, 22 nhựa–cao su, 25/27 cơ khí–điện).
- **Ánh xạ ngành:** VSIC ↔ ISIC ↔ JSIC ở cấp division, lập bảng ánh xạ tay và **công bố bảng đó
  trong phụ lục** — bản thân nó là sản phẩm dùng lại được, và là chỗ dễ sai nhất khi so hai nước.
- **28 DN niêm yết hiện có:** không còn là quần thể nghiên cứu; giữ làm tập con đối chiếu giàu
  dữ liệu (có BCTC thật từ CafeF) cho case study mô tả.

### 4.5. Pipeline đo lường

```
Khung (JP: 法人番号 + gBizINFO | VN: đăng bạ)
  → Tìm URL (search + đối sánh thực thể, abstain khi mỏng)
  → Cào website (httpx/Playwright, chỉ trang công khai)
  → Trích chỉ tiêu (thác 3 tầng)
  → Dò hiện diện sàn (search + xác minh, KHÔNG cào listing)
  → Ước lượng có trọng số + hiệu chỉnh chệch → Bảng chỉ tiêu ± CI → Trang công bố
```

Một pipeline, hai cấu hình quốc gia. **Điều kiện tự đặt cho thiết kế:** phần khác nhau giữa
hai nước chỉ được nằm trong tệp cấu hình (mẫu regex tầng 1, ngôn ngữ prompt, danh mục sàn),
không được nằm trong logic. Nếu phải sửa logic để chạy được nước thứ hai thì đó chính là câu
trả lời (âm tính) cho RQ3 — và phải báo cáo đúng như vậy, không được lặng lẽ sửa.

**Trích chỉ tiêu — thác 3 tầng** (báo cáo đường cong chi phí–chất lượng từng tầng):

1. **Luật cứng:** regex/DOM. VN — giỏ hàng, logo VNPay/Momo/COD, link Shopee/TikTok/Lazada.
   JP — カート/買い物かご, cổng thanh toán nội địa, link Rakuten/Amazon JP/Yahoo Shopping,
   trang 特定商取引法. Precision cao, recall thấp, miễn phí.
2. **LLM local** đọc text đã render → JSON có cấu trúc, mỗi trường kèm confidence + quyền từ chối. Cùng một prompt, đổi ngôn ngữ đầu vào — đây là phép thử zero-shot đa ngữ của RQ3.
3. **Người:** chỉ duyệt ca LLM từ chối hoặc tầng 1–2 mâu thuẫn.

**Hiện diện sàn (RQ2):** tìm gian hàng chính thức bằng truy vấn site-restricted + đối sánh tên
bằng LLM + xác minh tay trong gold standard. Chỉ ghi **có/không + URL gian hàng**, không cào
sản phẩm — không đụng anti-bot, không rủi ro pháp lý.

### 4.6. Gold standard

- **Việt Nam:** 500 DN phân tầng (400 tối thiểu), phủ đủ division × quy mô; **150 DN gán đôi
  độc lập** để tính Cohen's kappa. Sổ tay chú giải dịch–thích ứng từ annotation handbook ESSnet.
- **Nhật:** ~100 DN xác minh tay (mục 4.2). Nhỏ vì mục đích khác — không dùng để suy rộng, chỉ
  dùng để hiệu chuẩn nhãn bạc.
- **Quy trình:** LLM tiền-gán toàn bộ → người duyệt/sửa. Sản phẩm phụ đăng được: chi phí
  giờ-người tiết kiệm nhờ tiền-gán ở cùng mức chất lượng.

### 4.7. Chồng kiểm định — và phép đo chính của RQ1

| Lớp | Nguồn | Kiểm cái gì | Có ở VN? | Có ở JP? |
|---|---|---|---|---|
| 1 | Gold standard | P/R/F1 từng chỉ tiêu, từng tầng; so mốc châu Âu ~83–88% | Có (500) | Có (100) |
| 2 | Nhãn phía đăng ký | VN: danh bạ iDEA. JP: trường URL gBizINFO | Bán phần | **Quy mô lớn** |
| 3 | Neo mức quốc gia | VN: iDEA (44% có website; 42% trong đó có đặt hàng; 23% bán sàn) + EBI/VECOM. JP: IPA DX動向 | Có | Có |
| 4 | Nhãn điều tra chính thức | VN: bảng A5.2 GSO (nếu về). JP: điều tra 通信利用動向調査 (công bố sẵn) | Không chắc | Có |

**Phép đo của RQ1:** ở Nhật, tính sai số thiết bị đo bằng lớp 1+3 (thứ Việt Nam có) → gọi là
`ê_không_nhãn`. Rồi tính lại bằng lớp 2+4 (thứ chỉ Nhật có) → gọi là `e_thật`. Báo cáo hiệu số,
dấu của hiệu số, và nó biến thiên theo phân tầng nào. **Đó là con số trung tâm của bài** — và nó
nói cho mọi nhà thống kê ở nước thiếu điều tra ICT biết họ đang lạc quan hay bi quan bao nhiêu.

### 4.8. Ước lượng

Trọng số thiết kế theo tầng; phân tích chệch không-tìm-được-URL (thiên về DN nhỏ/cũ) — mô hình
hóa xác suất tìm được URL theo đặc điểm DN, hiệu chỉnh kiểu model-assisted (tinh thần combined
estimator của Istat). Báo cáo khoảng tin cậy mọi ước lượng; tuyệt đối không công bố điểm ước
lượng trần.

## 5. AI stack — AI là thiết bị đo, mỗi mảnh có sai số công bố

Mục này là **trọng tâm kỹ thuật của bài**, không còn là mục hỗ trợ.

| Thành phần | Công nghệ | Baseline so sánh | Số đo | Vai trò |
|---|---|---|---|---|
| Đối sánh URL–DN | LLM đọc bằng chứng cấu trúc | Fuzzy matching (kế thừa shop matcher) | P/R trên nhãn bạc JP (n lớn) + gold VN | Kết quả chính RQ1 |
| Trích chỉ tiêu website | Thác luật→LLM→người | Từng tầng so với nhau | Đường cong chi phí–chất lượng | Kết quả chính |
| **Chuyển giao đa ngữ** | Cùng prompt, đổi ngôn ngữ đầu vào (vi → ja) | Prompt bản địa hoá riêng từng nước | Δ P/R giữa hai nước, tách theo tầng | **Kết quả chính RQ3** |
| Đối sánh gian hàng sàn | LLM + xác minh tay | Fuzzy | P/R | RQ2 |
| Phân loại ngành từ web | LLM phân cấp 2→4 số | Mã trong đăng bạ (VSIC / JSIC) | Agreement + phân tích lệch | Chất lượng khung mẫu, hai nước |
| Tiền-gán nhãn | LLM local + human review | Gán tay thuần | Kappa, giờ-người tiết kiệm | Đóng góp phương pháp phụ |
| Selective prediction | Confidence + abstain kèm lý do | Không abstain | Hiệu chuẩn (calibration), risk–coverage | Xuyên suốt |
| (Tùy chọn) VLM nhìn screenshot | Vision model dò nút đặt hàng trong ảnh | Text-only | Δrecall | Ngoài đường găng |

**Quy tắc tái lập (bắt buộc):** model open-weights chạy trên GPU lab (cỡ Qwen-Instruct 7–32B là
đủ cho phân loại có cấu trúc, và xử lý tiếng Nhật được), **ghim phiên bản**, temperature 0,
toàn bộ prompt vào phụ lục, chạy lặp đo độ ổn định đầu ra. Không dùng API đóng cho các con số
vào bài.

**Không làm:** chatbot, fine-tune LLM không lý do, deep learning trên chuỗi 112 điểm,
narrative sinh văn trong báo cáo.

## 6. Dữ liệu: tải gì trước, xin gì sau

Thay đổi lớn so với v3: **nguồn không cần xin phép lên ưu tiên 1**. Không phải vì Nhật quan
trọng hơn Việt Nam, mà vì dự án không được phép treo vào chữ ký của người khác.

| Ưu tiên | Nguồn | Cách lấy | Giá trị chính | Rủi ro |
|---|---|---|---|---|
| **1** | 国税庁法人番号公表サイト — toàn bộ pháp nhân | Tải công khai, CSV/XML, không cần token | Khung chọn mẫu Nhật đầy đủ | Chỉ có 3 trường cơ bản → phải khớp gBizINFO |
| **1** | gBizINFO (METI) — 5tr+ pháp nhân | API v2 (đăng ký token miễn phí) + tải hàng loạt CSV/JSON, cập nhật hằng ngày | JSIC, lao động, vốn, **URL** (nhãn bạc), DX認定, trợ cấp | Độ phủ trường URL chưa biết → phải đo, và đó là kết quả |
| 2 | Trích xuất đăng bạ Section C (VN) | GVHD → GSO/Cục Thống kê; song song mua Cổng ĐKKD (TT 47/2019) | Khung mẫu VN → suy diễn quốc gia | Độ trễ cao → dùng khung dự phòng |
| 3 | Xuất danh bạ website TMĐT đã thông báo | Công văn → iDEA; có tra cứu công khai | Nhãn phía đăng ký + đo khoảng trống tuân thủ | Tra cứu tay cho riêng mẫu nếu chưa về |
| 4 | Bảng A5.2 phiếu 2/DN-MAU (2022–2024) | GVHD → GSO, công văn | RQ4 (đã rút khỏi đường găng) | Có thể không bao giờ về |
| 5 | 通信利用動向調査 (Nhật) | Công bố sẵn | Neo mức quốc gia + lớp 4 cho JP | Định nghĩa chỉ tiêu khác VN → phải đối chiếu cẩn thận |
| 6 | Xác nhận miễn trừ NCKH, Luật BVDLCN 91/2025 | GVHD/khoa luật | Mục đạo đức nghiên cứu | Thiết kế đã tự vệ: chỉ trang công khai |

Dữ liệu đã có: GSO macro live (829 dòng — chương bối cảnh), CafeF BCTC 28/28 mã (case study
đối chiếu), bộ dò website chạy live (phôi của tầng 1).

## 7. Tận dụng hệ thống hiện có

| Giữ nguyên | Đổi vai | Cắt |
|---|---|---|
| Crawler GSO/OECD (chương bối cảnh) | Bộ dò website → tầng 1 của thác trích chỉ tiêu, hai cấu hình quốc gia | KPI Digital VA + heatmap VA khỏi UI |
| CafeF BCTC + benchmark form/OCR | Shop matcher → đối sánh URL–DN và gian hàng–DN | Bảng MAPE 4 model (rò rỉ nhãn, thua naive — kiểm chứng 21/8) |
| Kiến trúc provenance/abstain (→ mục "khung chất lượng" của bài) | Product categorizer → phân loại VSIC/JSIC từ nội dung web | Pipeline cào listing sàn (đóng băng, giữ code + ADR làm phụ lục bài học) |
| PostgreSQL + FastAPI + frontend | Dashboard → trang công bố chỉ tiêu ± CI, **có tab so sánh VN–JP** | Forecast IIP khỏi phạm vi khoa học |

## 8. Roadmap 14 tuần (25/8 → 01/12)

**Phạm vi tháng 12 không đổi so với v3.** Nhánh Nhật chỉ vào roadmap ở **liều một tuần**
(tuần 2), đủ để có một con số thật trên dữ liệu Nhật; phần còn lại là nội dung Giai đoạn 2.

Người: **B** = bạn · **AG** = AI agent · **SV** = 2 sinh viên hỗ trợ · **GV** = GVHD

| Tuần | Việc | Ai | Mốc chốt |
|---|---|---|---|
| 1 (25–31/8) | Gặp GVHD: duyệt proposal này, **làm rõ thể thức nghiệm thu tháng 12**, hỏi ý kiến GVHD về nhánh Nhật, ký 2 công văn (Phụ lục A, B); mua báo cáo Cổng ĐKKD; dựng LLM local | B+GV, AG | Công văn đã gửi + quyết định về nhánh Nhật |
| 2 | **Pilot hiệu chuẩn Nhật** (evol-1 T08): tải khung 国税庁 + gBizINFO, 300 DN chế tạo, chạy bộ dò URL, chấm P/R trên nhãn bạc đã giữ riêng | AG+B | **Con số đầu tiên trên dữ liệu Nhật** |
| 2–3 | Sổ tay chú giải; gỡ KPI sai khỏi web; chốt danh mục chỉ tiêu + schema; bảng ánh xạ VSIC↔JSIC | AG+B | Handbook v1 + bảng ánh xạ |
| 3–4 | Khung mẫu VN (chính hoặc dự phòng) + rút mẫu phân tầng; tuyển & tập huấn 2 SV | B+AG, SV | Mẫu đã rút |
| 4–5 | Cào vòng pilot VN (2–3 division); khớp danh bạ iDEA | AG | ≥80% mẫu pilot xử lý xong URL |
| 5–7 | Thác trích chỉ tiêu tầng 1+2; LLM tiền-gán; SV gán gold standard (150 gán đôi) | AG+SV | Gold standard xong, có kappa |
| 7–8 | Dò hiện diện sàn; P/R từng tầng; **chạy tầng 1+2 trên 300 site Nhật → Δ P/R cho RQ3** | AG+B | Bảng chất lượng thiết bị đo, hai nước |
| 8–9 | Mở rộng cào toàn mẫu VN (nếu khung chính đã về; nếu chưa → chốt phạm vi pilot) | AG | Dữ liệu đủ chạy ước lượng |
| 9–10 | Ước lượng + trọng số + hiệu chỉnh chệch; RQ2; **phép đo RQ1 (`ê_không_nhãn` vs `e_thật`)** | B+AG | Bảng kết quả chính ± CI |
| 10–12 | Viết báo cáo NCKH (VN) + bản thảo tiếng Anh; dashboard thành trang công bố | B viết, AG nháp/red-team | Nháp đủ gửi GV |
| 12–13 | GV phản biện; sửa; red-team bằng AI (giả lập hội đồng) | B+GV+AG | Bản gần cuối |
| 14 (24/11–01/12) | Hoàn thiện, nộp; đóng gói dataset + codebook + code tái lập; **viết Phụ lục C thành 研究計画書** | B | **Nộp** |

**Đường găng:** pilot Nhật tuần 2 (rẻ, không phụ thuộc ai) → khung mẫu VN tuần 3–4 → gold
standard tuần 5–7. Mọi thứ khác trượt được, ba mắt xích này thì không.

**Chốt cứng về phạm vi:** nếu đến tuần 8 nhánh Nhật vượt quá một tuần công sức, **cắt nó xuống
còn bảng nhãn bạc + con số P/R của tuần 2** và đẩy toàn bộ phần còn lại sang Giai đoạn 2.
Báo cáo tháng 12 và thư giới thiệu quan trọng hơn một chương so sánh đẹp.

## 9. Rủi ro và phương án

| Rủi ro | Xác suất | Phương án |
|---|---|---|
| GSO không trả lời kịp | Cao | Khung dự phòng VN + nhánh Nhật vẫn chạy; A5.2 dời sang bản mở rộng |
| Nhánh Nhật phình to, ăn thời gian của phần VN | **Cao** | Chốt cứng ở mục 8; nhánh Nhật là *một tuần*, không phải một chương |
| Trường URL gBizINFO phủ thấp hoặc quá cũ | Vừa | Chính là kết quả cần báo cáo (chất lượng đăng bạ); nếu quá thấp thì hạ nhãn bạc xuống vai sàng lọc và tăng gold JP lên 200 |
| Rò rỉ nhãn URL vào pipeline | Vừa nếu không kỷ luật | Mục 4.3, có log hash để chứng minh |
| Tầng 1 tiếng Nhật recall thấp | Chắc chắn một phần | Đó là RQ3, không phải lỗi — đo và giải thích bằng chế độ pháp lý |
| Ánh xạ VSIC↔JSIC sai lệch | Vừa | Chỉ so ở cấp division, công bố bảng ánh xạ, phân tích độ nhạy |
| GVHD không muốn nhánh nước ngoài trong đề tài cấp trường | Vừa | Hỏi ngay tuần 1; nếu không → giữ toàn bộ nhánh Nhật ở Phụ lục C như đề cương cá nhân, thân bài về đúng v3 |
| Tìm URL kém với DN nhỏ | Chắc chắn một phần | Chính là phân tích chệch của bài |
| Search engine chặn truy vấn hàng loạt | Vừa | API tìm kiếm trả phí liều nhỏ + giãn nhịp + cache |
| SV gán nhãn không đều tay | Vừa | Handbook + buổi hiệu chuẩn + kappa trên tập gán đôi |
| Luật 91/2025 diễn giải chặt hơn | Thấp | Chỉ trang công khai; bỏ/băm định danh cá nhân; hỏi GVHD tuần 1 |

## 10. Sản phẩm đầu ra tháng 12

1. **Báo cáo NCKH** (tiếng Việt) — pilot VN có kết quả thật + pilot hiệu chuẩn Nhật + thiết kế mở rộng cấp trường.
2. **Bản thảo tiếng Anh** nộp được. Đích thực tế: tạp chí/hội nghị thống kê chính thức (SJIAOS, hội nghị thống kê khu vực). *Không đặt mục tiêu Q1 cho bản này* — xem ghi chú cuối file.
3. **Bộ dữ liệu + codebook** có phiên bản, hai nước: chỉ tiêu theo DN (ẩn danh hoá), bảng ước lượng ± CI, bảng ánh xạ VSIC↔JSIC.
4. **Web demo chạy thật:** trang công bố chỉ tiêu, phương pháp, chất lượng nguồn, tab so sánh hai nước.
5. **Pipeline tái lập:** code + prompt + model version ghim + log hash chứng minh không rò rỉ nhãn + hướng dẫn chạy lại.
6. **Đề cương nghiên cứu bậc thạc sĩ (Phụ lục C)** — dùng làm 研究計画書 khi ứng tuyển, và làm phần "hướng phát triển" của báo cáo lab. Cùng một văn bản, hai mục đích.

---

## Phụ lục A — Dự thảo công văn gửi GSO / Cục Thống kê

Giữ nguyên như proposal-v3, Phụ lục A. Không sửa nội dung; chỉ ghi chú rằng bảng A5.2 (đề nghị
số 2) nay thuộc phần mở rộng, nên nếu cơ quan chỉ đáp ứng được đề nghị số 1 (khung mẫu) thì
đề tài vẫn đủ điều kiện triển khai.

## Phụ lục B — Dự thảo công văn gửi Cục TMĐT và Kinh tế số (iDEA)

Giữ nguyên như proposal-v3, Phụ lục B.

## Phụ lục C — Đề cương mở rộng bậc thạc sĩ (phôi của 研究計画書)

*Phần này vừa là mục "hướng phát triển" của báo cáo lab, vừa là bản nháp research plan khi ứng
tuyển. Viết ở tuần 14, sau khi đã có số thật để dẫn.*

**Tên tạm:** Đo lường mức độ tham gia thương mại điện tử của doanh nghiệp nhỏ và vừa ngành chế
tạo từ dữ liệu web — thiết bị đo chuyển giao được giữa các chế độ thống kê

**Bối cảnh chính sách (phần nói với hội đồng Nhật):** Nhật đang chi ngân sách trợ cấp số hoá
SME (IT導入補助金 và các chương trình liên quan) trong khi công cụ đo mức số hoá SME dựa vào
điều tra tần suất năm. Báo cáo IPA『DX動向2025』cho thấy SME Nhật tụt lại so với Mỹ và Đức, và
hơn một nửa SME nói không thấy rõ lợi ích. Một thiết bị đo chi phí biên gần bằng không, tần suất
tháng hoặc quý, cho phép theo dõi hiệu quả trợ cấp gần thời gian thực thay vì sau một năm.

**Điểm khởi đầu (đã có, không phải hứa):** pipeline chạy được trên hai nước; con số P/R của bộ
dò URL trên n≈300 doanh nghiệp chế tạo Nhật, chấm bằng nhãn từ gBizINFO đã giữ riêng chống rò
rỉ; kết quả pilot Việt Nam n≈1.500 với gold standard 500 DN có kappa.

**Nội dung mở rộng đề xuất cho 2 năm:**

1. Mở rộng mẫu Nhật lên quy mô suy diễn được, phân tầng theo JSIC × quy mô × vùng.
2. **Chuỗi thời gian thay vì một lát cắt:** cào lặp theo quý để lần đầu có *biến thiên theo thời gian* của chỉ tiêu số hoá — thứ mà lát cắt một kỳ không cho, và là điều kiện để nói bất cứ điều gì về nhân quả của trợ cấp.
3. So sánh cấu trúc VN–JP: hai nước đều nhiều SME chế tạo nhưng khác nhau về mức độ sàn chiếm ưu thế và về chế độ công bố thông tin bắt buộc. Kiểm xem hiệu ứng nào là do thị trường, hiệu ứng nào do luật.
4. Nối vào chỉ tiêu chính thức: đối chiếu với 通信利用動向調査 và, nếu tiếp cận được, dữ liệu vi mô qua kênh nghiên cứu.
5. Đóng gói thành công cụ dùng lại được cho cơ quan thống kê nước thứ ba — đích cuối là *quy trình*, không phải *một bảng số*.

**Vì sao cần làm ở Nhật, không làm được ở nơi khác:** Nhật là một trong ít nước có đồng thời
(a) đăng bạ pháp nhân toàn bộ, mở, cập nhật hằng ngày; (b) dữ liệu hoạt động doanh nghiệp gắn
mã pháp nhân với mã ngành và trường website; (c) một bài toán chính sách SME đang được cấp
ngân sách. Ba điều kiện đó cùng lúc là tiền đề của thiết kế hiệu chuẩn nêu ở mục 4.

---

*Ghi chú phiên bản:*

*v4 kế thừa toàn bộ v3 và thay đổi ba điều: (1) thêm hiện trường hiệu chuẩn Nhật Bản để biến
RQ "kiểm định thế nào khi không có nhãn" từ dạng lập luận thành dạng đo được; (2) đưa nguồn
không cần xin phép lên ưu tiên 1 để đề tài không treo vào công văn; (3) rút RQ4 (bảng A5.2 GSO)
khỏi đường găng. Phạm vi giao tháng 12 không đổi.*

*v3 đã thay thế trọng tâm "Digital VA / VDEI / dự báo IIP" của proposal-v2 sau audit 20–21/8/2026
(rò rỉ nhãn trong feature dự báo, 4/4 model thua naive baseline, chỉ số Digital VA dựa trên
13 dòng listing và 3 hằng số tự đặt). Các công thức trong CONTEXT.md thuộc phạm vi cũ cần cập
nhật bằng ADR riêng; v4 bổ sung một quyết định kiến trúc nữa cần ADR — cấu hình đa quốc gia của
pipeline (mục 4.5) — đề xuất `docs/adr/0004-multi-country-measurement-config.md` khi bắt đầu
triển khai.*

*Về mục tiêu tạp chí: bản thảo tiếng Anh nhắm tạp chí thống kê chính thức, không nhắm Q1. Lý do
là chọn có ý thức, không phải hạ tiêu chuẩn — đích của đề tài này là một thiết bị đo chạy được
và một đề cương nghiên cứu dẫn được bằng số thật, phục vụ nộp hồ sơ học bổng và tuyển dụng.
Nếu về sau muốn nhắm tạp chí cao hơn, ngả tự nhiên là tách phần kỹ thuật (thác trích xuất,
selective prediction, chuyển giao đa ngữ) thành một bài riêng cho tạp chí xử lý thông tin,
dùng chính bộ số đo của mục 5.*
