# Provenance for data/raw/gso_va_fallback.csv

Dataset: Vietnam manufacturing **value added** (ISIC / VSIC Section C) from NSO
National Accounts SDMX.

| Stored code | SDMX INDICATOR | Price basis |
|-------------|----------------|-------------|
| `VA_C` | `NGDPVA_R_ISIC4_C_XDC` | Constant 2010 |
| `VA_C_NOMINAL` | `NGDPVA_ISIC4_C_XDC` | Current prices |

- Official URL: https://nsdp.nso.gov.vn/GSO-chung/SDMXFiles/GSO/GDPVNM.xml
- Catalog: https://nsdp.nso.gov.vn/index.htm
- `REF_AREA=VN`, `UNIT_MULT=9` (billions of VND)
- Extracted: 2026-07-26 from annual (`FREQ=A`) observations 2023–2024
- Fixture expands each annual value to Jan–Dec via **step-hold** (same policy as
  shipment/inventory) — not linear invention of intra-year paths

**Not included:** province-by-industry GRDP (no confirmed PX-Web/SDMX table ID as
of Task #38). Digital-economy VA shares of GDP/GRDP are a different concept and
are not stored as `VA_C`.
