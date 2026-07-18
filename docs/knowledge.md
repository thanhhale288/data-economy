# Knowledge — Thuật ngữ đã hỏi trong dự án

File này ghi lại các keyword/thuật ngữ đã được giải thích khi hỏi về project **Kinh tế số ngành Chế biến, Chế tạo**. Giọng viết hướng tới người mới, không giả định biết trước về data/crawl.

Nguồn bổ sung khi cần chi tiết domain/công thức: `CONTEXT.md`, `docs/plan.md`, `docs/proposal-v2.md`.

---

## 1. Phân ngành & dữ liệu nền

### ISIC Section C

**ISIC** = hệ thống phân ngành kinh tế quốc tế (Liên Hợp Quốc).  
**Section C** = ngành cấp 1 **Manufacturing — Công nghiệp chế biến, chế tạo**.

OECD thường dùng ISIC Section C. Trong project, Section C được map sang VSIC của Việt Nam.

### VSIC 10–33

**VSIC** = Hệ thống ngành kinh tế Việt Nam.  
Mã **10–33** là các ngành cấp 2 thuộc chế biến, chế tạo (thực phẩm, dệt, hóa chất, thép, điện tử, thiết bị điện…).

Mã càng dài càng chi tiết, ví dụ:

- `C` — ngành cấp 1
- `27` — thiết bị điện
- `2740` — thiết bị chiếu sáng (Rạng Đông)

**“ISIC Section C ↔ VSIC 10–33”** = bảng ánh xạ giữa chuẩn quốc tế và chuẩn Việt Nam cho cùng lĩnh vực chế biến chế tạo.

### Schema DB

**Schema** = bản thiết kế cấu trúc database: có bảng nào, cột gì, kiểu dữ liệu, khóa chính/ngoại, quan hệ giữa bảng.

Ví dụ trong project: `vsic_codes`, `companies`, `gso_macro`, `oecd_indicators`, `financial_reports`, `digital_presence`, `marketplace_listings`.

### Migration

**Migration** = phiên bản thay đổi schema theo thời gian (thêm bảng, thêm cột, đổi ràng buộc…). Giúp mọi máy (dev/test/prod) cùng một cấu trúc DB, có lịch sử và có thể nâng/hạ phiên bản có kiểm soát — thay vì `create_all()` ad-hoc.

### Alembic

**Alembic** = công cụ migration cho SQLAlchemy (Python). Trong stack: FastAPI + SQLAlchemy + Alembic + PostgreSQL. Lệnh điển hình: `alembic upgrade head`.

---

## 2. Crawl / nguồn macro (Task 3–4)

### Crawl / ingestion

Lấy dữ liệu từ nguồn ngoài (API/file), parse thành cấu trúc, rồi ghi vào DB.

### Macro data

Chỉ số vĩ mô ngành/quốc gia (IIP, BCI…), không phải số của từng doanh nghiệp.

### GSO / NSO

Cơ quan thống kê Việt Nam — nguồn số nội địa. Trong docs/code có thể gặp cả tên GSO và NSO/NSDP host mới.

### NSDP

**National Summary Data Page** — cổng công bố dữ liệu thống kê chuẩn SDMX (ví dụ file IIP).

### OECD

Organisation for Economic Co-operation and Development — nguồn chỉ số quốc tế để so sánh / leading indicator.

### SDMX

**Statistical Data and Metadata eXchange** — chuẩn trao đổi dữ liệu thống kê.

- **SDMX-XML**: dạng XML (GSO/NSDP IIP dùng kiểu này).
- **SDMX-JSON**: dạng JSON (OECD Data Explorer REST API dùng kiểu này).

### Dataflow

“Bảng/dataset” trên API OECD (ví dụ `DSD_STES@DF_INDSERV`).

### Series / observation

**Series** = một chuỗi thời gian.  
**Observation** = một điểm trong chuỗi (`TIME_PERIOD` + giá trị `OBS_VALUE`).

