import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts'
import { api } from '../api'
import { formatGrouped, formatMoney, parseGrouped, formatIndex } from '../format'
import MetricInfoTip from '../MetricInfoTip'

const METRIC_LABELS = {
  roa: 'Tỷ suất sinh lời trên tài sản (ROA)',
  roe: 'Tỷ suất sinh lời trên vốn CSH (ROE)',
  current_ratio: 'Hệ số thanh toán hiện hành',
  equity_ratio: 'Tỷ trọng vốn chủ sở hữu',
  revenue_per_worker: 'Doanh thu trên lao động',
  profit_per_worker: 'Lợi nhuận trên lao động',
  profit_margin: 'Biên lợi nhuận trước thuế',
  asset_turnover: 'Vòng quay tài sản',
  debt_to_equity: 'Nợ trên vốn chủ sở hữu',
}

/** Short labels for radar axes. */
const METRIC_SHORT = {
  roa: 'ROA',
  roe: 'ROE',
  current_ratio: 'Thanh khoản',
  equity_ratio: 'Tỷ trọng VCSH',
  revenue_per_worker: 'DT/LĐ',
  profit_per_worker: 'LN/LĐ',
  profit_margin: 'Biên LN',
  asset_turnover: 'Vòng quay TS',
  debt_to_equity: 'Nợ/VCSH',
}

/** Higher value = more leverage risk (not “better”). */
const HIGHER_IS_WORSE = new Set(['debt_to_equity'])

/** Công thức khớp `compute_benchmark_ratios`. */
const METRIC_INFO = {
  roa: {
    title: 'Tỷ suất sinh lời trên tài sản (ROA)',
    numerator: 'Lợi nhuận trước thuế',
    denominator: 'Tổng tài sản',
    blurb: 'Đo hiệu quả sử dụng tài sản để tạo lợi nhuận.',
  },
  roe: {
    title: 'Tỷ suất sinh lời trên vốn CSH (ROE)',
    numerator: 'Lợi nhuận trước thuế',
    denominator: 'Vốn chủ sở hữu',
    blurb: 'Đo mức sinh lời cho chủ sở hữu so với vốn CSH trên sổ sách.',
  },
  current_ratio: {
    title: 'Hệ số thanh toán hiện hành',
    numerator: 'Tài sản ngắn hạn',
    denominator: 'Nợ ngắn hạn',
    blurb: 'Khả năng thanh khoản: đáp ứng nghĩa vụ ngắn hạn bằng tài sản ngắn hạn.',
  },
  equity_ratio: {
    title: 'Tỷ trọng vốn chủ sở hữu',
    numerator: 'Vốn chủ sở hữu',
    denominator: 'Tổng tài sản',
    blurb: 'Tỷ lệ tài sản được tài trợ bằng vốn chủ sở hữu thay vì nợ.',
  },
  revenue_per_worker: {
    title: 'Doanh thu trên lao động',
    numerator: 'Doanh thu hoạt động',
    denominator: 'Số lao động',
    blurb: 'Chỉ số gần đúng năng suất lao động theo doanh thu hoạt động trên mỗi người.',
  },
  profit_per_worker: {
    title: 'Lợi nhuận trên lao động',
    numerator: 'Lợi nhuận trước thuế',
    denominator: 'Số lao động',
    blurb: 'Chỉ số gần đúng năng suất theo lợi nhuận trước thuế trên mỗi người.',
  },
  profit_margin: {
    title: 'Biên lợi nhuận trước thuế',
    numerator: 'Lợi nhuận trước thuế',
    denominator: 'Doanh thu hoạt động',
    blurb: 'Mỗi đồng doanh thu tạo ra bao nhiêu lợi nhuận trước thuế.',
  },
  asset_turnover: {
    title: 'Vòng quay tài sản',
    numerator: 'Doanh thu hoạt động',
    denominator: 'Tổng tài sản',
    blurb: 'Mức doanh thu tạo ra trên mỗi đồng tài sản. Cùng ROA: ROA ≈ biên LN × vòng quay tài sản.',
  },
  debt_to_equity: {
    title: 'Nợ trên vốn chủ sở hữu',
    numerator: 'Tổng tài sản − Vốn CSH',
    denominator: 'Vốn chủ sở hữu',
    blurb:
      'Ước lượng đòn bẩy: nợ tương đối so với vốn chủ. Số cao hơn thường nghĩa rủi ro đòn bẩy cao hơn — không phải chỉ số “càng cao càng tốt”.',
  },
}

const COMPARISON_LABELS = {
  above_average: 'Trên trung bình ngành',
  below_average: 'Dưới trung bình ngành',
  average: 'Bằng trung bình ngành',
  insufficient_peers: 'Chưa đủ doanh nghiệp cùng ngành',
  neutral: '—',
}

const DEBT_COMPARISON_LABELS = {
  above_average: 'Đòn bẩy cao hơn ngành',
  below_average: 'Đòn bẩy thấp hơn ngành',
  average: 'Đòn bẩy gần trung bình ngành',
  insufficient_peers: 'Chưa đủ doanh nghiệp cùng ngành',
  neutral: '—',
}

/** API BenchmarkResult.warnings → Vietnamese honesty copy (show all, not only insufficient_peers). */
const WARNING_LABELS = {
  prototype_listed_sample:
    'So sánh trên mẫu DN niêm yết trong nền tảng (~28 DN) — chưa phải chuẩn ngành quốc gia (VSIC Section C).',
  small_peer_sample:
    'Ít hơn 3 DN cùng ngành có BCTC — phân vị chỉ mang tính tham khảo.',
  insufficient_peers:
    'Chưa đủ doanh nghiệp cùng ngành trong dữ liệu để so sánh phân vị.',
}

const KEY_EXPENDITURE_ROWS = [
  { key: 'purchase_goods_share', label: 'Chi phí hàng hóa & nguyên vật liệu' },
  { key: 'rental_cost_share', label: 'Chi phí thuê mặt bằng' },
  { key: 'remuneration_share', label: 'Chi phí nhân công (thù lao)' },
]

