# Kinh tế số ngành Chế biến, Chế tạo — Sổ kiến thức dự án

Tài liệu này giải thích **mục tiêu kinh tế**, **ý nghĩa các thành phần**, **công thức** và **mối liên hệ** dùng trong Manufacturing Data Economy Platform. Không chứa code — đọc trước khi hoàn thiện hoặc thay đổi logic số liệu.

Nguồn chuẩn hóa thuật ngữ ngắn: `CONTEXT.md`.  
Sổ tay keyword kỹ thuật: `docs/knowledge.md`.  
Quyết định macro OECD: `docs/adr/0001-oecd-vietnam-macro-policy.md`.

---

## 1. Mục tiêu kinh tế của dự án

### 1.1. Câu hỏi nghiên cứu

Dự án trả lời: **kinh tế số đang xuất hiện và đóng góp thế nào vào ngành công nghiệp chế biến, chế tạo Việt Nam (VSIC Section C)** — không phải bán lẻ, không phải toàn nền kinh tế số nói chung.

Cụ thể cần đo và giải thích được:

1. **Sản xuất công nghiệp** đang tăng/giảm thế nào theo thời gian (IIP Section C).
2. **Doanh nghiệp chế tạo** (mẫu niêm yết) đã số hóa kênh bán và hiện diện số tới mức nào.
3. **Doanh thu / giá trị gia tăng gắn với kênh số** ước lượng được bao nhiêu ở cấp DN.
4. **Sự tương tác** giữa số hóa (micro) và sản xuất công nghiệp (macro) — có tín hiệu đồng biến, trễ, hay chỉ là nhiễu.
5. **Vị thế cạnh tranh số** của một DN so với peer cùng phân ngành (benchmark kiểu SingStat BITE).
6. **Triển vọng ngắn hạn** của IIP Section C (dự báo 3–6 tháng) có hỗ trợ đọc chu kỳ sản xuất không.

### 1.2. Vì sao không còn là “TMĐT bán lẻ”

Proposal gốc đo **tổng mức bán lẻ / Division 47**. Thực tế đề tài cần chuyển sang **chế biến, chế tạo** vì:

| Khía cạnh | Bán lẻ (cũ) | Chế tạo (project này) |
|-----------|-------------|------------------------|
| Đơn vị ngành | VSIC Division 47 | VSIC Section C (mã 10–33) |
| Biến “sức khỏe” ngành | Tổng mức bán lẻ | **IIP**, giá trị gia tăng công nghiệp |
| Hiện diện số | Shop bán hàng trực tiếp | Website DN + sàn + (sau này) logistics/thanh toán/xuất khẩu số |
| Đóng góp KTS | Doanh thu TMĐT bán lẻ | **Digital VA** từ online revenue, biên lãi, adoption, đầu tư số |
| Benchmark | Retail peers | Peer cùng **VSIC 2-digit** trong mẫu niêm yết |

### 1.3. Ba tầng quan sát — một bức tranh

```
        ┌─────────────────────────────────────────┐
        │  MACRO (GSO): IIP, shipment, inventory  │  ← “ngành đang sản xuất thế nào?”
        └──────────────────┬──────────────────────┘
                           │ truyền dẫn / tương tác
        ┌──────────────────▼──────────────────────┐
        │  MICRO (DN niêm yết): BCTC, kênh số,    │  ← “DN số hóa và kiếm tiền số thế nào?”
        │  online revenue, Digital VA, ratios     │
        └──────────────────┬──────────────────────┘
                           │ leading / đối chiếu
        ┌──────────────────▼──────────────────────┐
        │  QUỐC TẾ (OECD): INDIGO VNM, MEI peer   │  ← “bối cảnh số & cầu ngoài biên?”
        └─────────────────────────────────────────┘
```

Ý nghĩa kinh tế: **macro** nói về sản lượng; **micro** nói về hành vi số và đóng góp giá trị ở DN; **quốc tế** cung cấp chỉ báo mở thương mại số và cầu sản xuất vùng peer — không thay thế số Việt Nam.

---

## 2. Data economy trong ngữ cảnh dự án

### 2.1. “Kinh tế số” ở đây không phải gì

Không phải:

