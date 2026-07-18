# Provenance — `data/raw/companies/`

Structured BCTC fallbacks for the fixed listed sample (Task 5).

Canonical allowlisted file (git): `../companies_bctc_fallback.json`  
Provenance twin: `../companies_bctc_fallback.PROVENANCE.md`

| Ticker | Profile note | BCTC source_url |
|--------|--------------|-----------------|
| RAL | Rạng Đông lighting | `seed:companies.json` |
| HPG | Hòa Phát steel | `seed:companies.json` |
| VNM | Vinamilk | `seed:companies.json` |
| FPT | FPT | `seed:companies.json` |
| GVR | Cao su VN | `seed:companies.json` |
| DGC | Đức Giang chemicals | `seed:companies.json` |
| MSN | Masan | `seed:companies.json` |
| PNJ | PNJ jewelry | `seed:companies.json` |
| REE | REE M&E | `seed:companies.json` |
| BMP | **Intentional plastics sample** (VSIC 2220 / Bình Minh profile) — not water utility | `seed:companies.json` |

Optional per-ticker files may be added as `{ticker}_bctc_fallback.json` with an
explicit `source_url`. Do not add unsourced invented numbers.
