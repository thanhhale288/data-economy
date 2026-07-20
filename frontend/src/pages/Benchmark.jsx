import { useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../api'
import { formatGrouped, parseGrouped } from '../format'

const METRIC_LABELS = {
  roa: 'Tỷ suất sinh lời trên tài sản (ROA)',
  roe: 'Tỷ suất sinh lời trên vốn CSH (ROE)',
  current_ratio: 'Hệ số thanh toán hiện hành',
  equity_ratio: 'Tỷ trọng vốn chủ sở hữu',
  revenue_per_worker: 'Doanh thu trên lao động',
  profit_per_worker: 'Lợi nhuận trên lao động',
}

/** Công thức khớp `compute_benchmark_ratios` — đúng field form, không bịa “average”. */
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
}

const COMPARISON_LABELS = {
  above_average: 'Trên trung bình ngành',
  below_average: 'Dưới trung bình ngành',
  average: 'Bằng trung bình ngành',
  insufficient_peers: 'Thiếu mẫu peer',
  neutral: '—',
}

const WARNING_LABELS = {
  insufficient_peers: 'Không đủ peer ngành để tính phân vị — không bịa số.',
  prototype_listed_sample:
    'Bản demo: peer = DN niêm yết seed cùng phân ngành VSIC 2 số, không phải chuẩn quốc gia.',
  small_peer_sample: 'Mẫu peer nhỏ (< 3 DN) — phân vị chỉ mang tính tham khảo.',
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

const EMPTY_FORM = {
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

function displayNum(value) {
  if (value == null || value === '') return ''
  const n = typeof value === 'number' ? value : parseGrouped(value)
  if (n == null) return String(value)
  return formatGrouped(n, { maxFractionDigits: 0 })
}

function formatRatio(value) {
  if (value == null) return '—'
  if (typeof value !== 'number') return value
  if (value < 10) return `${(value * 100).toFixed(1)}%`
  return formatGrouped(value)
}

/** Share/ratio as percent string; null → null (caller renders N/A). */
function formatSharePct(value) {
  if (value == null || typeof value !== 'number') return null
  return `${(value * 100).toFixed(1)}%`
}

function shareToPct(value) {
  if (value == null || typeof value !== 'number') return null
  return Math.max(0, Math.min(100, value * 100))
}

function formFromPrefill(data) {
  return {
    vsic_code: data.vsic_code ?? '',
    operating_revenue: displayNum(data.operating_revenue),
    profit_before_tax: displayNum(data.profit_before_tax),
    employees: displayNum(data.employees),
    operating_expenses: displayNum(data.operating_expenses),
    cost_of_goods: displayNum(data.cost_of_goods),
    rental_cost: displayNum(data.rental_cost),
    remuneration: displayNum(data.remuneration),
    total_assets: displayNum(data.total_assets),
    total_equity: displayNum(data.total_equity),
    current_assets: displayNum(data.current_assets),
    current_liabilities: displayNum(data.current_liabilities),
  }
}

function scrollToId(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function MetricInfoTip({ metricKey }) {
  const info = METRIC_INFO[metricKey]
  const btnRef = useRef(null)
  const [open, setOpen] = useState(false)
  const [coords, setCoords] = useState(null)

  const updatePlace = () => {
    if (!btnRef.current) return
    const rect = btnRef.current.getBoundingClientRect()
    const width = Math.min(340, window.innerWidth - 24)
    let left = rect.left + rect.width / 2 - width / 2
    left = Math.max(12, Math.min(left, window.innerWidth - width - 12))
    const gap = 10
    const preferAbove = rect.top > 140
    if (preferAbove) {
      setCoords({
        width,
        left,
        bottom: window.innerHeight - rect.top + gap,
        top: undefined,
        placeAbove: true,
      })
    } else {
      setCoords({
        width,
        left,
        top: rect.bottom + gap,
        bottom: undefined,
        placeAbove: false,
      })
    }
  }

  useLayoutEffect(() => {
    if (!open) return undefined
    updatePlace()
    window.addEventListener('scroll', updatePlace, true)
    window.addEventListener('resize', updatePlace)
    return () => {
      window.removeEventListener('scroll', updatePlace, true)
      window.removeEventListener('resize', updatePlace)
    }
  }, [open])

  if (!info) return null

  const show = () => {
    updatePlace()
    setOpen(true)
  }
  const hide = () => {
    setOpen(false)
    setCoords(null)
  }

  const pop = open && coords
    ? createPortal(
        <div
          className={`metric-info-pop is-open${coords.placeAbove ? ' is-above' : ' is-below'}`}
          role="tooltip"
          style={{
            top: coords.top,
            bottom: coords.bottom,
            left: coords.left,
            width: coords.width,
          }}
        >
          <span className="metric-info-head">
            <span className="metric-info-badge" aria-hidden="true">
              <svg viewBox="0 0 32 32" width="22" height="22">
                <rect x="6" y="8" width="14" height="16" rx="2" fill="#38bdf8" />
                <rect x="9" y="11" width="8" height="2" rx="1" fill="#e0f2fe" />
                <rect x="9" y="15" width="8" height="2" rx="1" fill="#e0f2fe" />
                <rect x="9" y="19" width="5" height="2" rx="1" fill="#e0f2fe" />
                <circle cx="22" cy="20" r="5" fill="#fbbf24" />
                <circle cx="22" cy="20" r="3.2" fill="#f59e0b" />
              </svg>
            </span>
            <span className="metric-info-title">{info.title}</span>
            <span className="metric-info-eq" aria-hidden="true">=</span>
            <span className="metric-info-frac">
              <span className="metric-info-num">{info.numerator}</span>
              <span className="metric-info-den">{info.denominator}</span>
            </span>
          </span>
          <span className="metric-info-body">{info.blurb}</span>
        </div>,
        document.body,
      )
    : null

  return (
    <span
      className="metric-info"
      onMouseEnter={show}
      onMouseLeave={hide}
    >
      <button
        ref={btnRef}
        type="button"
        className="metric-info-btn"
        aria-label={`Công thức ${info.title}`}
        aria-expanded={open}
        onFocus={show}
        onBlur={hide}
      >
        i
      </button>
      {pop}
    </span>
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
        <span className="singstat-donut-pct">{pct.toFixed(1)}%</span>
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
              <span className="singstat-key-bar-pct">{indPct.toFixed(1)}%</span>
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
              <span className="singstat-key-bar-pct">{firmPct.toFixed(1)}%</span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Benchmark() {
  const [form, setForm] = useState({ ...EMPTY_FORM })
  const [prefillSource, setPrefillSource] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setPrefillSource(null)
  }

  const handleMoneyBlur = (field) => {
    setForm((prev) => {
      const n = parseGrouped(prev[field])
      if (n == null) return prev
      return { ...prev, [field]: formatGrouped(n, { maxFractionDigits: 0 }) }
    })
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
      const res = await api.benchmark(payload)
      setResult(res)
    } catch (err) {
      console.error(err)
      setResult(null)
      setError(err.message || 'Không so sánh được benchmark.')
    } finally {
      setLoading(false)
    }
  }

  const loadPrefill = async (stockCode) => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await api.benchmarkPrefill(stockCode)
      setForm(formFromPrefill(data))
      setPrefillSource(data.stock_code || stockCode)
    } catch (err) {
      console.error(err)
      setPrefillSource(null)
      setError(
        err.message?.includes('404')
          ? `Không có BCTC đủ trường để nạp «${stockCode}» — không nạp số bịa.`
          : (err.message || `Không nạp được ${stockCode}.`)
      )
    } finally {
      setLoading(false)
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
    setError(null)
  }

  const insufficientPeers = (result?.warnings || []).includes('insufficient_peers')
    || result?.peer_count === 0
  const metricEntries = result
    ? Object.entries(METRIC_LABELS).filter(([key]) => result[key] != null)
    : []

  const avg = result?.industry_averages || {}

  return (
    <div>
      <h2 className="page-title">So sánh hiệu quả doanh nghiệp</h2>
      <p style={{ color: '#888', marginBottom: 24 }}>
        So sánh chỉ số DN với peer cùng phân ngành VSIC (tham chiếu UX SingStat BITE).
        Nạp form từ BCTC qua API — thiếu mẫu thì phân vị để trống, không bịa mức 50.
      </p>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        <button
          type="button"
          className="btn btn-primary"
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
          title={`Đổi VSIC sang ${NO_PEER_VSIC} để demo thiếu peer`}
        >
          Demo thiếu peer (VSIC {NO_PEER_VSIC})
        </button>
      </div>

      {prefillSource && (
        <p className="chart-note" style={{ marginBottom: 12 }}>
          Form đã nạp từ <code>/api/benchmark/prefill/{prefillSource}</code> — số liệu BCTC đã lưu, không ghi cứng trên giao diện.
        </p>
      )}

      {!prefillSource && !form.operating_revenue && (
        <div className="banner banner-warn" style={{ marginBottom: 16 }}>
          Form trống — bấm «Nạp RAL từ BCTC» (hoặc nhập tay). Không dùng số mẫu bịa sẵn.
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

        <div className="form-grid" style={{ marginTop: 8 }}>
          <div className="form-group">
            <label>Tổng tài sản (VND)</label>
            <input
              inputMode="numeric"
              value={form.total_assets}
              onChange={(e) => handleChange('total_assets', e.target.value)}
              onBlur={() => handleMoneyBlur('total_assets')}
            />
          </div>
          <div className="form-group">
            <label>Vốn chủ sở hữu (VND)</label>
            <input
              inputMode="numeric"
              value={form.total_equity}
              onChange={(e) => handleChange('total_equity', e.target.value)}
              onBlur={() => handleMoneyBlur('total_equity')}
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
        <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: 16 }}>
          {loading ? 'Đang so sánh...' : 'So sánh benchmark'}
        </button>
      </form>

      {error && (
        <div className="banner banner-warn" style={{ marginTop: 16 }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 24 }}>
          <div className="chart-container" style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 14 }}>
              Phạm vi peer: <strong>{result.peer_scope || '—'}</strong>
              {' · '}
              Số peer BCTC: <strong>{result.peer_count ?? 0}</strong>
              {insufficientPeers && (
                <>
                  {' '}
                  <span className="badge badge-warning">thiếu peer</span>
                </>
              )}
            </div>
            {(result.warnings || []).length > 0 && (
              <ul style={{ margin: '8px 0 0', paddingLeft: 18, color: '#888', fontSize: 13 }}>
                {result.warnings.map((w) => (
                  <li key={w}>{WARNING_LABELS[w] || w}</li>
                ))}
              </ul>
            )}
            {insufficientPeers && (
              <div className="empty-state" style={{ marginTop: 12 }}>
                Thiếu peer cùng phân ngành — phân vị = Không có (không bịa mức 50).
                Chỉ số DN (nếu đủ input) vẫn tính từ form; TB ngành / xếp hạng để trống.
              </div>
            )}
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

          <div id="singstat-kpi">
            {metricEntries.length === 0 ? (
              <div className="empty-state">
                Không tính được chỉ số từ dữ liệu hiện tại — bổ sung BCTC (tài sản/vốn CSH/…) hoặc nạp RAL.
              </div>
            ) : (
              <div className="cards">
                {metricEntries.map(([key, label]) => {
                  const value = result[key]
                  const pct = result.percentiles?.[key]
                  const comp = result.comparison?.[key]
                  const indAvg = result.industry_averages?.[key]
                  return (
                    <div className="card" key={key}>
                      <div className="label">{label}</div>
                      <div className="value metric-value-row" style={{ fontSize: 22 }}>
                        <span>{formatRatio(value)}</span>
                        <MetricInfoTip metricKey={key} />
                      </div>
                      {pct != null ? (
                        <>
                          <div className="sub">Phân vị: {pct}%</div>
                          <div className="percentile-bar">
                            <div className="percentile-fill" style={{ width: `${pct}%` }} />
                          </div>
                        </>
                      ) : (
                        <div className="sub">Phân vị: Không có (thiếu mẫu peer)</div>
                      )}
                      <div style={{ fontSize: 12, color: '#888', marginTop: 8 }}>
                        TB ngành: {indAvg != null ? formatRatio(indAvg) : 'Không có'}
                      </div>
                      <div style={{ fontSize: 12, marginTop: 4 }}>
                        <span
                          className={`badge ${
                            comp === 'above_average'
                              ? 'badge-success'
                              : comp === 'below_average'
                                ? 'badge-danger'
                                : comp === 'insufficient_peers'
                                  ? 'badge-warning'
                                  : 'badge-warning'
                          }`}
                        >
                          {COMPARISON_LABELS[comp] || comp}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <section id="singstat-expenditure" className="singstat-section">
            <header className="singstat-section-head">
              <h3 className="singstat-section-title">Tỷ lệ liên quan chi phí</h3>
              <p className="singstat-section-note">
                Chi phí hoạt động ÷ doanh thu hoạt động. TB ngành lấy từ peer; thiếu dữ liệu thì «Không có» — không hiện 0%.
              </p>
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
              <p className="singstat-section-note">
                Tỷ trọng trong chi phí hoạt động. Thanh chỉ dùng share từ API; thiếu giá trị thì «Không có».
              </p>
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