- Toàn bộ GDP số quốc gia.
- Chỉ số “digital economy” OECD/UNCTAD đầy đủ.
- Chỉ đếm số app hay số website.

Mà là: **phần hoạt động kinh tế của ngành chế tạo có thể quan sát qua kênh số** (hiện diện, giao dịch, doanh thu ước tính, hiệu quả lao động số) và **cách phần đó gắn với sản xuất công nghiệp**.

### 2.2. Data economy như “nguyên liệu phân tích”

“Data economy” trong tên platform mang hai nghĩa chồng nhau:

1. **Đối tượng nghiên cứu**: kinh tế số của ngành CBCT.
2. **Cách làm**: xây chuỗi dữ liệu (macro + micro + quốc tế) để ước lượng chỉ tiêu mà thống kê chính thức chưa đủ chi tiết ở cấp DN/sàn.

Nguyên tắc trung thực: **thiếu số thì ghi thiếu / fallback có nguồn — không bịa OECD/GSO, không invent percentile 50 khi không có peer.**

---

## 3. Ngành công nghiệp chế biến, chế tạo

### 3.1. VSIC Section C

**VSIC** (Vietnam Standard Industrial Classification) — hệ thống ngành kinh tế Việt Nam.  
**Section C** = **chế biến, chế tạo** (manufacturing).

Phạm vi thường dùng trong project: mã cấp 2 **10–33** (thực phẩm, dệt may, hóa chất, cao su/nhựa, kim loại, điện tử, thiết bị điện, trang sức…).

Ví dụ mã 4 chữ số:

| Mã | Ngành con | DN mẫu minh họa |
|----|-----------|-----------------|
| 1050 | Sữa | VNM |
| 1071 | Thực phẩm khác | MSN |
| 2011 | Hóa chất cơ bản | DGC |
| 2211 | Cao su | GVR |
| 2220 | Nhựa | BMP |
| 2410 | Sắt thép | HPG |
| 2620 | Máy tính & thiết bị ngoại vi | FPT (mfg electronics trong mẫu) |
| 2710 | Thiết bị điện | REE |
| 2740 | Thiết bị chiếu sáng | **RAL (Rạng Đông)** — case study chính |
| 3211 | Trang sức | PNJ |

### 3.2. ISIC Section C và ánh xạ

**ISIC** là chuẩn quốc tế. OECD công bố nhiều series theo **ISIC Section C**.  
Project giữ bảng **ISIC Section C ↔ VSIC 10–33** để:

- Gắn series quốc tế đúng “manufacturing”.
- Gắn DN Việt Nam đúng mã VSIC khi so sánh / heatmap / peer.

Không dùng NAICS hay HS làm khung ngành chính của đề tài.

### 3.3. Ý nghĩa kinh tế của việc “chọn Section C”

Chế tạo là nơi:

- Tạo **giá trị gia tăng** lớn trong công nghiệp.
- Chịu chu kỳ **IIP**, tồn kho, xuất hàng.
- Đang chuyển từ bán B2B truyền thống sang **đa kênh** (website, sàn, social) — nhưng mức độ không đồng đều giữa thép, sữa, đèn, trang sức…

Đo KTS trên Section C giúp trả lời: số hóa đang **bổ sung** hay **thay thế** kênh truyền thống ở DN sản xuất, chứ không chỉ đo “mua sắm online của hộ gia đình”.

---

## 4. Tầng macro — sức khỏe sản xuất ngành

### 4.1. IIP (Industrial Production Index) — biến trung tâm

**IIP Section C (`IIP_C`)**: chỉ số sản xuất công nghiệp chế biến chế tạo, tần suất **tháng**, nguồn GSO/NSO.

Ý nghĩa:

- Phản ánh **khối lượng / hoạt động sản xuất** theo thời gian (chỉ số, không phải doanh thu tiền mặt).
- Là **biến mục tiêu dự báo** chính của ML Lab.
- Thường mang tính **lagging** so với một số chỉ báo tin tưởng kinh doanh quốc tế: IIP cho biết kết quả sản xuất đã diễn ra.

Không nhầm IIP với:

