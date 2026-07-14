import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api'

function formatVND(n) {
  if (n == null) return '—'
  if (n >= 1e12) return `${(n / 1e12).toFixed(2)} nghìn tỷ`
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)} tỷ`
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)} triệu`
  return n.toLocaleString()
}

export default function CompanyDetail() {
  const { code } = useParams()
  const [company, setCompany] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getCompany(code)
      .then(setCompany)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [code])

  if (loading) return <div className="loading">Đang tải...</div>
  if (!company) return <div className="loading">Không tìm thấy doanh nghiệp</div>

  const latestFin = company.financial_reports?.sort(
    (a, b) => new Date(b.period) - new Date(a.period)
  )[0]
  const latestMetric = company.digital_metrics?.sort(
    (a, b) => new Date(b.period) - new Date(a.period)
  )[0]

  const channelData = company.digital_presence?.map((dp) => ({
    name: dp.channel_type,
    confidence: (dp.match_confidence || 0) * 100,
  })) || []

  const productData = company.marketplace_listings?.map((ml) => ({
    name: ml.product_name?.slice(0, 20),
    revenue: ml.revenue_est || 0,
  })) || []

  return (
    <div>
      <Link to="/companies">← Quay lại</Link>
      <div className="company-header" style={{ marginTop: 16 }}>
        <div>
          <h2>{company.name} ({company.stock_code})</h2>
          <p style={{ color: '#888', marginTop: 4 }}>{company.description}</p>
          <div className="channel-tags">
            {company.digital_presence?.map((dp) => (
              <span key={dp.id} className="badge badge-info">{dp.channel_type}</span>
            ))}
          </div>
        </div>
      </div>

      <div className="cards">
        <div className="card">
          <div className="label">Doanh thu</div>
          <div className="value" style={{ fontSize: 20 }}>{formatVND(latestFin?.revenue)}</div>
        </div>
        <div className="card">
          <div className="label">Doanh thu TMĐT (ước tính)</div>
          <div className="value" style={{ fontSize: 20 }}>{formatVND(latestMetric?.online_revenue_est)}</div>
        </div>
        <div className="card">
          <div className="label">Digital VA</div>
          <div className="value" style={{ fontSize: 20 }}>{formatVND(latestMetric?.digital_va_contribution)}</div>
        </div>
        <div className="card">
          <div className="label">Đóng góp ngành</div>
          <div className="value" style={{ fontSize: 20 }}>{latestMetric?.industry_share_pct?.toFixed(1) ?? '—'}%</div>
        </div>
      </div>

      <div className="chart-container">
        <h3>Hiện diện số — Độ tin cậy match</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={channelData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis domain={[0, 100]} />
            <Tooltip formatter={(v) => `${v.toFixed(0)}%`} />
            <Bar dataKey="confidence" fill="#0f3460" name="Confidence %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {productData.length > 0 && (
        <div className="chart-container">
          <h3>Doanh thu sản phẩm TMĐT (ước tính)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={productData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip formatter={(v) => formatVND(v)} />
              <Bar dataKey="revenue" fill="#e94560" name="Revenue" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="chart-container">
        <h3>Kênh bán số</h3>
        <table>
          <thead>
            <tr><th>Kênh</th><th>URL</th><th>Checkout</th><th>Confidence</th></tr>
          </thead>
          <tbody>
            {company.digital_presence?.map((dp) => (
              <tr key={dp.id}>
                <td>{dp.channel_type}</td>
                <td><a href={dp.url} target="_blank" rel="noreferrer">{dp.url}</a></td>
                <td>{dp.has_checkout ? '✓' : '—'}</td>
                <td>{dp.match_confidence ? `${(dp.match_confidence * 100).toFixed(0)}%` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