### Dimension

Trục lọc trong SDMX: quốc gia, ngành, tần suất, chỉ tiêu…

Các dimension hay gặp:


| Dimension   | Ý nghĩa                         |
| ----------- | ------------------------------- |
| `INDICATOR` | Mã chỉ tiêu                     |
| `ACTIVITY`  | Ngành hoạt động (vd. Section C) |
| `REF_AREA`  | Quốc gia/vùng (vd. `VNM`)       |
| `FREQ`      | Tần suất (`M`/`Q`/`A`)          |


### IIP

**Index of Industrial Production** — Chỉ số sản xuất công nghiệp. Trong project: `IIP_C` cho Section C; biến mục tiêu dự báo chính của ML Lab.

### Shipment index

Chỉ số **xuất hàng** công nghiệp (hàng đã xuất khỏi nhà máy). Plan: `SHIPMENT_C`. File SDMX IIP hiện không có → cần nguồn khác (PX-Web).

### Inventory index

Chỉ số **tồn kho** công nghiệp. Plan: `INVENTORY_C`. Tương tự shipment: chưa có trong file IIP SDMX.

### MEI / MEI_IP

**MEI** = Main Economic Indicators (OECD).  
**MEI_IP** = Industrial Production Index của OECD (leading / so sánh quốc tế).

### BCI

**Business Confidence Index** — chỉ số tin tưởng kinh doanh (manufacturing).

### INDIGO

Digital Trade Openness Index — độ mở thương mại số (leading feature).

### ICT Investment

Đầu tư ICT — proxy mức độ số hóa (trong code: `ICT_INVEST`).

### Leading vs lagging

- **Leading**: báo trước xu hướng (nhiều chỉ số OECD).
- **Lagging**: phản ánh kết quả đã xảy ra (GSO IIP thường mang tính này).

### Frequency (M / Q / A)

Tần suất chuỗi: **tháng / quý / năm**.

### Nội suy (interpolation)

Biến chuỗi quý thành tháng bằng nội suy tuyến tính giữa các điểm neo (trong OECD client: Jan/Apr/Jul/Oct). Tháng/năm không nội suy kiểu đó.

### Fallback / fixture

File CSV/JSON đã commit sẵn, chỉ dùng khi live fail — **không bịa số ngẫu nhiên**. Có gắn nguồn (`GSO_FALLBACK`, fixture OECD…).

### Upsert

Có rồi thì update, chưa có thì insert. Crawl lại không nhân đôi bản ghi (idempotent theo khóa unique).

### httpx

Thư viện HTTP Python dùng để GET URL.

### Parse

Đọc XML/JSON thô thành record có cấu trúc để lưu DB.

### Provenance / source

Ghi nguồn gốc số liệu (`GSO`, `GSO_FALLBACK`, `seed:…`, `fallback:…`, `live`…).

### Wire PX-Web (cho shipment / inventory)

**Wire** = “nối dây”: viết code để hệ thống thật sự lấy dữ liệu từ nguồn đó.  
**PX-Web** = giao diện/web thống kê (chọn bảng → ngành → tháng → số).  
“Wire PX-Web cho shipment/inventory” = nối crawler với PX-Web để lấy xuất hàng & tồn kho vì file SDMX IIP không có hai series đó.

---

## 3. Scrape & lấy web

### Scrape

Máy **mở trang web như người dùng**, rồi **chép chữ/số trên trang** về.

Khác API/SDMX: API/SDMX là xin file/bảng chuẩn sẵn; scrape là đọc HTML/UI. Task marketplace (Shopee/TikTok) thường scrape; Task 3–4 GSO/OECD ưu tiên SDMX/API.

### Crawl live

Lúc chạy, máy **lên mạng lấy dữ liệu mới** từ website/API. Khác seed/fallback (đọc file sẵn trong repo).

---

## 4. Phase 2 — doanh nghiệp & kênh số

### Provenance seed / fallback