- GDP / GRDP (giá trị gia tăng tiền tệ — pillar M1 hướng tới nhưng chưa đủ nguồn đầy đủ trong phase hiện tại).
- PMI (chưa nằm trong phạm vi project).
- Doanh thu TMĐT DN (micro).

### 4.2. Shipment (chỉ số xuất hàng / tiêu thụ)

Series kiểu **E07.03** — phản ánh hàng đã xuất / tiêu thụ công nghiệp.  
Nguồn NSO thường **năm** → khi đưa vào chuỗi tháng dùng **step-hold** (giữ nguyên giá trị năm cho mọi tháng trong năm), không nội suy tuyến tính để bịa xu hướng trong năm.

Ý nghĩa kinh tế: cùng IIP, shipment giúp đọc **sản xuất vs tiêu thụ**. Nếu sản xuất tăng mà xuất hàng chậm → rủi ro tồn kho / cầu yếu.

### 4.3. Inventory (chỉ số tồn kho)

Series kiểu **E07.04** — tồn kho cuối kỳ (thường 31/12), cũng step-hold năm → tháng.

Ý nghĩa: tồn kho tăng kèm IIP tăng có thể là tích trữ; tồn kho tăng kèm xuất hàng yếu thường xấu hơn cho chu kỳ.

### 4.4. Giá trị gia tăng công nghiệp / GRDP ngành

Trong bộ VDEI (M1) là chỉ tiêu **cốt lõi về hiệu quả kinh tế thực** (tiền tệ), khác IIP (chỉ số sản lượng).  
Trong roadmap: còn phụ thuộc nguồn GSO quý/năm — **không invent**. Khi chưa có, dashboard vẫn lấy IIP làm proxy “quy mô & nhịp SXCN”.

### 4.5. Quy tắc nguồn macro Việt Nam

**GSO-first**: số Việt Nam về sản xuất lấy từ NSO/GSO.  
Khi crawl live thất bại → dùng **fallback có nguồn** (`GSO_FALLBACK`), không sinh số ngẫu nhiên.

---

## 5. Tầng quốc tế (OECD) — bối cảnh và leading indicator

### 5.1. INDIGO (Digital Trade Openness) — có cho Việt Nam

Chỉ số độ mở **thương mại số**. Series **năm** cho `VNM`.

Đưa vào bảng tháng bằng **step-hold** (mọi tháng trong năm = cùng giá trị năm): vì đây là chỉ số cấu trúc năm — nội suy tuyến tính tháng sẽ **bịa động học trong năm**.

Vai trò kinh tế: proxy môi trường / độ mở số quốc gia, dùng làm feature trễ (lag) khi giải thích hoặc dự báo IIP — không phải Digital VA của từng DN.

### 5.2. MEI Industrial Production — không có cho VNM

OECD **không công bố** MEI IP cho Việt Nam.  
Project lấy **EA20 (Euro area)** làm **peer**, gắn nguồn `OECD_PEER`.

Được dùng để:

- Feature ngoại sinh / lag cho **dự báo IIP Việt Nam** (kênh cầu xuất khẩu / chu kỳ sản xuất vùng đối tác).

Không được dùng để:

- Coi như IIP Việt Nam.
- So sánh DN Việt Nam với “sản xuất Việt Nam giả”.

### 5.3. BCI và ICT Investment

Business Confidence và ICT investment GFCF: **không có series VNM đáng tin trên OECD** trong phạm vi quyết định hiện tại → **không bịa**. Để trống / banner thiếu dữ liệu.

### 5.4. Leading vs lagging (ý nghĩa phân tích)

| Loại | Ví dụ trong project | Đọc thế nào |
|------|---------------------|-------------|
| Leading / phụ trợ | INDIGO (cấu trúc), MEI peer | Gợi ý môi trường / cầu trước hoặc song song |
| Lagging / kết quả | GSO IIP | Đo kết quả sản xuất đã xảy ra |
| Đồng thời micro | Online revenue, adoption | Hành vi số DN trong kỳ |

---

## 6. Tầng micro — doanh nghiệp niêm yết mẫu

### 6.1. Vì sao chỉ ~10 DN

Mẫu cố định (HOSE/HNX): RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BMP.

Ý nghĩa:

- Đủ **đa dạng VSIC con** để minh họa heatmap / peer.
- Đủ sâu để crawl BCTC + kênh số + listing.
- **Không** phải mẫu đại diện thống kê toàn quốc — mọi percentile benchmark phải ghi rõ là **prototype trên mẫu seed**.

### 6.2. BCTC (báo cáo tài chính có cấu trúc)

Các trường kinh tế dùng trong project (ý nghĩa):

| Thành phần | Ý nghĩa |
|------------|---------|
| Doanh thu hoạt động | Quy mô kinh doanh kỳ báo cáo |
| Lợi nhuận trước thuế | Khả năng sinh lời dùng cho ROA/ROE trong benchmark |
| Tổng tài sản / vốn CSH | Cơ sở tỷ suất sinh lời và cấu trúc vốn |
| Tài sản ngắn hạn / nợ ngắn hạn | Thanh khoản (current ratio) |
| Biên lãi gộp (gross margin) | Proxy biên cho phần doanh thu online trong Digital VA |
| Số lao động | Mẫu số năng suất / digital revenue per worker |
| Chi phí (COGS, thuê, lương…) | Trường BITE-style trên form; **không** bắt buộc vào 4 ratio lõi |

### 6.3. Hiện diện số (digital presence)

Một **kênh bán / hiện diện** đã xác minh: website, Shopee, TikTok, Lazada…

Ý nghĩa kinh tế:

- **Có kênh** ≠ đã có doanh thu số lớn.
- Checkout / giỏ hàng trên website = tín hiệu **khả năng giao dịch** trực tiếp.
- Độ tin cậy ghép shop ↔ DN (ngưỡng match ~0.65) quyết định chất lượng ước lượng doanh thu sàn.

### 6.4. Marketplace listing

Một dòng sản phẩm: giá, ước lượng đơn vị đã bán, doanh thu ước tính.

Đây là **nguyên liệu trực tiếp** của online revenue khi scrape được — không phải báo cáo kế toán.

### 6.5. Online revenue (doanh thu online ước tính)

Hai đường ước lượng (theo thứ tự trung thực):

1. **Từ listing**: tổng `giá × số lượng đã bán (ước tính)` trên các listing gắn DN.
2. **Industry-ratio**: `tỷ lệ TMĐT ngành × doanh thu BCTC` — **chỉ khi tỷ lệ có nguồn** (GSO/VECOM…). Không có nguồn thì **không nhân hệ số bịa**; có thể ghi 0 + ghi nhận thiếu dữ liệu.

Tỷ số quan trọng:

**Online revenue ratio** = doanh thu online ước tính / doanh thu BCTC (cùng kỳ hoặc kỳ gần nhất có thể khớp).

Ý nghĩa: mức độ “số hóa doanh thu” — input cho feature tương tác với tăng trưởng IIP và cho pillar M3/M5/M6.

---

## 7. Bộ chỉ tiêu VDEI Manufacturing (M1–M10)

**VDEI Manufacturing** = khung pillar đo kinh tế số **riêng cho chế tạo**, tái cấu trúc từ bộ chỉ tiêu TMĐT bán lẻ cũ.

| Pillar | Tên | Câu hỏi kinh tế | Chỉ tiêu cốt lõi |
|--------|-----|-----------------|------------------|
| **M1** | Quy mô & hiệu quả SXCN | Ngành sản xuất lớn và tăng thế nào? | IIP Section C; (hướng tới) VA / GRDP ngành |
| **M2** | Chuyển đổi số DN | Bao nhiêu DN “có mặt” trên kênh số? | % có website, % bán sàn, (hướng tới) ERP/IoT |
| **M3** | Doanh thu TMĐT ngành SX | Doanh thu số chiếm bao nhiêu so với doanh thu? | Online / tổng doanh thu (mẫu hoặc ngành khi có) |
| **M4** | Kênh bán số | Bán qua đâu là chính? | Tỷ trọng website vs marketplace vs social |
| **M5** | Hiệu quả số hóa | Mỗi lao động “kiếm” được bao nhiêu qua kênh số / tổng? | Doanh thu/lao động; digital revenue per worker |
| **M6** | Đóng góp KTS | Giá trị gia tăng gắn số ước được bao nhiêu? | **Digital VA** |
| **M7** | Hạ tầng & logistics số | Giao hàng số hóa tới đâu? | % dùng logistics TMĐT, thời gian giao (phase sau) |
| **M8** | Thanh toán số | Giao dịch đi qua cổng số bao nhiêu? | % thanh toán online (phase sau) |
| **M9** | Xuất khẩu số | Đơn hàng quốc tế qua kênh online? | % đơn online quốc tế (phase sau) |
| **M10** | Năng lực cạnh tranh số | DN đứng đâu so với peer? | Percentile các ratio / chỉ số số |