const MONEY_FIELDS = [
  'operating_revenue',
  'profit_before_tax',
  'operating_expenses',
  'cost_of_goods',
  'rental_cost',
  'remuneration',
  'total_assets',
  'total_equity',
  'current_assets',
  'current_liabilities',
]
const EXTRACT_LOW_CONFIDENCE = 0.75

const DIGITAL_LABELS = {
  digital_adoption_score: 'Mức độ số hóa kênh bán',
  online_revenue_ratio: 'Tỷ trọng doanh thu online (ước lượng)',
}

const DIGITAL_INFO = {
  digital_adoption_score: {
    title: 'Mức độ số hóa kênh bán',
    blurb:
      'Điểm tổng hợp 0–100% từ các kênh đã ghi nhận: website, gian hàng sàn thương mại điện tử và tín hiệu bán hàng. Điểm cao nghĩa là doanh nghiệp hiện diện trên nhiều kênh số hơn.',
  },
  online_revenue_ratio: {
    title: 'Tỷ trọng doanh thu online (ước lượng)',
    numerator: 'Doanh thu online ước lượng',
    denominator: 'Doanh thu hoạt động',
    blurb:
      'Phần doanh thu đến từ kênh online so với tổng doanh thu. Doanh thu online là ước lượng từ các sản phẩm thu thập được trên sàn, không phải số doanh nghiệp công bố.',
  },
}

const EMPTY_FORM = {
  stock_code: '',
  vsic_code: '',
  operating_revenue: '',
  profit_before_tax: '',
  employees: '',
  operating_expenses: '',
  cost_of_goods: '',
  rental_cost: '',
  remuneration: '',
  total_assets: '',
  total_equity: '',
  current_assets: '',
  current_liabilities: '',
}

/** VSIC division with no seed peers — demos honest insufficient_peers (user supplies own inputs). */
const NO_PEER_VSIC = '1100'

function displayNum(value, { money = false } = {}) {
  if (value == null || value === '') return ''
  const n = typeof value === 'number' ? value : parseGrouped(value)
  if (n == null) return String(value)
  if (money) {
    // Form inputs: show rounded grouped digits without suffix (label already has VND).
    const rounded = Math.round(n / 1000) * 1000
    return formatGrouped(rounded, { maxFractionDigits: 0 })
  }
  return formatGrouped(n, { maxFractionDigits: 0 })
}

function formatRatio(value, metricKey) {
  if (value == null) return '—'
  if (typeof value !== 'number') return value
  // Per-worker metrics are VND amounts; the rest are unitless ratios.
  if (metricKey === 'revenue_per_worker' || metricKey === 'profit_per_worker') {
    // Compact triệu amounts too (131M VND) so cards and band labels stay one-line.
    const abs = Math.abs(value)
    if (abs >= 1e6 && abs < 1e9) {
      return `${formatGrouped(value / 1e6, { maxFractionDigits: 0 })}M VND`
    }
    return formatMoney(value, 'VND')
  }
  if (
    metricKey === 'debt_to_equity'
    || metricKey === 'asset_turnover'
    || metricKey === 'current_ratio'
  ) {
    return `${formatGrouped(value, { maxFractionDigits: 2 })}×`
  }
  if (value < 10) return `${(value * 100).toFixed(2)}%`
  return formatGrouped(value, { maxFractionDigits: 2 })
}

function comparisonLabel(metricKey, comp) {
  const map = HIGHER_IS_WORSE.has(metricKey) ? DEBT_COMPARISON_LABELS : COMPARISON_LABELS
  return map[comp] || comp
}

function comparisonBadgeClass(metricKey, comp) {
  if (comp === 'insufficient_peers' || comp === 'average' || !comp) return 'badge-warning'
  const worseIsHigh = HIGHER_IS_WORSE.has(metricKey)
  if (comp === 'above_average') return worseIsHigh ? 'badge-danger' : 'badge-success'
  if (comp === 'below_average') return worseIsHigh ? 'badge-success' : 'badge-danger'
  return 'badge-warning'
}

/** Strength 0–100 for ranking (invert leverage). */
function strengthScore(metricKey, percentile) {
  if (percentile == null) return null
  return HIGHER_IS_WORSE.has(metricKey) ? 100 - percentile : percentile
}

function buildBenchmarkSummary(result, metricEntries) {
  if (!result || !metricEntries.length) return null
  const scored = metricEntries
    .map(([key]) => {
      const pct = result.percentiles?.[key]
      const strength = strengthScore(key, pct)
      if (strength == null) return null
      return { key, pct, strength, label: METRIC_LABELS[key] || key }
    })
    .filter(Boolean)

  if (!scored.length) {
    return {
      empty:
        'Chưa có đủ doanh nghiệp cùng ngành trong dữ liệu để xếp hạng. '
        + 'Các chỉ số của doanh nghiệp vẫn được tính từ báo cáo tài chính đã nhập.',
    }
  }

  const aboveMedian = scored.filter((s) => s.strength >= 50).length
  const weakest = scored.reduce((a, b) => (b.strength < a.strength ? b : a))
  const strongest = scored.reduce((a, b) => (b.strength > a.strength ? b : a))

  return {
    aboveMedian,
    total: scored.length,
    strongest,
    weakest,
    weakestIsLeverage: HIGHER_IS_WORSE.has(weakest.key),
  }
}

/** Plain-Vietnamese reading of a percentile, e.g. "cao hơn khoảng 80% doanh nghiệp cùng ngành". */
function describeRank(metricKey, pct) {
  if (pct == null) return 'chưa xếp hạng được'
  if (HIGHER_IS_WORSE.has(metricKey)) {
    return `vay nợ nhiều hơn khoảng ${pct}% doanh nghiệp cùng ngành`
  }
  return `cao hơn khoảng ${pct}% doanh nghiệp cùng ngành`
}

