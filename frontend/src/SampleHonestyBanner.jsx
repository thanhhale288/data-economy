/**
 * Persistent honesty signal (ADR-0003): Digital VA / digitalization =
 * listed sample (~28), not all of VSIC Section C.
 */
export const SAMPLE_HONESTY_TEXT =
  'Số liệu Digital VA và mức độ số hóa trên trang này tính trên mẫu ~28 doanh nghiệp niêm yết, không đại diện toàn ngành chế biến, chế tạo (VSIC Section C).'

export default function SampleHonestyBanner({ style }) {
  return (
    <div className="banner banner-warn" style={style} role="status">
      <span className="badge badge-warning" style={{ marginRight: 8 }}>
        mẫu ~28
      </span>
      {SAMPLE_HONESTY_TEXT}
    </div>
  )
}
