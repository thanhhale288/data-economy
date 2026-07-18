---
name: Manufacturing Data Economy
overview: Chuyển đổi proposal bán lẻ thành hệ thống web hoàn chỉnh cho ngành Công nghiệp chế biến, chế tạo (VSIC Section C), crawl GSO + phát hiện kênh TMĐT của ~10 DN niêm yết mẫu, tính chỉ số đóng góp kinh tế số, huấn luyện ML/DL dự báo xu hướng, và chuẩn bị nền tảng benchmark kiểu SingStat BITE.
todos:
  - id: scaffold
    content: "Scaffold project: Docker Compose, PostgreSQL, FastAPI, React, cấu trúc thư mục"
    status: completed
  - id: vsic-mapping
    content: Xây dựng bảng ánh xạ ISIC Section C ↔ VSIC 10-33 và seed 10 DN mẫu
    status: completed
  - id: gso-crawler
    content: "Implement GSO/NSO crawler: IIP (SDMX) + shipment/inventory (PX-Web E07.03/E07.04)"
    status: completed
  - id: oecd-crawler
    content: "Implement OECD SDMX: INDIGO@VNM + MEI_IP@EA20 peer; mark VNM MEI/BCI/ICT unavailable"
    status: completed
  - id: company-crawler
    content: "Crawl 10 DN niêm yết: metadata, website, BCTC có cấu trúc"
    status: pending
  - id: marketplace-crawler
    content: Phát hiện & scrape shop Shopee/TikTok + ML shop-matcher
    status: pending
  - id: digital-metrics
    content: "Tính chỉ số VDEI manufacturing: digital VA, online revenue estimate, industry share"
    status: pending
  - id: pipeline-clean
    content: Pipeline clean data + feature engineering (lag, rolling, digital features)
    status: pending
  - id: ml-models
    content: Huấn luyện ARIMA, XGBoost, LSTM — đánh giá MAE/RMSE/MAPE
    status: pending
  - id: web-dashboard
    content: "Frontend: Dashboard ngành, Company detail (Rạng Đông), Pipeline monitor, ML Lab"
    status: pending
  - id: benchmark-module
    content: "Module Benchmark kiểu SingStat BITE: form nhập + percentile so ngành"
    status: pending
  - id: proposal-update
    content: Cập nhật proposal Mục 4 với schema, chỉ tiêu, kết quả thực tế
    status: pending
isProject: false
---

# Kế hoạch dự án: Kinh tế số ngành Chế biến, Chế tạo

## 1. Nhận xét điều chỉnh proposal hiện tại

Proposal gốc ([Proposal-DataEconomy-Lê Thanh Hà.docx](Proposal-DataEconomy-Lê Thanh Hà.docx)) có nền tảng tốt về kiến trúc pipeline 4 tầng (CRISP-DM) nhưng **chưa đủ cho yêu cầu thực tiễn** của cô:


| Vấn đề trong proposal                    | Cần điều chỉnh                                                                                                                                                                                                                        |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Case study **bán lẻ** (VSIC Division 47) | Chuyển sang **chế biến, chế tạo** (VSIC Section C, mã 10–33)                                                                                                                                                                          |
| Chỉ crawl macro GSO + OECD               | Thêm **micro-level**: DN niêm yết, website, sàn TMĐT                                                                                                                                                                                  |
| Biến mục tiêu = tổng mức bán lẻ          | Biến mục tiêu = **IIP, giá trị gia tăng công nghiệp, doanh thu TMĐT DN**                                                                                                                                                              |
| Không đo kênh bán số                     | Thêm **phát hiện website riêng, Shopee, TikTok Shop**                                                                                                                                                                                 |
| Visualization = Apache Superset          | **Web app full-stack** (backend API + frontend dashboard)                                                                                                                                                                             |
| Không có benchmark DN                    | Chuẩn bị module **Benchmark My Performance** (tham chiếu [SingStat BITE](https://www.singstat.gov.sg/data-tools-services/business-insights-tool-for-enterprises-bite/benchmark-my-performance/retail-trade/wearing-apparel-footwear)) |
| File CSV 81 chỉ tiêu TMĐT bán lẻ         | **Tái cấu trúc** thành bộ chỉ tiêu VDEI cho manufacturing                                                                                                                                                                             |


---

## 2. Kiến trúc hệ thống tổng thể

```mermaid
flowchart TB
    subgraph sources [Nguồn dữ liệu]
        GSO[GSO PX-Web / SDMX]
        OECD[OECD SDMX API]
        Exchange[HOSE/HNX - DN niêm yết]
        FinReport[BCTC có cấu trúc]
        WebCrawl[Website / Shopee / TikTok]
    end

    subgraph pipeline [Data Pipeline]
        Ingest[Ingestion Layer]
        Clean[Clean & Harmonize]
        Feature[Feature Engineering]
        ML[ML/DL Training]
    end

    subgraph storage [PostgreSQL]
        Raw[(raw_data)]
        Staging[(staging)]
        Mart[(data_mart)]
        Model[(model_registry)]
    end

    subgraph app [Web Application]
        API[FastAPI Backend]
        FE[React Frontend]
        Bench[Benchmark Module]
    end

    sources --> Ingest --> Clean --> Feature --> ML
    Ingest --> Raw --> Staging --> Mart
    ML --> Model
    Mart --> API --> FE
    API --> Bench
```



**Tech stack đề xuất** (kế thừa proposal, bổ sung web app):

- **Crawl**: Playwright (GSO PX-Web), `requests` + `pandasdmx` (OECD), BeautifulSoup
- **Pipeline orchestration**: Prefect hoặc Apache Airflow (nhẹ hơn Spark cho quy mô ~10 DN)
- **DB**: PostgreSQL 16
- **Backend**: FastAPI + SQLAlchemy + Alembic migrations
- **Frontend**: React + Vite + Recharts/ECharts
- **ML/DL**: scikit-learn, XGBoost/LightGBM, PyTorch (LSTM/GRU)
- **Deploy**: Docker Compose (app + db + redis + worker)

---

## 3. Mục 4 chi tiết — Cấu trúc thu thập dữ liệu

### 3.1. Ánh xạ ngành ISIC ↔ VSIC (thay Division 47 → Section C)


| Mã ISIC Rev.4  | Mã VSIC 2018           | Diễn giải                                                      |
| -------------- | ---------------------- | -------------------------------------------------------------- |
| Section C      | Ngành cấp 1 - Mã C     | Công nghiệp chế biến, chế tạo                                  |
| Division 10–33 | Ngành cấp 2 - Mã 10–33 | Các nhóm ngành chế biến chế tạo                                |
| Class 4-digit  | Mã 4 chữ số            | Chi tiết (vd: 2740 = sản xuất thiết bị chiếu sáng → Rạng Đông) |


### 3.2. Ba luồng thu thập song song

#### Luồng A — Macro ngành (GSO, tự động)


| Dataset                           | Chỉ tiêu                           | Tần suất | Phương pháp                                      |
| --------------------------------- | ---------------------------------- | -------- | ------------------------------------------------ |
| IIP (Chỉ số sản xuất công nghiệp) | IIP Section C, theo Division 10–33 | Tháng    | SDMX XML từ `nsdp.gso.gov.vn` hoặc PX-Web scrape |
| Chỉ số xuất hàng công nghiệp      | Shipment index manufacturing       | Tháng    | PX-Web                                           |
| Chỉ số tồn kho công nghiệp        | Inventory index                    | Tháng    | PX-Web                                           |
| GRDP/GDP theo ngành               | Giá trị gia tăng công nghiệp       | Quý/Năm  | PX-Web                                           |
| Số DN, lao động, doanh thu ngành  | Thống kê doanh nghiệp công nghiệp  | Năm      | PX-Web / Niên giám                               |


**GSO PX-Web tables cần khai thác** (xác nhận khi implement):

- `IIP` — Index of Industrial Production by VSIC
- `Tinh hinh san xuat cong nghiep` — Báo cáo SXCN hàng tháng
- `Ket qua hoat dong kinh doanh` — KQKD doanh nghiệp theo ngành

#### Luồng B — Micro doanh nghiệp niêm yết (~10 DN mẫu)

**Danh sách DN mẫu đề xuất** (đại diện đa ngành con):


| Mã CK | Tên                   | VSIC                       | Lý do chọn            |
| ----- | --------------------- | -------------------------- | --------------------- |
| RAL   | Rạng Đông             | 2740 (thiết bị chiếu sáng) | Ví dụ cô nêu, có TMĐT |
| HPG   | Hòa Phát              | 2410 (sắt thép)            | DN lớn, có website    |
| VNM   | Vinamilk              | 1050 (sữa)                 | Bán online mạnh       |
| FPT   | FPT (electronics mfg) | 2620                       | Chuyển đổi số cao     |
| GVR   | Cao su Việt Nam       | 2211                       | Ngành truyền thống    |
| DGC   | Đức Giang Chemicals   | 2011                       | Hóa chất              |
| MSN   | Masan                 | 1071 (thực phẩm)           | Đa kênh bán           |
| PNJ   | PNJ                   | 3211 (trang sức)           | Bán lẻ + TMĐT         |
| REE   | REE Electric          | 2710                       | Thiết bị điện         |
| BWE   | Bình Minh Plastics    | 2220                       | Nhựa                  |


**Dữ liệu crawl từng DN:**


| Nhóm                    | Trường dữ liệu                                  | Nguồn                         | Tự động?                  |
| ----------------------- | ----------------------------------------------- | ----------------------------- | ------------------------- |
| Thông tin cơ bản        | Tên, mã CK, VSIC, website chính thức            | HOSE/HNX API, Vietstock       | Có                        |
| BCTC có cấu trúc        | Doanh thu, LNST, tài sản, vốn CSH, chi phí      | BCTC niêm yết (PDF/XBRL)      | Bán tự động (PDF extract) |
| Hiện diện số            | Có website bán hàng? URL, có giỏ hàng/checkout? | HTTP crawl + rule-based       | Có                        |
| Sàn TMĐT                | Có shop Shopee/TikTok/Lazada? URL shop          | Search API + scrape shop page | Có (ML hỗ trợ match)      |
| Ước lượng bán online    | Số lượng đã bán, rating, giá TB                 | Scrape listing sản phẩm       | Có (ước lượng)            |
| Doanh thu TMĐT (nếu có) | Tỷ trọng online trong BCTC/AR                   | BCTC thường niên              | Bán tự động               |


#### Luồng C — Quốc tế (OECD, tự động)


| Dataset OECD                      | Vai trò                | Mapping        |
| --------------------------------- | ---------------------- | -------------- |
| MEI — Industrial Production Index | Leading indicator      | ISIC Section C |
| INDIGO (Digital trade openness)   | Leading indicator      | Toàn ngành     |
| ICT Investment by industry        | Digital adoption proxy | ISIC C         |
| Business Confidence Index         | Leading indicator      | Manufacturing  |


**Đồng bộ tần suất**: OECD Quý → nội suy tháng (giữ từ proposal gốc).

### 3.3. Bộ chỉ tiêu VDEI cho Manufacturing (tái cấu trúc từ CSV)

Chuyển 10 pillar trong [File hướng dẫn crawl data - đề tài chỉ số kinh tế số - Trang tính1.csv](File hướng dẫn crawl data - đề tài chỉ số kinh tế số - Trang tính1.csv) sang ngữ cảnh chế biến chế tạo:


| Pillar | Tên mới (Manufacturing) | Chỉ tiêu cốt lõi (Tier 1)                                                |
| ------ | ----------------------- | ------------------------------------------------------------------------ |
| M1     | Quy mô & hiệu quả SXCN  | IIP Section C, giá trị gia tăng công nghiệp, tốc độ tăng GRDP ngành      |
| M2     | Chuyển đổi số DN        | % DN có website, % DN bán trên sàn, % DN dùng ERP/IoT                    |
| M3     | Doanh thu TMĐT ngành SX | Doanh thu online ước tính / tổng doanh thu ngành                         |
| M4     | Kênh bán số             | Tỷ trọng website riêng vs marketplace vs social commerce                 |
| M5     | Hiệu quả số hóa         | Doanh thu/lao động, digital revenue per worker                           |
| M6     | Đóng góp KTS            | Digital value-added = f(doanh thu TMĐT, chi phí số, productivity uplift) |
| M7     | Hạ tầng & logistics số  | % DN dùng logistics TMĐT, thời gian giao hàng                            |
| M8     | Thanh toán số B2B/B2C   | % giao dịch qua cổng thanh toán online                                   |
| M9     | Xuất khẩu số            | % đơn hàng qua kênh online quốc tế                                       |
| M10    | Năng lực cạnh tranh số  | So sánh percentile với ngành (benchmark module)                          |


**Công thức ước lượng giá trị gia tăng kinh tế số (DN level):**

```
Digital_VA_estimate = 
  (Estimated_online_revenue × Digital_margin_proxy) 
  + (Cost_savings_from_digital × Adoption_score)
  - Digital_investment_amortized

Trong đó:
- Estimated_online_revenue = Σ(unit_price × units_sold) từ scrape Shopee/TikTok
  HOẶC nội suy từ tỷ lệ TMĐT/ngành × doanh thu DN (nếu không scrape được)
- Digital_margin_proxy = lấy từ BCTC (gross margin) hoặc ngành benchmark
- Adoption_score = weighted(C01 website + C06 marketplace + C05 social)
```

### 3.4. Schema database chính

```mermaid
erDiagram
    companies ||--o{ financial_reports : has
    companies ||--o{ digital_presence : has
    companies ||--o{ marketplace_listings : has
    companies ||--o{ digital_metrics : has
    vsic_codes ||--o{ companies : classifies
    gso_macro ||--o{ vsic_codes : belongs_to
    oecd_indicators ||--o{ vsic_codes : maps_to
    model_predictions ||--o{ gso_macro : forecasts

    companies {
        int id PK
        string stock_code
        string name
        string vsic_code FK
        string website_url
        bool has_ecommerce_site
        json digital_channels
    }
    digital_presence {
        int id PK
        int company_id FK
        string channel_type
        string url
        bool is_active
        datetime crawled_at
    }
    marketplace_listings {
        int id PK
        int company_id FK
        string platform
        string product_name
        float price
        int units_sold_est
        float revenue_est
    }
    digital_metrics {
        int id PK
        int company_id FK
        date period
        float online_revenue_est
        float digital_va_contribution
        float industry_share_pct
    }
    gso_macro {
        int id PK
        string vsic_code
        string indicator_code
        date period
        float value
        string unit
    }
```



---

## 4. Pipeline xử lý & ML/DL

### 4.1. Clean data (3 kịch bản từ proposal + bổ sung)

1. **Missing values**: median (gap ngắn), linear interpolation (gap dài) — giữ từ proposal
2. **Outlier detection**: IQR/Z-score cho scrape marketplace (giá/số lượng bất thường)
3. **Entity resolution**: ML classifier (TF-IDF + cosine similarity) match tên shop Shopee ↔ tên DN niêm yết
4. **VSIC mapping**: bảng ánh xạ 1:1 ISIC Section C ↔ VSIC 10–33

### 4.2. Feature engineering


| Nhóm feature | Biến                                      | Mục đích                          |
| ------------ | ----------------------------------------- | --------------------------------- |
| Lag (macro)  | CCI_lag1q, INDIGO_lag1q, IIP_lag2m        | Truyền dẫn kinh tế quốc tế → SXCN |
| Rolling      | IIP_roll3m, IIP_roll6m                    | Xu hướng trung hạn                |
| Digital      | digital_adoption_score, channel_diversity | Mức số hóa DN                     |
| Cross        | online_revenue_ratio × IIP_growth         | Tương tác KTS-SXCN                |
| Financial    | ROA, ROE, current_ratio (từ BCTC)         | Input benchmark                   |


### 4.3. Mô hình huấn luyện (3 tầng như proposal)


| Tier        | Model            | Target variable               | Input                          |
| ----------- | ---------------- | ----------------------------- | ------------------------------ |
| Statistical | ARIMA/SARIMAX    | IIP Section C (tháng)         | IIP history + OECD lags        |
| ML          | XGBoost/LightGBM | IIP + digital_va_growth       | Tabular features               |
| DL          | LSTM/GRU         | Multi-step forecast 3–6 tháng | Sequence IIP + digital metrics |


**Đánh giá**: MAE, RMSE, MAPE — walk-forward validation (train 2018–2023, test 2024–2025).

**ML bổ sung cho crawl**:

- **Shop matcher**: Binary classifier xác nhận shop Shopee/TikTok thuộc DN (precision > 90%)
- **Product categorizer**: Phân loại sản phẩm theo VSIC 4-digit từ tên SP
- **Trend detector**: Time series anomaly detection (Isolation Forest / LSTM autoencoder) trên IIP

---

## 5. Web application — các module

### Module 1: Dashboard tổng quan ngành

- Biểu đồ IIP, giá trị gia tăng, xu hướng dự báo
- Heatmap đóng góp KTS theo nhóm ngành VSIC
- So sánh OECD leading indicators vs GSO lagging

### Module 2: Doanh nghiệp (~10 DN mẫu)

- Profile từng DN: kênh bán số (website/Shopee/TikTok), ước lượng doanh thu online
- Ví dụ **Rạng Đông**: website `rangdong.com.vn`, shop Shopee, đóng góp vào ngành 2740
- Timeline crawl history + data quality score

### Module 3: Pipeline monitor

- Trạng thái job crawl (GSO, marketplace, OECD)
- Log lỗi, lần crawl cuối, số record mới

### Module 4: ML Lab

- So sánh 3 model (ARIMA vs XGBoost vs LSTM)
- Biểu đồ forecast vs actual
- Feature importance

### Module 5: Benchmark (Phase 2 — tham chiếu SingStat BITE)

- Form nhập: Doanh thu, LN trước thuế, số NV, chi phí (hàng hóa, thuê, lương)
- Output: ROA, ROE, Current Ratio, Equity Ratio + **percentile so với ngành**
- Nội suy từ BCTC công ty chưa đủ field → dùng tỷ lệ ngành từ GSO

---

## 6. Lộ trình triển khai (~18 tuần / 1 học kỳ)

### Giai đoạn 1: Nền tảng & Macro data (Tuần 1–5)

- Scaffold project: Docker Compose, PostgreSQL, FastAPI skeleton, React shell
- Implement GSO crawler (IIP, shipment, inventory — Section C)
- Implement OECD SDMX ingestion
- VSIC/ISIC mapping table
- DB migrations + seed data

### Giai đoạn 2: Enterprise crawl & Digital detection (Tuần 6–10)

- Crawl danh sách 10 DN niêm yết + metadata
- Website detector (có checkout/giỏ hàng?)
- Shopee/TikTok shop finder + product scraper
- BCTC PDF extractor (doanh thu, chi phí cấu trúc)
- Shop-matcher ML model
- Tính digital metrics per company

### Giai đoạn 3: Clean, Features & ML (Tuần 11–14)

- Data cleaning pipeline (Prefect/Airflow DAGs)
- Feature engineering
- Train & evaluate ARIMA, XGBoost, LSTM
- Model registry + API endpoints

### Giai đoạn 4: Web hoàn thiện & Demo (Tuần 15–17)

- Dashboard modules 1–4
- Company detail pages (Rạng Đông case study)
- Pipeline monitor UI
- Integration testing end-to-end

### Giai đoạn 5: Benchmark & Báo cáo (Tuần 18)

- Benchmark module (SingStat BITE style)
- Cập nhật proposal Mục 4 với kết quả thực tế
- Demo presentation + documentation

---

## 7. Cấu trúc thư mục dự án đề xuất

```
ai-in-data-economy/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   └── alembic/          # DB migrations
├── crawlers/
│   ├── gso/              # PX-Web + SDMX
│   ├── oecd/             # SDMX API
│   ├── marketplace/      # Shopee, TikTok
│   ├── companies/        # Stock exchange, websites
│   └── financial/        # BCTC parser
├── pipeline/
│   ├── cleaning/
│   ├── features/
│   └── dags/             # Prefect/Airflow flows
├── ml/
│   ├── models/           # ARIMA, XGBoost, LSTM
│   ├── shop_matcher/
│   └── evaluation/
├── frontend/
│   └── src/
│       ├── pages/        # Dashboard, Company, ML, Benchmark
│       └── components/
├── data/
│   ├── mappings/         # VSIC-ISIC table
│   └── seeds/            # 10 sample companies
└── docs/
    └── proposal-v2.md    # Proposal cập nhật Mục 4
```

---

## 8. Rủi ro & giảm thiểu


| Rủi ro                                   | Giảm thiểu                                                |
| ---------------------------------------- | --------------------------------------------------------- |
| GSO PX-Web thay đổi UI                   | Dùng SDMX XML endpoint khi có; fallback Playwright        |
| Shopee/TikTok chặn scrape                | Rate limiting, rotate UA; dùng official search API nếu có |
| Shop không match đúng DN                 | ML matcher + manual QA cho 10 DN mẫu                      |
| BCTC PDF khó parse                       | Ưu tiên DN có BCTC HTML/XBRL; nội suy cho field thiếu     |
| Không có doanh thu TMĐT riêng trong BCTC | Ước lượng từ scrape marketplace + tỷ lệ ngành             |


---

## 9. Kết quả deliverable cuối học kỳ

1. **Web app chạy được** với 4 module chính (Dashboard, DN, Pipeline, ML Lab)
2. **Database** chứa macro GSO/OECD + micro 10 DN + digital presence
3. **Pipeline tự động** crawl định kỳ (cron/Prefect schedule)
4. **3 model** đã train, so sánh metric, API forecast
5. **Case study Rạng Đông** đầy đủ: kênh bán, ước lượng online, đóng góp ngành
6. **Proposal v2** — Mục 4 cập nhật với schema, chỉ tiêu, công thức thực tế
7. **Benchmark module** (prototype) nhập liệu → so sánh percentile ngành

