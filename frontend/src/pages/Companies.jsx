import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function Companies() {
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getCompanies()
      .then(setCompanies)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Đang tải...</div>

  return (
    <div>
      <h2 className="page-title">Doanh nghiệp niêm yết — Mẫu 10 DN</h2>
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
          {companies.map((c) => (
            <tr key={c.stock_code}>
              <td><strong>{c.stock_code}</strong></td>
              <td>{c.name}</td>
              <td>{c.vsic_code}</td>
              <td>{c.website_url ? <a href={c.website_url} target="_blank" rel="noreferrer">Link</a> : '—'}</td>
              <td>
                <span className={`badge ${c.has_ecommerce_site ? 'badge-success' : 'badge-warning'}`}>
                  {c.has_ecommerce_site ? 'Có' : 'Không'}
                </span>
              </td>
              <td>
                {c.digital_channels && Object.entries(c.digital_channels)
                  .filter(([, v]) => v)
                  .map(([k]) => k)
                  .join(', ') || '—'}
              </td>
              <td><Link to={`/companies/${c.stock_code}`}>Chi tiết →</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
