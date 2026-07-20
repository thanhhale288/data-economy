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
            <label>Doanh thu (VND)</label>
            <input type="number" value={form.operating_revenue} onChange={(e) => handleChange('operating_revenue', e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Lợi nhuận trước thuế (VND)</label>
            <input type="number" value={form.profit_before_tax} onChange={(e) => handleChange('profit_before_tax', e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Số nhân viên</label>
            <input type="number" value={form.employees} onChange={(e) => handleChange('employees', e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Giá vốn hàng bán (VND)</label>
            <input type="number" value={form.cost_of_goods} onChange={(e) => handleChange('cost_of_goods', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Chi phí thuê (VND)</label>
            <input type="number" value={form.rental_cost} onChange={(e) => handleChange('rental_cost', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Chi phí lương (VND)</label>
            <input type="number" value={form.remuneration} onChange={(e) => handleChange('remuneration', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Chi phí hoạt động (VND)</label>
            <input type="number" value={form.operating_expenses} onChange={(e) => handleChange('operating_expenses', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Tổng tài sản (VND)</label>
            <input type="number" value={form.total_assets} onChange={(e) => handleChange('total_assets', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Vốn chủ sở hữu (VND)</label>
            <input type="number" value={form.total_equity} onChange={(e) => handleChange('total_equity', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Tài sản ngắn hạn (VND)</label>
            <input type="number" value={form.current_assets} onChange={(e) => handleChange('current_assets', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Nợ ngắn hạn (VND)</label>
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
          </div>

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
                const avg = result.industry_averages?.[key]
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
                      TB ngành: {avg != null ? formatRatio(avg) : 'N/A'}
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
      )}
    </div>
  )
}