/** Peer band P25–P75 with median + firm marker (percentile axis 0–100). */
function QuartileBand({ quartiles, firmValue, formatValue }) {
  if (!quartiles || firmValue == null) return null
  const { p25, p50, p75 } = quartiles
  if (p25 == null || p50 == null || p75 == null) return null

  const lo = Math.min(p25, firmValue)
  const hi = Math.max(p75, firmValue)
  const span = hi - lo || 1
  // Pad 8% each side so markers at the extremes don't touch the edge.
  const pct = (v) => 8 + ((v - lo) / span) * 84
  const bandLeft = pct(p25)
  const bandWidth = Math.max(pct(p75) - bandLeft, 2)
  const medLeft = pct(p50)
  const firmLeft = pct(firmValue)
  // Keep the "Bạn" pin label inside the card even when the dot is near an edge.
  const pinLeft = Math.min(Math.max(firmLeft, 16), 84)

  return (
    <div className="quartile-band">
      <div className="quartile-pin-row">
        <span className="quartile-pin" style={{ left: `${pinLeft}%` }}>
          Bạn: {formatValue(firmValue)}
        </span>
        <span className="quartile-pin-caret" style={{ left: `${firmLeft}%` }} />
      </div>
      <div className="quartile-track">
        <div
          className="quartile-range"
          style={{ left: `${bandLeft}%`, width: `${bandWidth}%` }}
        />
        <div className="quartile-median" style={{ left: `${medLeft}%` }} />
        <div className="quartile-firm" style={{ left: `${firmLeft}%` }} />
      </div>
      <div className="quartile-labels">
        <span>Thấp {formatValue(p25)}</span>
        <span>Giữa ngành {formatValue(p50)}</span>
        <span>Cao {formatValue(p75)}</span>
      </div>
    </div>
  )
}

/** One-line legend explaining the quartile band, rendered once per card group. */
function QuartileLegend() {
  return (
    <div className="quartile-legend">
      <span className="quartile-legend-item">
        <i className="quartile-legend-swatch swatch-range" />
        Khoảng phổ biến — một nửa số doanh nghiệp cùng ngành nằm trong vùng này
      </span>
      <span className="quartile-legend-item">
        <i className="quartile-legend-swatch swatch-median" />
        Mức giữa ngành
      </span>
      <span className="quartile-legend-item">
        <i className="quartile-legend-swatch swatch-firm" />
        Doanh nghiệp của bạn
      </span>
    </div>
  )
}

/** Human-readable peer scope from API (`vsic_division:27` → plain Vietnamese). */
function describePeerScope(result) {
  if (!result) return null
  const scope = result.peer_scope || ''
  const count = result.peer_count ?? 0
  const divisionMatch = /^vsic_division:(\d+)$/i.exec(scope)
  const division = divisionMatch?.[1]
  const vsicHint = division ? (
    <>
      phân ngành VSIC <strong className="scope-highlight">{division}</strong>
    </>
  ) : (
    scope || 'cùng phân ngành VSIC'
  )

  if (count === 0) {
    return (
      <>
        Chưa có doanh nghiệp niêm yết cùng {vsicHint} có báo cáo tài chính trong dữ liệu
        để làm đối chiếu.
      </>
    )
  }
  return (
    <>
      Đang so sánh với <strong className="scope-highlight">{count}</strong>{' '}
      doanh nghiệp niêm yết cùng {vsicHint} (có báo cáo tài chính trong dữ liệu).
    </>
  )
}

/** Share/ratio as percent string; null → null (caller renders N/A). */
function formatSharePct(value) {
  if (value == null || typeof value !== 'number') return null
  return `${(value * 100).toFixed(2)}%`
}

function shareToPct(value) {
  if (value == null || typeof value !== 'number') return null
  return Math.max(0, Math.min(100, value * 100))
}

function formFromPrefill(data) {
  const money = (v) => displayNum(v, { money: true })
  return {
    stock_code: data.stock_code ?? '',
    vsic_code: data.vsic_code ?? '',
    operating_revenue: money(data.operating_revenue),
    profit_before_tax: money(data.profit_before_tax),
    employees: displayNum(data.employees),
    operating_expenses: money(data.operating_expenses),
    cost_of_goods: money(data.cost_of_goods),
    rental_cost: money(data.rental_cost),
    remuneration: money(data.remuneration),
    total_assets: money(data.total_assets),
    total_equity: money(data.total_equity),
    current_assets: money(data.current_assets),
    current_liabilities: money(data.current_liabilities),
  }
}

function formFromExtract(fields, prevForm) {
  const money = (v) => displayNum(v, { money: true })
  return {
    ...prevForm,
    operating_revenue: money(fields?.operating_revenue),
    profit_before_tax: money(fields?.profit_before_tax),
    employees: displayNum(fields?.employees),
    total_assets: money(fields?.total_assets),
    total_equity: money(fields?.total_equity),
  }
}

/** Snapshot of allowlisted numeric/string fields for Task #64 feedback diffs. */
function snapshotFormFields(formLike) {
  const keys = [
    'stock_code',
    'vsic_code',
    'operating_revenue',
    'profit_before_tax',
    'employees',
    'operating_expenses',
    'cost_of_goods',
    'rental_cost',
    'remuneration',
    'total_assets',
    'total_equity',
    'current_assets',
    'current_liabilities',
  ]
  const out = {}
  for (const key of keys) {
    const raw = formLike?.[key]
    if (raw === '' || raw == null) {
      out[key] = null
      continue
    }
    if (key === 'stock_code' || key === 'vsic_code') {
      out[key] = String(raw)
      continue
    }
    const n = typeof raw === 'number' ? raw : parseGrouped(raw)
    out[key] = n == null ? String(raw) : n
  }
  return out
}

