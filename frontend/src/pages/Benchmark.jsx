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
  neutral: '—',
}

export default function Benchmark() {
  const [form, setForm] = useState({
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
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: Number(value) || value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await api.benchmark(form)
      setResult(res)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadRangDong = () => {
    setForm({
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
    })
  }

  return (
    <div>
      <h2 className="page-title">Benchmark My Performance</h2>
      <p style={{ color: '#888', marginBottom: 24 }}>
        So sánh hiệu quả doanh nghiệp với trung bình ngành (tham chiếu SingStat BITE)
      </p>

      <button className="btn btn-primary" onClick={loadRangDong} style={{ marginBottom: 16 }}>
        Nạp dữ liệu Rạng Đông (RAL)
      </button>

      <form onSubmit={handleSubmit} className="chart-container">
        <div className="form-grid">
          <div className="form-group">
            <label>VSIC Code</label>
            <input value={form.vsic_code} onChange={(e) => handleChange('vsic_code', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Doanh thu (VND)</label>
            <input type="number" value={form.operating_revenue} onChange={(e) => handleChange('operating_revenue', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Lợi nhuận trước thuế (VND)</label>
            <input type="number" value={form.profit_before_tax} onChange={(e) => handleChange('profit_before_tax', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Số nhân viên</label>
            <input type="number" value={form.employees} onChange={(e) => handleChange('employees', e.target.value)} />
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

      {result && (
        <div style={{ marginTop: 24 }}>
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
                    {typeof value === 'number' ? (value < 10 ? (value * 100).toFixed(1) + '%' : value.toLocaleString()) : value}
                  </div>
                  {pct != null && (
                    <>
                      <div className="sub">Percentile: {pct}%</div>
                      <div className="percentile-bar">
                        <div className="percentile-fill" style={{ width: `${pct}%` }} />
                      </div>
                    </>
                  )}
                  <div style={{ fontSize: 12, color: '#888', marginTop: 8 }}>
                    TB ngành: {avg != null ? (avg < 10 ? (avg * 100).toFixed(1) + '%' : avg.toLocaleString()) : '—'}
                  </div>
                  <div style={{ fontSize: 12, marginTop: 4 }}>
                    <span className={`badge ${comp === 'above_average' ? 'badge-success' : comp === 'below_average' ? 'badge-danger' : 'badge-warning'}`}>
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
