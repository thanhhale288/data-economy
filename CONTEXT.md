# Manufacturing Digital Economy (VSIC Section C)

Shared language for the Manufacturing Data Economy Platform — Vietnam manufacturing digital economy analytics (macro GSO/OECD + micro listed companies + marketplace + IIP forecast + benchmark).

## Industry & classifications

**VSIC Section C**:
Vietnam Standard Industrial Classification section for manufacturing (chế biến, chế tạo). Project focus is Section C; detailed codes often VSIC 10–33.
_Avoid_: “toàn ngành công nghiệp”, ISIC alone when mapping VN firms

**ISIC Section C**:
International Standard Industrial Classification manufacturing section. Used for OECD series and VSIC↔ISIC mapping in `vsic_codes`.
_Avoid_: NAICS, HS

**VSIC code**:
A specific industry code on a company or macro series (e.g. `2740` lighting, `2410` steel), stored in `vsic_codes` and `companies.vsic_code`.

## Macro indicators

**IIP** (Industrial Production Index):
Monthly manufacturing production index for Section C from GSO (`IIP_C`). Primary forecast target for the ML Lab.
_Avoid_: GDP, PMI (unless explicitly added later)

**GSO macro**:
Vietnam statistical series ingested from NSO/GSO NSDP SDMX (host `nsdp.nso.gov.vn`) and PX-Web (`pxweb.nso.gov.vn`), stored in `gso_macro` — monthly IIP; annual shipment (E07.03) and inventory (E07.04) step-held to monthly. `source` ∈ `{GSO, GSO_FALLBACK}`.
_Avoid_: inventing GSO numbers; prefer live NSO endpoints, then sourced fallback fixtures

**OECD MEI IP**:
OECD Main Economic Indicators industrial production — ISIC Section C. **Not published for VNM**; project stores peer **EA20** as `country=EA20`, `source=OECD_PEER` for IIP forecast lags only (see ADR-0001).
_Avoid_: inventing VNM MEI values; treating peer series as Vietnam data

**BCI** (Business Confidence Index):
OECD manufacturing confidence leading indicator. Unavailable for VNM; do not fabricate.

**INDIGO**:
OECD digital trade openness index for VNM (annual). Harmonized to monthly via **step-hold** (same annual value Jan–Dec) so it can join monthly IIP — not linear interpolation (ADR-0001).
`oecd_indicators.source` ∈ `{OECD, OECD_FALLBACK, OECD_PEER}`.

## Micro / companies

**Listed sample company**:
One of the ten seeded HOSE/HNX firms used for micro analysis: RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BWE.
_Avoid_: random extra tickers unless the user expands the seed set

**BCTC**:
Structured financial report fields for a company-period (revenue, profit, assets, equity, employees, gross margin, etc.) in `financial_reports`.
_Avoid_: “báo cáo tài chính” as a vague blob without the schema fields

**Digital presence**:
A verified digital sales channel for a company (website, Shopee, TikTok, Lazada, …) in `digital_presence`, including checkout detection and match confidence.

**Marketplace listing**:
A scraped product row (price, units sold estimate, revenue estimate) linked to a company in `marketplace_listings`.

**Shop matcher**:
Model/heuristic that links a marketplace shop name to a listed company (fuzzy + optional TF-IDF/embeddings; match threshold **0.65**).
_Avoid_: assuming 1.0 confidence without evidence

**Online revenue**:
Estimated digital sales = Σ(price × units_sold) from marketplace listings, or industry-ratio interpolation when listings are missing.

## Digital economy metrics

**VDEI Manufacturing**:
The project’s pillar indicator set (M1–M10) for manufacturing digital economy — IIP/VA, adoption, e-commerce share, channel mix, labour productivity, Digital VA, logistics/payment/export digital, percentile benchmark.

**Digital VA**:
Firm-level digital value-added estimate:

`Digital_VA = (Online_revenue × Gross_margin) + (Cost_savings × Adoption_score) - Digital_investment`

_Avoid_: equating Digital VA with total revenue or with IIP

**Digital adoption score**:
Composite of how digital a firm is (channels, checkout, activity) used in features and Digital VA.

**Channel diversity**:
Spread of digital channels (website vs marketplace vs social) for a firm or aggregate.

**Online revenue ratio**:
Online revenue relative to total firm (or industry) revenue; used in cross features with IIP growth.

## Benchmark & finance ratios

**Benchmark** (SingStat BITE style):
Compare a firm’s efficiency ratios to industry peers/percentiles (ROA, ROE, current ratio, digital revenue per worker, etc.).

**ROA / ROE / current ratio**:
Standard financial ratios from BCTC used as benchmark inputs — do not invent definitions; compute from `financial_reports` fields.

## ML Lab

**ARIMA tier**:
Statistical forecast of IIP Section C; proposal baseline ARIMA(1,1,1) via statsmodels (not a hand-rolled EMA stand-in).

**XGBoost tier**:
Tree model forecasting IIP with engineered lag/rolling/digital/OECD features.

**LSTM tier**:
Deep multi-step forecast (about 3–6 months), evaluated with MAE / RMSE / MAPE like the other tiers.

**Model prediction**:
A stored forecast row in `model_predictions` / registry for dashboard comparison.

## Platform modules

**Dashboard**:
UI for IIP, digital-economy heatmap, OECD vs GSO comparison.

**Pipeline job**:
A crawl/clean/train run tracked in `pipeline_jobs` (scheduler target ~02:00 daily).

**Data ingestion layer**:
The three parallel ingest streams: GSO macro, listed-company micro, OECD international.
