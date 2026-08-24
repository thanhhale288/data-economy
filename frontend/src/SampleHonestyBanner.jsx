/**
 * Sample scope signal (ADR-0003): listed deep sample ≠ all of VSIC Section C.
 */

export const SAMPLE_HONESTY_TEXT =
  'Số liệu doanh nghiệp trên nền tảng lấy từ mẫu niêm yết (~28 DN), không đại diện toàn ngành chế biến, chế tạo (VSIC Section C).'

/** Vietnamese copy for UniverseCoverageNote.claim (contract #39). */
export const COVERAGE_CLAIM_LABELS = {
  prototype_listed_sample:
    'Số liệu doanh nghiệp trên nền tảng lấy từ mẫu niêm yết, không đại diện toàn ngành chế biến, chế tạo (VSIC Section C).',
  universe_shallow_only:
    'Chỉ có vũ trụ DN nông (identity/VSIC) — chưa đủ mẫu sâu để suy ra chuẩn toàn Section C.',
  official_macro:
    'Đây là chỉ số macro chính thức (GSO/NSO).',
  insufficient_data:
    'Chưa đủ dữ liệu universe/mẫu sâu để tuyên bố độ phủ ngành chế biến, chế tạo.',
}

function badgeLabel(coverageNote) {
  if (!coverageNote) return 'mẫu ~28'
  const n = coverageNote.deep_sample_size
  const u = coverageNote.universe_row_count
  if (typeof n === 'number' && n > 0) {
    return `mẫu ~${n}`
  }
  if (typeof u === 'number' && u > 0) {
    return `universe ${u}`
  }
  return coverageNote.claim || 'coverage'
}

function bannerText(coverageNote) {
  if (!coverageNote) return SAMPLE_HONESTY_TEXT
  const mapped = COVERAGE_CLAIM_LABELS[coverageNote.claim]
  if (mapped) {
    const n = coverageNote.deep_sample_size
    const u = coverageNote.universe_row_count
    const sizeBit =
      typeof n === 'number'
        ? ` Mẫu sâu (listed): ${n} DN.`
        : ''
    const universeBit =
      typeof u === 'number'
        ? ` Universe nông: ${u} dòng (không phải coverage toàn Section C).`
        : ''
    return `${mapped}${sizeBit}${universeBit}`
  }
  return coverageNote.detail || SAMPLE_HONESTY_TEXT
}

export default function SampleHonestyBanner({ style, className, coverageNote }) {
  const classes = ['banner', 'banner-warn', className].filter(Boolean).join(' ')
  return (
    <div className={classes} style={style} role="status">
      <span className="badge badge-warning" style={{ marginRight: 8 }}>
        {badgeLabel(coverageNote)}
      </span>
      {bannerText(coverageNote)}
    </div>
  )
}