Mọi số micro (BCTC, listing, digital presence…) gắn nhãn nguồn:


| Tầng     | Nghĩa                                | Ví dụ                   |
| -------- | ------------------------------------ | ----------------------- |
| Live     | Lấy web/API thật lúc chạy            | `live`, URL http…       |
| Seed     | Dữ liệu mẫu 10 DN trong repo         | `seed:…`, `SEED_SOURCE` |
| Fallback | Dự phòng khi live chết, vẫn có nguồn | `fallback:data/raw/...` |


“Pipeline + test + provenance seed/fallback” = luồng chạy được, có test, số nào cũng biết từ đâu — **chưa** đồng nghĩa crawl live đầy đủ.

### Detector

Bộ phát hiện website bán hàng (`website_detector`): đọc HTML, rule/từ khóa (`giỏ hàng`, `checkout`…) → `has_ecommerce_site`, `has_checkout`.

### OR seed

Logic kiểu: `kết_quả_live OR cờ_trong_seed`.  
Nếu live = không nhưng seed = có → DB vẫn ghi có. Có thể **làm méo** ý nghĩa detector (không còn phản ánh đúng trang web thật).

### Matcher (shop matcher)

Bộ ghép shop trên sàn ↔ doanh nghiệp (fuzzy + alias; mặc định ngưỡng **0.65** theo `CONTEXT.md`).

### Ngưỡng (threshold)

Điểm giống nhau tối thiểu để được coi là match. Dưới ngưỡng → **không gắn** DN với shop.

### Seed bypass ngưỡng

Shop/URL đã có trong seed được gắn DN luôn (`is_match=True`, `match_source=seed_known_url`), **không bắt buộc** vượt 0.65. Shop tìm mới phải qua `evaluate_discovered_shop` và ngưỡng.

### Listing marketplace (marketplace listing)

**Listing** = **một dòng sản phẩm** trên sàn TMĐT (Shopee, TikTok, Lazada…).

Ví dụ đời thường: trên Shopee bạn thấy “Đèn LED 12W — 89.000đ — đã bán 1.2k”. Đó là **một listing**.

Trong project, mỗi listing lưu vào bảng `marketplace_listings`, gắn với một DN, thường gồm:

- giá (`price`)
- ước lượng đã bán (`units_sold`)
- ước lượng doanh thu (`price × units_sold`)
- nền tảng / shop liên quan
- provenance (`live` / `seed` / `fallback`)

Phân biệt nhanh:

| Khái niệm | Là gì |
|-----------|--------|
| **Shop** | Cửa hàng trên sàn (cả gian hàng) |
| **Digital presence** | Kênh số đã xác nhận (website/Shopee/TikTok…) |
| **Marketplace listing** | **Từng sản phẩm** trong shop dùng để ước doanh thu online |

Online revenue ước lượng ≈ tổng các listing marketplace (không tính listing kiểu `platform=website` trong một số bước Task 9).

### Industry-ratio (tỷ lệ ngành)

**Industry-ratio** = tỷ lệ “doanh thu TMĐT / tổng doanh thu” **của cả ngành** (không phải của từng DN), lấy từ nguồn thống kê (ví dụ VECOM/GSO) khi có.

Cách dùng dự kiến khi **không có listing sản phẩm**:

```text
online_revenue_est ≈ industry_ratio × doanh_thu_BCTC
```

Ví dụ: DN doanh thu 100 tỷ, tỷ lệ ngành TMĐT = 5% → ước online ≈ 5 tỷ.

**“Industry-ratio có nguồn chưa gắn”** nghĩa là:

- Plan/CONTEXT **cho phép** dùng cách này khi thiếu listing
- Nhưng hiện **chưa gắn** một tỷ lệ có nguồn thật vào code (`SOURCED_INDUSTRY_ECOMMERCE_RATIO = None`)
- Không được bịa số kiểu ×0.15 im lặng
- Vì vậy nếu không có listing → `online_revenue_est = 0` + log (không invent)