**Đọc pillar như một hệ:**

- M1 = nền sản xuất.  
- M2–M4 = **mức độ và hình thái** số hóa.  
- M5–M6 = **hiệu quả và đóng góp giá trị**.  
- M7–M9 = hạ tầng giao dịch số (thường khó crawl hơn — roadmap sau).  
- M10 = định vị cạnh tranh.

---

## 8. Công thức trung tâm

### 8.1. Digital VA (giá trị gia tăng kinh tế số — cấp DN)

Công thức chuẩn dự án (`CONTEXT.md` / proposal):

```
Digital_VA =
    (Online_revenue × Gross_margin)
  + (Cost_savings × Adoption_score)
  − Digital_investment
```

Biến thể diễn giải trong plan (cùng ý):

```
Digital_VA_estimate =
    (Estimated_online_revenue × Digital_margin_proxy)
  + (Cost_savings_from_digital × Adoption_score)
  − Digital_investment_amortized
```

#### Ý nghĩa từng hạng mục

| Hạng mục | Ý nghĩa kinh tế | Nguồn ý tưởng đo |
|----------|-----------------|------------------|
| **Online_revenue × Gross_margin** | Phần **giá trị gia tăng gần đúng** từ doanh thu kênh số, giả sử biên gộp BCTC áp được cho phần online | Listing + BCTC |
| **Cost_savings × Adoption_score** | Lợi ích tiết kiệm chi phí nhờ số hóa, có trọng số theo mức adoption | Ước lượng / proxy — cần giả định rõ; không bịa nếu chưa đo |
| **Digital_investment** | Chi phí / đầu tư số đã phân bổ — trừ ra để không kể “doanh thu số” mà quên vốn đã bỏ | BCTC / giả định khấu hao — cần nguồn |

#### Những điều Digital VA **không** phải

- Không phải tổng doanh thu DN.
- Không phải IIP.
- Không phải GDP số quốc gia.
- Không thay thế VA công nghiệp chính thức của GSO.

### 8.2. Online revenue từ listing

```
Online_revenue ≈ Σ (price × units_sold_estimate)   trên các listing gắn DN
```

Hoặc, khi có tỷ lệ ngành có nguồn:

```
Online_revenue ≈ industry_online_ratio × firm_revenue_BCTC
```

### 8.3. Digital adoption score

Điểm tổng hợp mức độ số hóa DN — trọng số các kênh (ví dụ website + marketplace + social).

Ý nghĩa: DN “có mặt” đa kênh và có tín hiệu giao dịch thì adoption cao hơn → hệ số nhân phần tiết kiệm chi phí trong Digital VA và feature ML.

### 8.4. Channel diversity

Độ trải kênh (website / sàn / social).  
Ý nghĩa: đa dạng kênh giảm phụ thuộc một nền tảng; input M4 và feature `channel_diversity`.

### 8.5. Tỷ số tài chính benchmark (Module 5)

Trên BCTC cuối kỳ — **không invent trung bình hai kỳ nếu thiếu dữ liệu**:

| Tỷ số | Công thức | Ý nghĩa |
|-------|-----------|---------|
| **ROA** | Lợi nhuận trước thuế / Tổng tài sản | Sinh lời trên tài sản |
| **ROE** | Lợi nhuận trước thuế / Vốn chủ sở hữu | Sinh lời trên vốn CSH |
| **Current ratio** | Tài sản ngắn hạn / Nợ ngắn hạn | Thanh khoản ngắn hạn |
| **Equity ratio** | Vốn CSH / Tổng tài sản | Mức độ tự tài trợ bằng vốn chủ |
| **Revenue per worker** | Doanh thu / Số lao động | Năng suất doanh thu |
| **Profit per worker** | LN trước thuế / Số lao động | Năng suất lợi nhuận |
| **Digital revenue per worker** | Online revenue / Số lao động | Năng suất kênh số |