function scrollToId(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function BenchmarkMetricTip({ metricKey, source = METRIC_INFO }) {
  const info = source[metricKey]
  if (!info) return null
  return (
    <MetricInfoTip
      title={info.title}
      blurb={info.blurb}
      numerator={info.numerator}
      denominator={info.denominator}
      ariaLabel={`Công thức ${info.title}`}
    />
  )
}

/** Digital footprint vs same-division peers (only for prefilled listed firms). */
function DigitalSection({ digital }) {
  if (!digital) return null

  if (digital.status !== 'ok') {
    const message = {
      no_stock_code:
        'Nhập tay chưa gắn với doanh nghiệp niêm yết nào, nên chưa so sánh được mức độ số hóa. '
        + 'Hãy bấm nạp một doanh nghiệp ở phía trên.',
      no_company:
        'Doanh nghiệp đã nạp không thuộc phân ngành đang chọn, nên chưa so sánh được mức độ số hóa.',
      no_metrics:
        'Chưa thu thập được dữ liệu kênh số của doanh nghiệp này, nên chưa có gì để so sánh.',
    }[digital.status]
    if (!message) return null
    return (
      <div className="chart-container" style={{ marginBottom: 16 }}>
        <h3>So sánh mức độ số hóa</h3>
        <div className="empty-state">{message}</div>
      </div>
    )
  }

  const entries = Object.entries(DIGITAL_LABELS).filter(
    ([key]) => digital.metrics?.[key] != null,
  )
  if (!entries.length) return null

  return (
    <div id="digital-benchmark" className="chart-container" style={{ marginBottom: 16 }}>
      <h3>So sánh mức độ số hóa</h3>
      <p className="chart-note" style={{ marginTop: 0 }}>
        Dữ liệu kênh số của <strong className="scope-highlight">{digital.stock_code}</strong>
        {digital.period ? ` (kỳ ${String(digital.period).slice(0, 7)})` : ''} so với{' '}
        <strong className="scope-highlight">{digital.peer_count}</strong> doanh nghiệp cùng
        phân ngành đã có dữ liệu số hóa.
      </p>
      {entries.some(([key]) => digital.industry_quartiles?.[key]) && <QuartileLegend />}
      <div className="cards">
        {entries.map(([key, label]) => {
          const value = digital.metrics[key]
          const pct = digital.percentiles?.[key]
          const avg = digital.industry_averages?.[key]
          const comp = digital.comparison?.[key]
          const quartiles = digital.industry_quartiles?.[key]
          const asPct = (v) => (v == null ? '—' : `${(v * 100).toFixed(2)}%`)
          return (
            <div className="card" key={key}>
              <div className="label">{label}</div>
              <div className="value metric-value-row" style={{ fontSize: 22 }}>
                <span>{asPct(value)}</span>
                <BenchmarkMetricTip metricKey={key} source={DIGITAL_INFO} />
              </div>
              {pct != null ? (
                <>
                  <div className="sub">Xếp hạng: {describeRank(key, pct)}</div>
                  <div className="percentile-bar">
                    <div className="percentile-fill" style={{ width: `${pct}%` }} />
                  </div>
                </>
              ) : (
                <div className="sub">
                  Chưa xếp hạng được — không đủ doanh nghiệp cùng ngành có dữ liệu số hóa
                </div>
              )}
              {quartiles && (
                <QuartileBand quartiles={quartiles} firmValue={value} formatValue={asPct} />
              )}
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>
                Trung bình ngành: {asPct(avg)}
              </div>
              <div style={{ fontSize: 12, marginTop: 4 }}>
                <span className={`badge ${comparisonBadgeClass(key, comp)}`}>
                  {comparisonLabel(key, comp)}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ShareDonut({ label, value, tone }) {
  const pct = shareToPct(value)
  const r = 36
  const c = 2 * Math.PI * r
  const stroke = tone === 'firm' ? 'var(--singstat-firm)' : 'var(--singstat-industry)'

  if (pct == null) {
    return (
      <div className="singstat-donut">
        <div className="singstat-donut-ring singstat-donut-ring--empty" aria-hidden="true">
          <span className="singstat-donut-na">Không có</span>
        </div>
        <div className="singstat-donut-caption">{label}</div>
      </div>
    )
  }

  const dash = (pct / 100) * c
  return (
    <div className="singstat-donut">
      <svg className="singstat-donut-svg" viewBox="0 0 96 96" aria-hidden="true">
        <circle className="singstat-donut-track" cx="48" cy="48" r={r} />
        <circle
          className="singstat-donut-arc"
          cx="48"
          cy="48"
          r={r}
          stroke={stroke}
          strokeDasharray={`${dash} ${c - dash}`}
          transform="rotate(-90 48 48)"
        />
      </svg>
      <div className="singstat-donut-center">
        <span className="singstat-donut-pct">{pct.toFixed(2)}%</span>
      </div>
      <div className="singstat-donut-caption">{label}</div>
    </div>
  )
}

function KeyExpenditureRow({ label, industry, firm }) {
  const indPct = shareToPct(industry)
  const firmPct = shareToPct(firm)
  const maxPct = Math.max(indPct ?? 0, firmPct ?? 0, 1)

  return (
    <div className="singstat-key-row">
      <div className="singstat-key-row-label">{label}</div>
      <div className="singstat-key-bars">
        <div className="singstat-key-bar-line">
          <span className="singstat-key-bar-tag singstat-key-bar-tag--industry">Ngành</span>
          {indPct == null ? (
            <span className="singstat-na">Không có</span>
          ) : (
            <>
              <div className="singstat-key-bar-track">
                <div
                  className="singstat-key-bar-fill singstat-key-bar-fill--industry"
                  style={{ width: `${(indPct / maxPct) * 100}%` }}
                />
              </div>
              <span className="singstat-key-bar-pct">{indPct.toFixed(2)}%</span>
            </>
          )}
        </div>
        <div className="singstat-key-bar-line">
          <span className="singstat-key-bar-tag singstat-key-bar-tag--firm">DN của bạn</span>
          {firmPct == null ? (
            <span className="singstat-na">Không có</span>
          ) : (
            <>
              <div className="singstat-key-bar-track">
                <div
                  className="singstat-key-bar-fill singstat-key-bar-fill--firm"
                  style={{ width: `${(firmPct / maxPct) * 100}%` }}
                />
              </div>
              <span className="singstat-key-bar-pct">{firmPct.toFixed(2)}%</span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Benchmark() {
  const [searchParams] = useSearchParams()
  const vsicFromUrl = searchParams.get('vsic') || ''
  const [form, setForm] = useState({
    ...EMPTY_FORM,
    vsic_code: vsicFromUrl || '',
  })
  const [prefillSource, setPrefillSource] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const [extractMeta, setExtractMeta] = useState(null)
  const [requireConfirm, setRequireConfirm] = useState(false)
  const [humanConfirmed, setHumanConfirmed] = useState(false)
  /** Task #64 — prefill/extract snapshot for edit→confirm training signal. */
  const [prefillSnapshot, setPrefillSnapshot] = useState(null)
  const [narrative, setNarrative] = useState(null)
  const [narrativeLoading, setNarrativeLoading] = useState(false)
  const [narrativeError, setNarrativeError] = useState(null)

  useEffect(() => {
    if (vsicFromUrl) {
      setForm((prev) => ({ ...prev, vsic_code: vsicFromUrl }))
    }
  }, [vsicFromUrl])

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setPrefillSource(null)
    if (requireConfirm) setHumanConfirmed(false)
  }

  const handleMoneyBlur = (field) => {
    setForm((prev) => {
      const n = parseGrouped(prev[field])
      if (n == null) return prev
      const rounded = Math.round(n / 1000) * 1000
      return { ...prev, [field]: formatGrouped(rounded, { maxFractionDigits: 0 }) }
    })
  }

  const loadNarrative = async (compareResult) => {
    if (!compareResult) {
      setNarrative(null)
      setNarrativeError(null)
      return
    }
    setNarrativeLoading(true)
    setNarrativeError(null)
    try {
      const payload = await api.benchmarkNarrative(compareResult)
      setNarrative(payload)
    } catch (err) {
      console.error(err)
      setNarrative(null)
      setNarrativeError(err.message || 'Không tạo được giải thích benchmark.')
    } finally {
      setNarrativeLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const payload = { ...form }
      for (const key of MONEY_FIELDS) {
        if (payload[key] === '' || payload[key] == null) payload[key] = null
        else payload[key] = parseGrouped(payload[key])
      }
      payload.operating_revenue = parseGrouped(payload.operating_revenue)
      payload.profit_before_tax = parseGrouped(payload.profit_before_tax)
      payload.employees = parseGrouped(payload.employees)
      payload.stock_code = payload.stock_code || null
      const res = await api.benchmark(payload)
      setResult(res)
      await loadNarrative(res)
    } catch (err) {
      console.error(err)
      setResult(null)
      setNarrative(null)
      setError(err.message || 'Không so sánh được benchmark.')
    } finally {
      setLoading(false)
    }
  }

  const handleUploadExtract = async (file) => {
    if (!file) return
    setExtracting(true)
    setError(null)
    setResult(null)
    setNarrative(null)
    setNarrativeError(null)
    setPrefillSource(null)
    try {
      const extracted = await api.benchmarkExtract(file)
      setForm((prev) => formFromExtract(extracted.fields, prev))
      setPrefillSnapshot(snapshotFormFields(extracted.fields || {}))
      setExtractMeta({
        confidence: extracted.confidence || {},
        warnings: extracted.warnings || [],
        source_type: extracted.source_type || 'unknown',
        filename: file.name,
      })
      setRequireConfirm(true)
      setHumanConfirmed(false)
    } catch (err) {
      console.error(err)
      setExtractMeta(null)
      setPrefillSnapshot(null)
      setRequireConfirm(false)
      setHumanConfirmed(false)
      setError(err.message || 'Không trích xuất được BCTC.')
    } finally {
      setExtracting(false)
    }
  }

  const loadPrefill = async (stockCode) => {
    setLoading(true)
    setError(null)
    setResult(null)
    setNarrative(null)
    setNarrativeError(null)
    setExtractMeta(null)
    setRequireConfirm(false)
    setHumanConfirmed(false)
    try {
      const data = await api.benchmarkPrefill(stockCode)
      const next = formFromPrefill(data)
      setForm(next)
      setPrefillSnapshot(snapshotFormFields(next))
      setPrefillSource(data.stock_code || stockCode)
    } catch (err) {
      console.error(err)
      setPrefillSource(null)
      setPrefillSnapshot(null)
      setError(
        err.message?.includes('404')
          ? `Không tìm thấy BCTC đủ trường để nạp «${stockCode}».`
          : (err.message || `Không nạp được ${stockCode}.`)
      )
    } finally {
      setLoading(false)
    }
  }

  /** Task #64 — soft POST training signal on confirm (never send raw file). */
  const postFeedbackSignal = (sourceType) => {
    if (!prefillSnapshot) return
    const after = snapshotFormFields(form)
    api.benchmarkFeedback({
      before: prefillSnapshot,
      after,
      ticker: form.stock_code || prefillSource || null,
      source_type: sourceType || extractMeta?.source_type || 'docai_extract',
    }).catch((err) => {
      console.warn('feedback signal failed', err)
    })
  }

  const handleConfirmChange = (checked) => {
    setHumanConfirmed(checked)
    if (checked) {
      postFeedbackSignal(extractMeta?.source_type || 'docai_extract')
    }
  }

  const setInsufficientPeerDemo = () => {
    // Keep firm inputs if already prefilled; only swap VSIC to a division with no peers.
    setForm((prev) => ({
      ...prev,
      vsic_code: NO_PEER_VSIC,
    }))
    setPrefillSource(null)
    setResult(null)
    setNarrative(null)
    setNarrativeError(null)
    setError(null)
    setExtractMeta(null)
    setRequireConfirm(false)
    setHumanConfirmed(false)
    setPrefillSnapshot(null)
  }

  const insufficientPeers = (result?.warnings || []).includes('insufficient_peers')
    || result?.peer_count === 0
  const resultWarnings = result?.warnings || []
  const metricEntries = result
    ? Object.entries(METRIC_LABELS).filter(([key]) => result[key] != null)
    : []

  const avg = result?.industry_averages || {}
  const summary = buildBenchmarkSummary(result, metricEntries)
  const radarData = metricEntries
    .map(([key]) => {
      const firmPct = result?.percentiles?.[key]
      if (firmPct == null) return null
      return {
        metric: METRIC_SHORT[key] || key,
        firm: strengthScore(key, firmPct),
        peerMedian: 50,
      }
    })
    .filter(Boolean)
  const lowConfidenceFields = Object.entries(extractMeta?.confidence || {})
    .filter(([, score]) => typeof score === 'number' && score > 0 && score < EXTRACT_LOW_CONFIDENCE)
    .map(([key]) => key)
  const isLowConfidence = (field) => lowConfidenceFields.includes(field)
  const compareLockedByConfirm = requireConfirm && !humanConfirmed

  return (
    <div>
      <h2 className="page-title">So sánh hiệu quả doanh nghiệp</h2>
      <p className="page-subtitle">
        Upload BCTC → trích xuất → kiểm tra/chỉnh sửa → xác nhận → so sánh phân vị với peers niêm yết
        trong mẫu (không phải chuẩn ngành quốc gia). Thiếu số liệu luôn hiện N/A — không bịa phân vị.
      </p>

      <div className="toolbar mb-md">
        <label
          className="btn btn-primary"
          htmlFor="benchmark-upload-input"
          style={{ cursor: extracting ? 'wait' : 'pointer' }}
        >
          {extracting ? 'Đang trích xuất...' : 'Upload BCTC để prefill'}
        </label>
        <input
          id="benchmark-upload-input"
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.webp,.tif,.tiff,.bmp"
          style={{ display: 'none' }}
          disabled={extracting || loading}
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleUploadExtract(file)
            e.target.value = ''
          }}
        />
        <button
          type="button"
          className="btn"
          onClick={() => loadPrefill('RAL')}
          disabled={loading}
        >
          Nạp RAL từ BCTC
        </button>
        <button type="button" className="btn" onClick={() => loadPrefill('REE')} disabled={loading}>
          Nạp REE (cùng ngành 27)
        </button>
        <button
          type="button"
          className="btn"
          onClick={setInsufficientPeerDemo}
          disabled={loading}
          title={`Đổi VSIC sang ${NO_PEER_VSIC} để xem trường hợp không có DN cùng ngành`}
        >
          Xem khi không có DN cùng ngành (VSIC {NO_PEER_VSIC})
        </button>
      </div>

      {extractMeta && (
        <div className="banner banner-warn mb-md" role="status">
          File <strong>{extractMeta.filename}</strong> đã được trích xuất ({extractMeta.source_type}).
          {extractMeta.warnings?.length > 0 && (
            <div className="extract-meta-detail">
              Cảnh báo: {extractMeta.warnings.join(', ')}
            </div>
          )}
          {lowConfidenceFields.length > 0 && (
            <div className="extract-meta-detail">
              Confidence thấp (&lt; {EXTRACT_LOW_CONFIDENCE}): {lowConfidenceFields.join(', ')}.
              Hãy kiểm tra kỹ trước khi compare.
            </div>
          )}
        </div>
      )}

      {!prefillSource && !form.operating_revenue && !extractMeta && (
        <div className="banner banner-warn mb-md" role="status">
          Form trống — upload BCTC, bấm «Nạp RAL từ BCTC», hoặc nhập tay các chỉ tiêu.
        </div>
      )}

      <form onSubmit={handleSubmit} className="chart-container">
        <div className="form-grid">
          <div className="form-group">
            <label>Mã VSIC</label>
            <input value={form.vsic_code} onChange={(e) => handleChange('vsic_code', e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Doanh thu hoạt động (VND)</label>
            <input
              inputMode="numeric"
              value={form.operating_revenue}
              onChange={(e) => handleChange('operating_revenue', e.target.value)}
              onBlur={() => handleMoneyBlur('operating_revenue')}
              className={isLowConfidence('operating_revenue') ? 'field-low-confidence' : undefined}
              required
            />
          </div>
          <div className="form-group">
            <label>Lợi nhuận trước thuế (VND)</label>
            <input
              inputMode="numeric"
              value={form.profit_before_tax}
              onChange={(e) => handleChange('profit_before_tax', e.target.value)}
              onBlur={() => handleMoneyBlur('profit_before_tax')}
              className={isLowConfidence('profit_before_tax') ? 'field-low-confidence' : undefined}
              required
            />
          </div>
          <div className="form-group">
            <label>Số lao động</label>
            <input
              inputMode="numeric"
              value={form.employees}
              onChange={(e) => handleChange('employees', e.target.value)}
              onBlur={() => handleMoneyBlur('employees')}
              className={isLowConfidence('employees') ? 'field-low-confidence' : undefined}
              required
            />
          </div>
        </div>

        <div className="singstat-form-block">
          <div className="form-group">
            <label>Chi phí hoạt động (VND)</label>
            <input
              inputMode="numeric"
              value={form.operating_expenses}
              onChange={(e) => handleChange('operating_expenses', e.target.value)}
              onBlur={() => handleMoneyBlur('operating_expenses')}
            />
          </div>
          <p className="singstat-of-which">Trong đó</p>
          <div className="form-grid singstat-of-which-grid">
            <div className="form-group">
              <label>Giá vốn hàng bán &amp; NVL (VND)</label>
              <input
                inputMode="numeric"
                value={form.cost_of_goods}
                onChange={(e) => handleChange('cost_of_goods', e.target.value)}
                onBlur={() => handleMoneyBlur('cost_of_goods')}
              />
            </div>
            <div className="form-group">
              <label>Chi phí thuê mặt bằng (VND)</label>
              <input
                inputMode="numeric"
                value={form.rental_cost}
                onChange={(e) => handleChange('rental_cost', e.target.value)}
                onBlur={() => handleMoneyBlur('rental_cost')}
              />
            </div>
            <div className="form-group">
              <label>Chi phí nhân công / thù lao (VND)</label>
              <input
                inputMode="numeric"
                value={form.remuneration}
                onChange={(e) => handleChange('remuneration', e.target.value)}
                onBlur={() => handleMoneyBlur('remuneration')}
              />
            </div>
          </div>
        </div>

        <div className="form-grid mt-sm">
          <div className="form-group">
            <label>Tổng tài sản (VND)</label>
            <input
              inputMode="numeric"
              value={form.total_assets}
              onChange={(e) => handleChange('total_assets', e.target.value)}
              onBlur={() => handleMoneyBlur('total_assets')}
              className={isLowConfidence('total_assets') ? 'field-low-confidence' : undefined}
            />
          </div>
          <div className="form-group">
            <label>Vốn chủ sở hữu (VND)</label>
            <input
              inputMode="numeric"
              value={form.total_equity}
              onChange={(e) => handleChange('total_equity', e.target.value)}
              onBlur={() => handleMoneyBlur('total_equity')}
              className={isLowConfidence('total_equity') ? 'field-low-confidence' : undefined}
            />
          </div>
          <div className="form-group">
            <label>Tài sản ngắn hạn (VND)</label>
            <input
              inputMode="numeric"
              value={form.current_assets}
              onChange={(e) => handleChange('current_assets', e.target.value)}
              onBlur={() => handleMoneyBlur('current_assets')}
            />
          </div>
          <div className="form-group">
            <label>Nợ ngắn hạn (VND)</label>
            <input
              inputMode="numeric"
              value={form.current_liabilities}
              onChange={(e) => handleChange('current_liabilities', e.target.value)}
              onBlur={() => handleMoneyBlur('current_liabilities')}
            />
          </div>
        </div>
        {requireConfirm && (
          <label className="confirm-check">
            <input
              type="checkbox"
              checked={humanConfirmed}
              onChange={(e) => handleConfirmChange(e.target.checked)}
            />
            <span>Tôi đã kiểm tra/chỉnh sửa dữ liệu prefill từ file trước khi so sánh</span>
          </label>
        )}
        {compareLockedByConfirm && (
          <div className="banner banner-warn mt-sm" role="status">
            Cần xác nhận dữ liệu prefill từ file trước khi bấm compare.
          </div>
        )}
        <button type="submit" className="btn btn-primary mt-md" disabled={loading || compareLockedByConfirm}>
          {loading ? 'Đang so sánh...' : 'So sánh benchmark'}
        </button>
      </form>

      {error && (
        <div className="banner banner-warn mt-md" role="alert">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-lg">
          {resultWarnings.length > 0 && (
            <div className="banner-stack">
              {resultWarnings.map((code) => (
                <div
                  key={code}
                  className="banner banner-warn"
                  role="status"
                >
                  <span className="badge badge-warning" style={{ marginRight: 8 }}>
                    {code}
                  </span>
                  {WARNING_LABELS[code] || code}
                </div>
              ))}
            </div>
          )}
          <div className="chart-container mb-md">
            <p className="chart-note mt-0" style={{ fontSize: 14, color: 'var(--ink-soft)' }}>
              {describePeerScope(result)}
              {insufficientPeers && (
                <>
                  {' '}
                  <span className="badge badge-warning">chưa đủ dữ liệu so sánh</span>
                </>
              )}
            </p>
            <div className="singstat-jump">
              <button
                type="button"
                className="singstat-jump-btn"
                onClick={() => scrollToId('singstat-expenditure')}
              >
                So sánh tỷ lệ liên quan chi phí
              </button>
              <button
                type="button"
                className="singstat-jump-btn"
                onClick={() => scrollToId('singstat-kpi')}
              >
                So sánh hiệu quả theo phân vị
              </button>
            </div>
          </div>

          <div
            id="benchmark-narrative"
            className="chart-container story-panel mb-md"
            role="region"
            aria-label="Giải thích kết quả benchmark"
          >
            <h3>Giải thích ROA / ROE / phân vị</h3>
            <p className="chart-note mt-0">
              Chỉ trích dẫn số từ kết quả so sánh vừa nhận — thiếu chỉ số thì bỏ qua, không bịa.
            </p>
            {narrativeLoading && (
              <p className="chart-note">Đang soạn giải thích…</p>
            )}
            {narrativeError && (
              <div className="banner banner-warn" role="alert">
                {narrativeError}
              </div>
            )}
            {!narrativeLoading && narrative?.narrative && (
              <>
                <div className="narrative-list" style={{ listStyle: 'none', paddingLeft: 0 }}>
                  {(narrative.paragraphs?.length
                    ? narrative.paragraphs
                    : narrative.narrative.split(/\n\n+/)).map((para, idx) => (
                    <p key={`narr-${idx}`} className="chart-note" style={{ marginTop: idx === 0 ? 0 : 8 }}>
                      {para}
                    </p>
                  ))}
                </div>
                {narrative.omitted?.length > 0 && (
                  <p className="chart-note muted-text">
                    Bỏ qua (thiếu trong kết quả): {narrative.omitted.join(', ')}
                  </p>
                )}
                <p className="chart-note muted-text" style={{ fontSize: 12 }}>
                  Nguồn: {narrative.method === 'llm' ? 'LLM (đã kiểm tra số)' : 'mẫu rules-first'}
                </p>
              </>
            )}
            {!narrativeLoading && !narrativeError && !narrative?.narrative && (
              <div className="empty-state">Chưa có giải thích cho kết quả này.</div>
            )}
          </div>

          <div id="singstat-kpi">
            {metricEntries.length === 0 ? (
              <div className="empty-state">
                Không tính được chỉ số từ dữ liệu hiện tại — bổ sung BCTC (tài sản/vốn CSH/…) hoặc nạp RAL.
              </div>
            ) : (
              <>
                {radarData.length >= 3 && (
                  <div className="chart-container" style={{ marginBottom: 16 }}>
                    <h3>Vị trí của doanh nghiệp so với các doanh nghiệp cùng ngành</h3>
                    <p className="chart-note" style={{ marginTop: 0 }}>
                      Mỗi trục là một chỉ số, thang 0–100: càng ra ngoài càng tốt hơn so với các
                      doanh nghiệp cùng ngành. Đường nét đứt là mức giữa của ngành. Riêng nợ trên
                      vốn chủ sở hữu đã được đảo chiều, nên ra ngoài nghĩa là vay nợ ít hơn.
                    </p>
                    <ResponsiveContainer width="100%" height={320}>
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="#c9dfea" />
                        <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: '#164654' }} />
                        <PolarRadiusAxis
                          angle={30}
                          domain={[0, 100]}
                          tick={{ fontSize: 10 }}
                        />
                        <Radar
                          name="Doanh nghiệp của bạn"
                          dataKey="firm"
                          stroke="#367ea2"
                          fill="#367ea2"
                          fillOpacity={0.35}
                        />
                        <Radar
                          name="Mức giữa của ngành"
                          dataKey="peerMedian"
                          stroke="#164654"
                          fill="transparent"
                          strokeDasharray="4 4"
                        />
                        <Legend />
                        <Tooltip formatter={(value) => formatIndex(value)} />
                      </RadarChart>
                    </ResponsiveContainer>

                    {summary && (
                      <div className="benchmark-summary" role="status">
                        {summary.empty ? (
                          <p className="benchmark-summary-empty">{summary.empty}</p>
                        ) : (
                          <>
                            <div className="benchmark-summary-head">
                              <span className="benchmark-summary-score">
                                {summary.aboveMedian}
                                <span className="benchmark-summary-total">
                                  /{summary.total}
                                </span>
                              </span>
                              <span className="benchmark-summary-caption">
                                chỉ số đạt từ mức giữa của ngành trở lên
                              </span>
                            </div>
                            <ul className="benchmark-summary-list">
                              <li>
                                <span className="benchmark-summary-tag is-strong">
                                  Điểm mạnh
                                </span>
                                <span>
                                  <strong>{summary.strongest.label}</strong> —{' '}
                                  {describeRank(summary.strongest.key, summary.strongest.pct)}.
                                </span>
                              </li>
                              <li>
                                <span className="benchmark-summary-tag is-weak">
                                  {summary.weakestIsLeverage ? 'Cần chú ý' : 'Điểm yếu'}
                                </span>
                                <span>
                                  <strong>{summary.weakest.label}</strong> —{' '}
                                  {describeRank(summary.weakest.key, summary.weakest.pct)}.
                                </span>
                              </li>
                            </ul>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {metricEntries.some(([key]) => result.industry_quartiles?.[key]) && (
                  <QuartileLegend />
                )}
                <div className="cards">
                  {metricEntries.map(([key, label]) => {
                    const value = result[key]
                    const pct = result.percentiles?.[key]
                    const comp = result.comparison?.[key]
                    const indAvg = result.industry_averages?.[key]
                    const quartiles = result.industry_quartiles?.[key]
                    return (
                      <div className="card" key={key}>
                        <div className="label">{label}</div>
                        <div className="value metric-value-row" style={{ fontSize: 22 }}>
                          <span>{formatRatio(value, key)}</span>
                          <BenchmarkMetricTip metricKey={key} />
                        </div>
                        {pct != null ? (
                          <>
                            <div className="sub">
                              Xếp hạng: {describeRank(key, pct)}
                            </div>
                            <div className="percentile-bar">
                              <div className="percentile-fill" style={{ width: `${pct}%` }} />
                            </div>
                          </>
                        ) : (
                          <div className="sub">
                            Chưa xếp hạng được — không đủ doanh nghiệp cùng ngành để so sánh
                          </div>
                        )}
                        {quartiles ? (
                          <QuartileBand
                            quartiles={quartiles}
                            firmValue={value}
                            formatValue={(v) => formatRatio(v, key)}
                          />
                        ) : (
                          pct != null && (
                            <div className="sub muted" style={{ marginTop: 6 }}>
                              Cần ít nhất 4 doanh nghiệp cùng ngành để hiện khoảng phổ biến
                            </div>
                          )
                        )}
                        <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>
                          Trung bình ngành: {indAvg != null ? formatRatio(indAvg, key) : 'Không có'}
                        </div>
                        <div style={{ fontSize: 12, marginTop: 4 }}>
                          <span className={`badge ${comparisonBadgeClass(key, comp)}`}>
                            {comparisonLabel(key, comp)}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>

                <DigitalSection digital={result.digital} />
              </>
            )}
          </div>

          <section id="singstat-expenditure" className="singstat-section">
            <header className="singstat-section-head">
              <h3 className="singstat-section-title">Tỷ lệ liên quan chi phí</h3>
            </header>

            <div className="singstat-donut-row">
              <ShareDonut
                label="Ngành"
                value={avg.expenditure_related_ratio}
                tone="industry"
              />
              <ShareDonut
                label="DN của bạn"
                value={result.expenditure_related_ratio}
                tone="firm"
              />
            </div>

            <div className="singstat-legend">
              <span className="singstat-legend-item">
                <i className="singstat-swatch singstat-swatch--industry" /> Ngành
              </span>
              <span className="singstat-legend-item">
                <i className="singstat-swatch singstat-swatch--firm" /> DN của bạn
              </span>
            </div>

            <header className="singstat-section-head" style={{ marginTop: 28 }}>
              <h3 className="singstat-section-title">Cơ cấu chi phí chính</h3>
            </header>

            <div className="singstat-key-list">
              {KEY_EXPENDITURE_ROWS.map(({ key, label }) => (
                <KeyExpenditureRow
                  key={key}
                  label={label}
                  industry={avg[key]}
                  firm={result[key]}
                />
              ))}
            </div>

            {(result.comparison?.expenditure_related_ratio
              || result.comparison?.purchase_goods_share) && (
              <p className="singstat-comp-note">
                So sánh chi phí:{' '}
                {COMPARISON_LABELS[result.comparison?.expenditure_related_ratio]
                  || result.comparison?.expenditure_related_ratio
                  || '—'}
                {formatSharePct(result.expenditure_related_ratio) != null && (
                  <> · Tỷ lệ chi phí DN {formatSharePct(result.expenditure_related_ratio)}</>
                )}
              </p>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