### Online revenue phụ thuộc listing seed nếu không scrape được

Thứ tự thực tế gần như:

1. **Scrape live** Shopee/TikTok được → dùng listing live  
2. Không scrape được → dùng **listing trong seed/fallback** (số mẫu đã chuẩn bị)  
3. DN không có listing nào dùng được → **không** tự nhân tỷ lệ ngành (vì ratio chưa gắn nguồn) → online rev = 0  

Vì Phase 2 scrape live thường fail/block, **số online revenue bạn thấy phần lớn đến từ listing seed**, không phải doanh thu TMĐT đã kiểm toán từ sàn thật.

Một câu nhớ: **muốn có online rev thì cần listing; listing thật khó lấy thì dùng seed; tỷ lệ ngành chỉ là cửa dự phòng chưa mở vì chưa có nguồn gắn.**

---

## 5. Công cụ & Git

### Upstream (Git)

Nhánh/remote “phía trên” mà nhánh local đang theo dõi (ví dụ trên GitHub).  
“Không có upstream” ≈ nhánh local chưa gắn remote để `push`/`pull` chính thức.  
(`git push -u origin HEAD` thường là lần đầu nối upstream.)

### Homebrew

Trình quản lý phần mềm bằng dòng lệnh trên macOS (và Linux). Ví dụ: `brew install git`, `brew install python`.

### BMP (mã chứng khoán)

Trong ngữ cảnh project này, **BMP** thường là **mã HOSE thật của CTCP Nhựa Bình Minh** (thương hiệu nhựa Bình Minh).

Lưu ý:

- Mã HOSE **BMP** = CTCP Nhựa Bình Minh (VSIC 2220) — nằm trong 10 DN mẫu.
- **Không** nhầm với **BWE** (Biwase / nước) hay đuôi file ảnh `.bmp`.

### Fetch

**Fetch** = “đi lấy về”: chương trình gọi mạng (HTTP GET…) hoặc đọc nguồn, rồi mang dữ liệu về để parse.

Khác scrape một chút về cách nói:

- **Fetch** nhấn mạnh hành động *lấy response* (file JSON/XML, API, trang…)
- **Scrape** nhấn mạnh *đọc nội dung trang web* để chép số/chữ

Trong code hay gặp: `fetch_gso_iip`, `fetch_bctc`, `fetch_shopee_listings`, `fetch_oecd_indicators` — đều là hàm “đi lấy dữ liệu về”.

Một câu nhớ: **fetch = gọi nguồn và mang về; parse = đọc hiểu; enrich = gắn vào hồ sơ.**

### Trace

**Trace** = “lần theo dấu vết”: đi theo một đường đi từ đầu đến cuối để xem chuyện gì xảy ra.

Trong project hay gặp theo vài nghĩa gần nhau:

| Cách nói | Ý nghĩa đời thường |
|----------|-------------------|
| **Trace call chain** | Lần theo chuỗi hàm gọi nhau, ví dụ từ GSO crawl → lưu DB → API → ML prediction |
| **Stack trace** | Khi lỗi, danh sách “đang đứng ở hàm nào → gọi từ đâu” để debug |
| **Replay a captured trace** | Giữ lại request/payload thật rồi chạy lại để tái hiện bug |

Một câu nhớ: **trace = lần theo đường đi của dữ liệu hoặc của lời gọi hàm, không phải tự sinh số mới.**

---

## 6. Cách dùng file này

- Hỏi thêm keyword → **bổ sung vào đúng mục** (hoặc thêm mục mới), giữ giọng giải thích cho người mới.
- Không thay `CONTEXT.md`: file đó là ubiquitous language / công thức; `docs/knowledge.md` là **sổ tay giải thích** từ các câu hỏi học thuật ngữ.
- Khi thuật ngữ đã ổn định trong domain, có thể đồng bộ định nghĩa ngắn vào `CONTEXT.md` qua skill domain-modeling.

