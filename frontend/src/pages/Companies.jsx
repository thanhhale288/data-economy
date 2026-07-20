import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function Companies() {
  const [companies, setCompanies] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    api.getCompanies()
      .then((data) => {
        if (!cancelled) setCompanies(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Không tải được danh sách')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="loading">Đang tải...</div>

  if (error) {
    return (
      <div>
        <h2 className="page-title">Doanh nghiệp niêm yết — Mẫu 10 DN</h2>
        <div className="empty-state">{error}</div>
      </div>
    )
  }

  return (
    <div>
      <h2 className="page-title">Doanh nghiệp niêm yết — Mẫu 10 DN</h2>
      <p className="chart-note" style={{ marginTop: -8, marginBottom: 16 }}>
        Hồ sơ số: website / Shopee / TikTok + ước lượng online. Case study nổi bật:{' '}
        <Link to="/companies/RAL">Rạng Đông (RAL)</Link>.
      </p>
      {companies.length === 0 ? (
        <div className="empty-state">
          Chưa có DN trong DB — chạy seed (`PYTHONPATH=. python -m backend.app.seed`).
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Mã CK</th>
              <th>Tên</th>
              <th>VSIC</th>
              <th>Website</th>
              <th>TMĐT</th>
              <th>Kênh số</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {companies.map((c) => {
              const isRal = c.stock_code === 'RAL'
              const channels = c.digital_channels
                ? Object.entries(c.digital_channels)
                    .filter(([, v]) => v)
                    .map(([k]) => k)
                    .join(', ')
                : ''
              return (
                <tr key={c.stock_code} style={isRal ? { background: '#fff8f9' } : undefined}>
                  <td>
                    <strong>{c.stock_code}</strong>
                    {isRal && (
                      <span className="badge badge-info" style={{ marginLeft: 6 }}>
                        Case study
                      </span>
                    )}
                  </td>
                  <td>{c.name}</td>
                  <td>{c.vsic_code}</td>
                  <td>
                    {c.website_url ? (
                      <a href={c.website_url} target="_blank" rel="noreferrer">Link</a>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td>
                    <span className={`badge ${c.has_ecommerce_site ? 'badge-success' : 'badge-warning'}`}>
                      {c.has_ecommerce_site ? 'Có' : 'Không'}
                    </span>
                  </td>
                  <td>{channels || '—'}</td>
                  <td>
                    <Link to={`/companies/${c.stock_code}`}>Chi tiết →</Link>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
