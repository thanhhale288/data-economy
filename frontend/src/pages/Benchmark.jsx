import { useState } from 'react'
import { api } from '../api'

const METRIC_LABELS = {
  roa: 'Return on Assets (ROA)',
  roe: 'Return on Equity (ROE)',
  current_ratio: 'Current Ratio',
  equity_ratio: 'Equity Ratio',
  revenue_per_worker: 'Revenue per Worker',
  profit_per_worker: 'Profit per Worker',
}

const COMPARISON_LABELS = {
  above_average: 'Trên trung bình ngành',
  below_average: 'Dưới trung bình ngành',
  average: 'Bằng trung bình ngành',
  insufficient_peers: 'Thiếu mẫu peer',
  neutral: '—',
}

const WARNING_LABELS = {
  insufficient_peers: 'Không đủ peer ngành để tính percentile — không bịa số.',
  prototype_listed_sample: 'Prototype: peer = DN niêm yết seed cùng phân ngành VSIC 2 số, không phải chuẩn quốc gia.',
  small_peer_sample: 'Mẫu peer nhỏ (< 3 DN) — percentile chỉ mang tính tham khảo.',
}

const KEY_EXPENDITURE_ROWS = [
  { key: 'purchase_goods_share', label: 'Purchase of Goods & Materials' },
  { key: 'rental_cost_share', label: 'Rental Cost of Premises' },
  { key: 'remuneration_share', label: 'Remuneration' },
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

function formatRatio(value) {
  if (value == null) return '—'
  if (typeof value !== 'number') return value
  if (value < 10) return `${(value * 100).toFixed(1)}%`
  return value.toLocaleString()
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
    operating_revenue: data.operating_revenue ?? '',
    profit_before_tax: data.profit_before_tax ?? '',
    employees: data.employees ?? '',
    operating_expenses: data.operating_expenses ?? '',
    cost_of_goods: data.cost_of_goods ?? '',
    rental_cost: data.rental_cost ?? '',
    remuneration: data.remuneration ?? '',
    total_assets: data.total_assets ?? '',
    total_equity: data.total_equity ?? '',
    current_assets: data.current_assets ?? '',
    current_liabilities: data.current_liabilities ?? '',
  }
}

