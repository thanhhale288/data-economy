# Đề xuất Đề tài v2 — Kinh tế số ngành Chế biến, Chế tạo

## 4. PHƯƠNG PHÁP NGHIÊN CỨU & KIẾN TRÚC HỆ THỐNG (Cập nhật)

### 4.1. Tầng Thu thập dữ liệu (Data Ingestion Layer)

Hệ thống thu thập theo **3 luồng song song**:

#### Luồng A — Macro ngành (GSO)
| Dataset | Chỉ tiêu | Tần suất | Công cụ |
|---------|----------|----------|---------|
| IIP | Chỉ số SXCN Section C | Tháng | SDMX XML (`nsdp.nso.gov.vn`) |
| Shipment | Chỉ số xuất hàng công nghiệp | Tháng | PX-Web / fallback |
| Inventory | Chỉ số tồn kho công nghiệp | Tháng | PX-Web / fallback |

#### Luồng B — Micro doanh nghiệp niêm yết
| Dữ liệu | Nguồn | Phương pháp |
|---------|-------|-------------|
| Metadata 10 DN | HOSE/HNX seed | JSON seed + HTTP verify |
| BCTC có cấu trúc | BCTC niêm yết | PDF extract / seed |
| Website bán hàng | HTTP crawl | Rule-based (checkout detection) |
| Shop Shopee/TikTok | Marketplace scrape | ML shop-matcher (fuzzy + TF-IDF) |
| Ước lượng doanh thu online | Product listings | Σ(price × units_sold) |

**DN mẫu**: RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BWE

#### Luồng C — Quốc tế (OECD)
| Dataset | Vai trò | Mapping |
|---------|---------|---------|
| MEI Industrial Production | Leading indicator | ISIC Section C |
| Business Confidence Index | Leading indicator | Manufacturing |
| INDIGO | Digital trade openness | Toàn ngành |

### 4.2. Tầng Tiền xử lý & Lưu trữ

- **Database**: PostgreSQL 16
- **Schema**: companies, financial_reports, digital_presence, marketplace_listings, digital_metrics, gso_macro, oecd_indicators, model_predictions, pipeline_jobs
- **Xử lý missing**: median (gap ngắn), linear interpolation (gap dài)
- **Outlier**: IQR cho dữ liệu marketplace
- **Đồng bộ tần suất**: OECD Quý → nội suy Tháng
- **Ánh xạ ngành**: ISIC Section C ↔ VSIC 10–33 (bảng `vsic_codes`)

### 4.3. Tầng Trích chọn đặc trưng

| Nhóm | Biến | Mục đích |
|------|------|----------|
| Lag | CCI_lag1q, INDIGO_lag1q, IIP_lag2m | Truyền dẫn kinh tế |
| Rolling | IIP_roll3m, IIP_roll6m | Xu hướng trung hạn |
| Digital | digital_adoption_score, channel_diversity | Mức số hóa DN |
| Cross | online_revenue_ratio × IIP_growth | Tương tác KTS-SXCN |
| Financial | ROA, ROE, current_ratio | Benchmark input |

### 4.4. Tầng Huấn luyện AI

| Tier | Model | Target | Metrics |
|------|-------|--------|---------|
| Statistical | ARIMA(1,1,1) | IIP Section C | MAE, RMSE, MAPE |
| ML | XGBoost | IIP + features | MAE, RMSE, MAPE |
| DL | LSTM (32 units) | Multi-step 3–6 tháng | MAE, RMSE, MAPE |

**ML bổ sung cho crawl**:
- Shop Matcher: fuzzy matching tên DN ↔ shop (threshold 0.65)
- Product Categorizer: phân loại VSIC từ tên sản phẩm

### 4.5. Bộ chỉ tiêu VDEI Manufacturing

| Pillar | Chỉ tiêu cốt lõi |
|--------|------------------|
| M1 | IIP Section C, giá trị gia tăng công nghiệp |
| M2 | % DN có website, bán trên sàn |
| M3 | Doanh thu TMĐT / tổng doanh thu ngành |
| M4 | Tỷ trọng website vs marketplace vs social |
| M5 | Doanh thu/lao động, digital revenue per worker |
| M6 | Digital VA = f(online_revenue, margin, adoption) |
| M7–M9 | Logistics số, thanh toán, xuất khẩu số |
| M10 | Percentile benchmark vs ngành |

**Công thức Digital VA (DN level)**:
```
Digital_VA = (Online_revenue × Gross_margin) + (Cost_savings × Adoption_score) - Digital_investment
Online_revenue = Σ(price × units_sold) từ marketplace HOẶC nội suy từ tỷ lệ ngành
```

### 4.6. Web Application

| Module | Chức năng |
|--------|-----------|
| Dashboard | IIP, heatmap KTS, OECD vs GSO |
| Companies | Profile 10 DN, kênh bán số, case Rạng Đông |
| Pipeline | Monitor crawl jobs, trigger manual |
| ML Lab | So sánh 3 model, forecast chart |
| Benchmark | Form nhập BCTC → ROA/ROE/percentile |

### 4.7. Triển khai

- Docker Compose: backend + frontend + PostgreSQL + Redis + worker
- Pipeline scheduler: chạy hàng ngày lúc 02:00
- API: FastAPI `/api/*`
- Frontend: React + Recharts
