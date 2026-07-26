# Provenance for data/raw/gso_iip_fallback.csv
#
# Dataset: Vietnam Industrial Production Index — Manufacturing (ISIC Section C)
# SDMX INDICATOR: AIP_ISIC4_C_IX
# Official URL (current host, NSO): https://nsdp.nso.gov.vn/GSO-chung/SDMXFiles/GSO/IIPVNM.xml
# Former host (dead / timeout as of 2026-07-18): https://nsdp.gso.gov.vn/.../IIPVNM.xml
# Archive mirror used to build this file when official host timed out on 2026-07-17:
#   https://raw.githubusercontent.com/thanhqtran/gso-macro-monitor/main/2024q3/IIPVNM.xml
# Wayback snapshot of the same official file:
#   https://web.archive.org/web/20230325152851/https://nsdp.gso.gov.vn/GSO-chung/SDMXFiles/GSO/IIPVNM.xml
# SDMX Header/Prepared in mirror: 2024-11-13T06:48:52Z
# Extracted: 2026-07-17; host update noted: 2026-07-18
# Unit: index, BASE_PER=2015 (2015=100)
#
# Shipment (E07.03) and inventory (E07.04) are NOT in this IIP SDMX document —
# they are crawled separately via PX-Web (`pxweb.nso.gov.vn`) with their own
# fallbacks under data/raw/gso_pxweb_*_fallback.json.
# Manufacturing VA is NOT in this file — see GDPVNM.xml + gso_va_fallback.csv
# (Task #38).