### 8.6. Percentile benchmark (M10)

So sánh một DN với **peer cùng VSIC 2-digit** trong mẫu seed (BCTC kỳ mới nhất có thể).

- Đủ peer → xếp percentile.
- Không đủ peer → **null** + trạng thái `insufficient_peers` — **không bịa percentile 50**.

Đây là công cụ **định vị tương đối trong mẫu**, không phải chuẩn quốc gia.

---

## 9. Mối liên hệ giữa các thành phần

### 9.1. Sơ đồ nhân quả / truyền dẫn (ý niệm phân tích)

```
Cầu / chu kỳ quốc tế (MEI peer)
        │
        ▼
Độ mở thương mại số (INDIGO) ──► môi trường số quốc gia
        │
        ▼
IIP Section C ◄── shipment / inventory (cân đối SX–tiêu thụ–tồn)
        ▲
        │  feature tương tác
online_revenue_ratio × IIP_growth
        ▲
        │
Adoption & kênh số ──► Online revenue ──► Digital VA
        ▲
        │
BCTC (margin, assets, labour) ──► ratios & benchmark percentiles
```

### 9.2. Các liên hệ “được phép” trong project

| Liên hệ | Ý nghĩa | Cách dùng |
|---------|---------|-----------|
| IIP ← lags IIP, rolling IIP | Xu hướng và quán tính sản xuất | ARIMA / features |
| IIP ← INDIGO lag | Môi trường số quốc gia có thể gắn nhịp SX | Feature (không phải nhân quả đã chứng minh) |
| IIP ← MEI peer lag | Chu kỳ sản xuất vùng đối tác / cầu ngoài | Feature `OECD_PEER` only |
| IIP_growth × online_revenue_ratio | Tương tác **KTS–SXCN** | Cross feature |
| Listing → online revenue → Digital VA | Đóng góp kinh tế số cấp DN | Metrics M3/M6 |
| BCTC → ROA/ROE/… → percentile | Cạnh tranh tài chính trong peer VSIC | M10 / Module 5 |
| Digital presence → adoption → Digital VA | Số hóa kênh làm tăng phần “tiết kiệm × adoption” | M2/M4/M6 |

### 9.3. Các liên hệ **cấm nhầm**

| Nhầm lẫn | Vì sao sai |
|----------|------------|
| MEI EA20 = IIP Việt Nam | Peer chỉ là chỉ báo phụ |
| Digital VA = doanh thu online | VA đã nhân biên và trừ đầu tư |
| Digital VA = IIP | Khác đơn vị, khác đối tượng (DN vs ngành) |
| Percentile mẫu 10 DN = chuẩn ngành quốc gia | n nhỏ, prototype |
| Fallback = số “thật mới nhất” | Fallback là dự phòng có nguồn, phải gắn provenance |
| Step-hold năm→tháng = quan sát tháng thật | Chỉ là kỹ thuật khớp tần suất |

### 9.4. Feature engineering — ý nghĩa kinh tế từng nhóm

| Nhóm | Ví dụ | Ý nghĩa |
|------|-------|---------|
| Lag | IIP_lag2m, INDIGO_lag… | Truyền dẫn theo thời gian |
| Rolling | IIP_roll3m, IIP_roll6m | Xu hướng trung hạn, giảm nhiễu tháng |
| Digital | adoption, channel diversity | Trạng thái số hóa |
| Cross | online_revenue_ratio × IIP_growth | Giả thuyết tương tác KTS–sản xuất |
| Financial | ROA, ROE, current | Năng lực tài chính gắn benchmark |

### 9.5. Dự báo IIP — ý nghĩa kinh tế (không chỉ “điểm số ML”)

Ba tầng mô hình (ARIMA, XGBoost, LSTM) cùng nhắm **IIP Section C** để:

- Đọc **chu kỳ sản xuất** ngắn hạn (3–6 tháng với LSTM).
- So sánh mô hình thống kê cổ điển vs ML vs DL trên cùng bài toán kinh tế.
- Đưa forecast lên dashboard **chồng lên chuỗi thật** — forecast là lớp diễn giải, không thay thế số GSO đã công bố.

Metric MAE / RMSE / MAPE đo **sai số dự báo**, không đo “mức độ số hóa”.

---

## 10. Case study kinh tế: Rạng Đông (RAL)

RAL (VSIC **2740** — thiết bị chiếu sáng) được chọn vì:

- Là DN chế tạo có **câu chuyện TMĐT / kênh số** rõ trong định hướng đề tài.
- Cho phép minh họa đủ chuỗi: phân ngành → BCTC → website/sàn → listing → online revenue → Digital VA → so peer cùng division (nếu đủ).

Ý nghĩa sư phạm: người đọc thấy **một DN chế tạo** đi từ sản xuất vật lý sang hiện diện số — đúng tinh thần Section C, không phải retailer thuần.

---

## 11. Nguyên tắc trung thực số liệu (phần của “ý nghĩa kinh tế”)

Trong kinh tế thực chứng, **số bịa làm hỏng diễn giải**. Project gắn nguyên tắc:

1. **Không invent** series GSO/OECD khi thiếu.
2. **Provenance** trên mọi chuỗi: live / fallback / seed / peer — phải đọc được nguồn.
3. **Peer OECD** chỉ cho forecast feature, không đóng vai số Việt Nam.
4. **Industry-ratio** chỉ khi có nguồn tỷ lệ; không nhân 15% “cho có”.
5. **Benchmark**: thiếu peer → null, không bịa median.
6. **UI**: thiếu metrics / artifact → banner / empty — không vẽ đường tăng trưởng giả.

Những nguyên tắc này bảo vệ **ý nghĩa kinh tế** của mọi biểu đồ và công thức phía trên.

---

## 12. Giới hạn và phần chưa đủ để kết luận kinh tế đầy đủ

Để không over-claim khi đọc kết quả platform:

| Hạng mục | Trạng thái ý niệm | Hệ quả diễn giải |
|----------|-------------------|------------------|
| Mẫu 10 DN | Prototype | Không suy ra toàn Section C |
| M7–M9 (logistics, thanh toán, XK số) | Thường thiếu nguồn crawl ổn định | Pillar khung còn trống hoặc proxy yếu |
| Cost_savings, Digital_investment trong Digital VA | Khó quan sát trực tiếp | Cần giả định tường minh hoặc tạm thời phần = 0 / thiếu |
| GRDP / VA ngành chính thức | Chưa đủ chuỗi trong phase sớm | M1 nghiêng về IIP |
| Industry-ratio TMĐT ngành | Có thể chưa gắn nguồn | Online revenue phụ thuộc listing |
| Causal claim “số hóa → tăng IIP” | Feature tương tác ≠ chứng minh nhân quả | Chỉ là tín hiệu thống kê cần kiểm định thêm |

---

## 13. Tóm tắt một trang — trước khi đụng code

1. **Đối tượng**: kinh tế số của **chế biến chế tạo** (VSIC Section C), không phải bán lẻ.  
2. **Nhịp ngành**: theo dõi bằng **IIP_C** (+ shipment/inventory khi có).  
3. **Hành vi DN**: hiện diện số → online revenue → **Digital VA** và năng suất lao động số.  
4. **Khung đo**: **VDEI M1–M10**.  
5. **Đối chiếu quốc tế**: INDIGO (VNM) + MEI peer (EA20) — đúng vai trò, không nhập nhằng.  
6. **Cạnh tranh**: ratio BCTC + percentile peer VSIC 2-digit trong mẫu.  
7. **Dự báo**: phục vụ đọc chu kỳ IIP; không thay số thống kê chính thức.  
8. **Trung thực nguồn** là điều kiện để mọi công thức còn mang ý nghĩa kinh tế.

Khi thay đổi bất kỳ công thức Digital VA, định nghĩa VDEI, hoặc cách dùng series OECD/GSO: cập nhật tài liệu này và `CONTEXT.md` (và ADR nếu là quyết định khó đảo ngược) **trước hoặc cùng lúc** với thay đổi logic.

