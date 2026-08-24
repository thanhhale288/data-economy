# PROVENANCE — Frame Pilot (Evol-1 T02)

- Retrieved at (UTC): 2026-08-24T09:03:11Z
- Source: https://www.masothue.com public listing pages
- Industry index: https://www.masothue.com/tra-cuu-ma-so-thue-theo-nganh-nghe/
- Requested divisions: 10, 22, 25
- Target unique firms: 800
- Final unique firms: 800

## Coverage

- VSIC 4-digit industries discovered and harvested:
  - 1010: https://www.masothue.com/tra-cuu-ma-so-thue-theo-nganh-nghe/che-bien-bao-quan-thit-va-cac-san-pham-tu-thit-1010
  - 2211: https://www.masothue.com/tra-cuu-ma-so-thue-theo-nganh-nghe/san-xuat-sam-lop-cao-su-dap-va-tai-che-lop-cao-su-2211
  - 2511: https://www.masothue.com/tra-cuu-ma-so-thue-theo-nganh-nghe/san-xuat-cac-cau-kien-kim-loai-2511
  - 1020: https://www.masothue.com/tra-cuu-ma-so-thue-theo-nganh-nghe/che-bien-bao-quan-thuy-san-va-cac-san-pham-tu-thuy-san-1020
  - 2212: https://www.masothue.com/tra-cuu-ma-so-thue-theo-nganh-nghe/san-xuat-san-pham-khac-tu-cao-su-2212
  - 2512: https://www.masothue.com/tra-cuu-ma-so-thue-theo-nganh-nghe/san-xuat-thung-be-chua-va-dung-cu-chua-dung-bang-kim-loai-2512
  - 1030: https://www.masothue.com/tra-cuu-ma-so-thue-theo-nganh-nghe/che-bien-va-bao-quan-rau-qua-1030

## Counts by division

- 10: 300
- 22: 250
- 25: 250

## Limits

- **Not an official GSO/Cổng ĐKKD frame.** This is the proposal-v4 *backup* pilot frame from a public tax directory.
- **VSIC on the listing page is “registered activity,” not necessarily the firm’s main activity.** Example noise: hospitality/branch names can appear under manufacturing codes when that code is one of many registered lines.
- Listings include **chi nhánh / địa điểm kinh doanh** (branch MST with `-xxx` suffix), not only head offices.
- Province distribution reflects what masothue indexes publicly — **not** national manufacturing geography.
- No employee-size field → cannot stratify by firm size yet.
- `founded_year` left empty when absent from listing cards (detail-page crawl deferred).
- Deduplicated by `tax_code`; **no synthetic rows** invented to hit the target.
- Do **not** claim “n=800 represents Vietnam Section C manufacturing.”