function scrollToId(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
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
          <span className="singstat-donut-na">N/A</span>
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
          <span className="singstat-key-bar-tag singstat-key-bar-tag--industry">Industry</span>
          {indPct == null ? (
            <span className="singstat-na">N/A</span>
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
          <span className="singstat-key-bar-tag singstat-key-bar-tag--firm">Your firm</span>
          {firmPct == null ? (
            <span className="singstat-na">N/A</span>
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const payload = { ...form }
      for (const key of [
        'operating_expenses',
        'cost_of_goods',
        'rental_cost',
        'remuneration',
        'total_assets',
        'total_equity',
        'current_assets',
        'current_liabilities',
      ]) {
        if (payload[key] === '' || payload[key] == null) payload[key] = null
        else payload[key] = Number(payload[key])
      }
      payload.operating_revenue = Number(payload.operating_revenue)
      payload.profit_before_tax = Number(payload.profit_before_tax)
      payload.employees = Number(payload.employees)
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
          ? `Không có BCTC đủ field để prefill «${stockCode}» — không nạp số bịa.`
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
      <h2 className="page-title">Benchmark My Performance</h2>
      <p style={{ color: '#888', marginBottom: 24 }}>
        So sánh hiệu quả doanh nghiệp với peer cùng phân ngành VSIC (tham chiếu UX SingStat BITE).
        Prefill lấy từ BCTC API — thiếu mẫu thì percentile null, không bịa 50th.
      </p>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => loadPrefill('RAL')}
          disabled={loading}
        >
          Nạp RAL từ BCTC (prefill API)
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
          Form đã nạp từ <code>/api/benchmark/prefill/{prefillSource}</code> — số liệu BCTC đã lưu, không hard-code.
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
            <label>VSIC Code</label>
            <input value={form.vsic_code} onChange={(e) => handleChange('vsic_code', e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Operating revenue (VND)</label>
            <input type="number" value={form.operating_revenue} onChange={(e) => handleChange('operating_revenue', e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Profit before tax (VND)</label>
            <input type="number" value={form.profit_before_tax} onChange={(e) => handleChange('profit_before_tax', e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Number of employees</label>
            <input type="number" value={form.employees} onChange={(e) => handleChange('employees', e.target.value)} required />
          </div>
        </div>

        <div className="singstat-form-block">
          <div className="form-group">
            <label>Operating expenses (VND)</label>
            <input
              type="number"
              value={form.operating_expenses}
              onChange={(e) => handleChange('operating_expenses', e.target.value)}
            />
          </div>
          <p className="singstat-of-which">Of which</p>
          <div className="form-grid singstat-of-which-grid">
            <div className="form-group">
              <label>Cost of goods &amp; materials (VND)</label>
              <input type="number" value={form.cost_of_goods} onChange={(e) => handleChange('cost_of_goods', e.target.value)} />
            </div>
            <div className="form-group">
              <label>Rental cost of premises (VND)</label>
              <input type="number" value={form.rental_cost} onChange={(e) => handleChange('rental_cost', e.target.value)} />
            </div>
            <div className="form-group">
              <label>Remuneration (VND)</label>
              <input type="number" value={form.remuneration} onChange={(e) => handleChange('remuneration', e.target.value)} />
            </div>
          </div>
        </div>

        <div className="form-grid" style={{ marginTop: 8 }}>
          <div className="form-group">
            <label>Total assets (VND)</label>
            <input type="number" value={form.total_assets} onChange={(e) => handleChange('total_assets', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Total equity (VND)</label>
            <input type="number" value={form.total_equity} onChange={(e) => handleChange('total_equity', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Current assets (VND)</label>
            <input type="number" value={form.current_assets} onChange={(e) => handleChange('current_assets', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Current liabilities (VND)</label>
            <input type="number" value={form.current_liabilities} onChange={(e) => handleChange('current_liabilities', e.target.value)} />
          </div>
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: 16 }}>
          {loading ? 'Đang so sánh...' : 'Compare Benchmark'}
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
              Peer scope: <strong>{result.peer_scope || '—'}</strong>
              {' · '}
              Số peer BCTC: <strong>{result.peer_count ?? 0}</strong>
              {insufficientPeers && (
                <>
                  {' '}
                  <span className="badge badge-warning">insufficient_peers</span>
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
                Thiếu peer cùng phân ngành — percentile = N/A (không bịa 50th).
                Chỉ số DN (nếu đủ input) vẫn tính từ form; TB ngành / xếp hạng để trống.
              </div>
            )}
            <div className="singstat-jump">
              <button
                type="button"
                className="singstat-jump-btn"
                onClick={() => scrollToId('singstat-expenditure')}
              >
                Compare Expenditure Related Ratio
              </button>
              <button
                type="button"
                className="singstat-jump-btn"
                onClick={() => scrollToId('singstat-kpi')}
              >
                Compare Performance by Percentile
              </button>
            </div>
          </div>

          <div id="singstat-kpi">
            {metricEntries.length === 0 ? (
              <div className="empty-state">
                Không có metric tính được từ input hiện tại — bổ sung BCTC (assets/equity/…) hoặc prefill RAL.
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
                      <div className="value" style={{ fontSize: 22 }}>
                        {formatRatio(value)}
                      </div>
                      {pct != null ? (
                        <>
                          <div className="sub">Percentile: {pct}%</div>
                          <div className="percentile-bar">
                            <div className="percentile-fill" style={{ width: `${pct}%` }} />
                          </div>
                        </>
                      ) : (
                        <div className="sub">Percentile: N/A (thiếu mẫu peer)</div>
                      )}
                      <div style={{ fontSize: 12, color: '#888', marginTop: 8 }}>
                        TB ngành: {indAvg != null ? formatRatio(indAvg) : 'N/A'}
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
              <h3 className="singstat-section-title">Expenditure-Related Ratio</h3>
              <p className="singstat-section-note">
                Operating expenses ÷ operating revenue. Industry from peer averages; N/A when missing — not shown as 0%.
              </p>
            </header>

            <div className="singstat-donut-row">
              <ShareDonut
                label="Industry"
                value={avg.expenditure_related_ratio}
                tone="industry"
              />
              <ShareDonut
                label="Your firm"
                value={result.expenditure_related_ratio}
                tone="firm"
              />
            </div>

            <div className="singstat-legend">
              <span className="singstat-legend-item">
                <i className="singstat-swatch singstat-swatch--industry" /> Industry
              </span>
              <span className="singstat-legend-item">
                <i className="singstat-swatch singstat-swatch--firm" /> Your firm
              </span>
            </div>

            <header className="singstat-section-head" style={{ marginTop: 28 }}>
              <h3 className="singstat-section-title">Key Expenditure Ratio</h3>
              <p className="singstat-section-note">
                Share of operating expenses. Bars use API shares only; missing values stay N/A.
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
                Expenditure comparison:{' '}
                {COMPARISON_LABELS[result.comparison?.expenditure_related_ratio]
                  || result.comparison?.expenditure_related_ratio
                  || '—'}
                {formatSharePct(result.expenditure_related_ratio) != null && (
                  <> · Firm ERR {formatSharePct(result.expenditure_related_ratio)}</>
                )}
              </p>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
