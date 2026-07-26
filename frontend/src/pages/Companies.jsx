import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'

export default function Companies() {
  const [searchParams] = useSearchParams()
  const vsicFilter = searchParams.get('vsic') || ''
  const [companies, setCompanies] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    api.getCompanies(vsicFilter || undefined)
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
  }, [vsicFilter])

  const title = useMemo(() => {
    if (!vsicFilter) return `Doanh nghiệp niêm yết — Mẫu ${companies.length || '…'} DN`
    return `Doanh nghiệp — VSIC ${vsicFilter} (${companies.length} DN)`
  }, [vsicFilter, companies.length])

  if (loading) return <div className="loading">Đang tải...</div>

  if (error) {
    return (
      <div>
        <h2 className="page-title">{title}</h2>
        <div className="empty-state">{error}</div>
      </div>
    )
  }

  return (
    <div>
      <h2 className="page-title">{title}</h2>
      {vsicFilter ? (
        <div className="page-nav-actions filter-actions" role="group" aria-label="Thao tác bộ lọc VSIC">
          <Link to="/companies" className="page-nav-chip">
            Xóa bộ lọc VSIC {vsicFilter}
          </Link>
          <Link
            to={`/benchmark?vsic=${vsicFilter}`}
            className="page-nav-chip page-nav-chip--accent"
          >
            So sánh benchmark ngành {vsicFilter}
          </Link>
        </div>
      ) : null}
      {companies.length === 0 ? (
        <div className="empty-state">
          {vsicFilter
            ? `Không có DN với VSIC/division «${vsicFilter}» trong mẫu — không bịa peer.`
            : 'Chưa có DN trong DB — chạy seed (`PYTHONPATH=. python -m backend.app.seed`).'}
        </div>
      ) : (
        <div className="table-scroll">
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
              const channels = c.digital_channels
                ? Object.entries(c.digital_channels)
                    .filter(([, v]) => v)
                    .map(([k]) => k)
                    .join(', ')
                : ''
              return (
                <tr key={c.stock_code}>
                  <td>
                    <strong>{c.stock_code}</strong>
                  </td>
                  <td>{c.name}</td>
                  <td>
                    <Link to={`/companies?vsic=${String(c.vsic_code || '').slice(0, 2)}`}>
                      {c.vsic_code}
                    </Link>
                  </td>
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
                    <Link to={`/companies/${c.stock_code}`} className="link-action">Chi tiết →</Link>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        </div>
      )}
    </div>
  )
}
