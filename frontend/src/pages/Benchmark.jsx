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

const RAL_DEFAULTS = {
  vsic_code: '2740',
  operating_revenue: 5200000000000,
  profit_before_tax: 420000000000,
  employees: 3200,
  operating_expenses: 4500000000000,
  cost_of_goods: 3200000000000,
  rental_cost: 85000000000,
  remuneration: 680000000000,
  total_assets: 6800000000000,
  total_equity: 3200000000000,
  current_assets: 3100000000000,
  current_liabilities: 2100000000000,
}

function formatRatio(value) {
  if (value == null) return '—'
  if (typeof value !== 'number') return value
  if (value < 10) return `${(value * 100).toFixed(1)}%`
  return value.toLocaleString()
}

export default function Benchmark() {
  const [form, setForm] = useState({ ...RAL_DEFAULTS })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (field, value) => {
    setForm((prev) => ({
      ...prev,
      [field]: field === 'vsic_code' ? value : Number(value) || value,
    }))
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

  const loadRangDong = () => {
    setForm({ ...RAL_DEFAULTS })
    setError(null)
  }

  const loadPrefill = async (stockCode) => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.benchmarkPrefill(stockCode)
      setForm({
        vsic_code: data.vsic_code,
        operating_revenue: data.operating_revenue,
        profit_before_tax: data.profit_before_tax,
        employees: data.employees,
        operating_expenses: data.operating_expenses ?? '',
        cost_of_goods: data.cost_of_goods ?? '',
        rental_cost: data.rental_cost ?? '',
        remuneration: data.remuneration ?? '',
        total_assets: data.total_assets ?? '',
        total_equity: data.total_equity ?? '',
        current_assets: data.current_assets ?? '',
        current_liabilities: data.current_liabilities ?? '',
      })
    } catch (err) {
      console.error(err)
      setError(err.message || `Không nạp được ${stockCode}.`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2 className="page-title">Benchmark My Performance</h2>
      <p style={{ color: '#888', marginBottom: 24 }}>
        So sánh hiệu quả doanh nghiệp với peer cùng phân ngành VSIC (tham chiếu UX SingStat BITE).
        Percentile lấy từ BCTC seed — thiếu mẫu thì để trống, không bịa.
      </p>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        <button type="button" className="btn btn-primary" onClick={loadRangDong}>
          Nạp dữ liệu Rạng Đông (RAL)
        </button>
        <button type="button" className="btn" onClick={() => loadPrefill('REE')} disabled={loading}>
          Nạp REE (cùng ngành 27)
        </button>
      </div>

      <form onSubmit={handleSubmit} className="chart-container">
        <div className="form-grid">
          <div className="form-group">
            <label>VSIC Code</label>
            <input value={form.vsic_code} onChange={(e) => handleChange('vsic_code', e.target.value)} />
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
        <div className="chart-container" style={{ marginTop: 16, color: '#b42318' }}>
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
            </div>
            {(result.warnings || []).length > 0 && (
              <ul style={{ margin: '8px 0 0', paddingLeft: 18, color: '#888', fontSize: 13 }}>
                {result.warnings.map((w) => (
                  <li key={w}>{WARNING_LABELS[w] || w}</li>
                ))}
              </ul>
            )}
          </div>

          <div className="cards">
            {Object.entries(METRIC_LABELS).map(([key, label]) => {
              const value = result[key]
              const pct = result.percentiles?.[key]
              const comp = result.comparison?.[key]
              const avg = result.industry_averages?.[key]
              if (value == null) return null
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
        </div>
      )}
    </div>
  )
}
