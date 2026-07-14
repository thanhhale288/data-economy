import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar,
} from 'recharts'
import { api } from '../api'

function formatNumber(n) {
  if (n == null) return '—'
  if (n >= 1e12) return `${(n / 1e12).toFixed(1)}T`
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`
  return n.toLocaleString()
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [iip, setIip] = useState([])
  const [heatmap, setHeatmap] = useState([])
  const [oecdGso, setOecdGso] = useState({ gso: [], oecd: [] })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.getSummary(),
      api.getIip(),
      api.getHeatmap(),
      api.getOecdVsGso(),
    ])
      .then(([s, i, h, og]) => {
        setSummary(s)
        setIip(i)
        setHeatmap(h)
        setOecdGso(og)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Đang tải dữ liệu...</div>

  const combinedChart = oecdGso.gso.map((g, idx) => ({
    period: g.period?.slice(0, 7),
    gso: g.value,
    oecd: oecdGso.oecd[idx]?.value,
  }))

  return (
    <div>
      <h2 className="page-title">Dashboard — Công nghiệp Chế biến, Chế tạo</h2>

      <div className="cards">
        <div className="card">
          <div className="label">IIP (SXCN)</div>
          <div className="value">{summary?.iip_latest?.toFixed(1) ?? '—'}</div>
          {summary?.iip_growth_pct != null && (
            <div className="sub">{summary.iip_growth_pct > 0 ? '+' : ''}{summary.iip_growth_pct}%</div>
          )}
        </div>
        <div className="card">
          <div className="label">Doanh nghiệp</div>
          <div className="value">{summary?.total_companies ?? 0}</div>
          <div className="sub">{summary?.companies_with_ecommerce ?? 0} có TMĐT</div>
        </div>
        <div className="card">
          <div className="label">Digital Adoption</div>
          <div className="value">{summary?.avg_digital_adoption != null ? `${(summary.avg_digital_adoption * 100).toFixed(0)}%` : '—'}</div>
        </div>
        <div className="card">
          <div className="label">Tổng Digital VA</div>
          <div className="value">{formatNumber(summary?.total_digital_va)}</div>
        </div>
      </div>

      <div className="chart-container">
        <h3>Chỉ số SXCN (IIP) — Section C</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={iip}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" tick={{ fontSize: 11 }} />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#e94560" strokeWidth={2} dot={false} name="IIP" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-container">
        <h3>OECD Leading vs GSO Lagging</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={combinedChart}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" tick={{ fontSize: 11 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="gso" stroke="#e94560" strokeWidth={2} dot={false} name="GSO IIP" />
            <Line type="monotone" dataKey="oecd" stroke="#0f3460" strokeWidth={2} dot={false} name="OECD MEI" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-container">
        <h3>Đóng góp Kinh tế số theo ngành (VSIC)</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={heatmap}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="vsic_code" />
            <YAxis />
            <Tooltip formatter={(v) => formatNumber(v)} />
            <Bar dataKey="digital_va" fill="#e94560" name="Digital VA" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
