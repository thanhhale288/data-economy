import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { formatMoney } from '../format'

export default function Companies() {
  const [searchParams] = useSearchParams()
  const vsicFilter = searchParams.get('vsic') || ''
  const contributorsOnly = searchParams.get('contributors') === '1'
  const [companies, setCompanies] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    api.getCompanies(vsicFilter || undefined, contributorsOnly)
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
  }, [vsicFilter, contributorsOnly])

  const title = useMemo(() => {
    if (!vsicFilter) return `Doanh nghiệp niêm yết — Mẫu ${companies.length || '…'} doanh nghiệp`
    if (contributorsOnly) {
      return `Doanh nghiệp đóng góp giá trị gia tăng số — VSIC ${vsicFilter} (${companies.length} doanh nghiệp)`
    }
    return `Doanh nghiệp — VSIC ${vsicFilter} (${companies.length} doanh nghiệp)`
  }, [vsicFilter, companies.length, contributorsOnly])

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
      <p className="page-subtitle">
        Mẫu doanh nghiệp niêm yết trong nền tảng — VSIC peer filter không bịa doanh nghiệp ngoài seed.
      </p>
      {vsicFilter ? (
        <div className="page-nav-actions filter-actions" role="group" aria-label="Thao tác bộ lọc VSIC">
          <Link to="/#dashboard-heatmap" className="page-nav-chip">
            ← Quay lại Dashboard
          </Link>
          <Link to="/companies" className="page-nav-chip">
            Xóa bộ lọc VSIC {vsicFilter}
            {contributorsOnly ? ' · chỉ đóng góp' : ''}
          </Link>
          <Link
            to={`/benchmark?vsic=${vsicFilter}`}
            className="page-nav-chip page-nav-chip--accent"
          >
            So sánh benchmark ngành {vsicFilter}
          </Link>
        </div>
      ) : null}
      {contributorsOnly && (
        <p className="chart-note" style={{ marginTop: 0 }}>
          Chỉ hiện doanh nghiệp có giá trị gia tăng số &gt; 0 trong mã VSIC này (từ heatmap Dashboard).
          Tỷ trọng = đóng góp doanh nghiệp ÷ tổng đóng góp các doanh nghiệp đang liệt kê.
        </p>
      )}
      {companies.length === 0 ? (
        <div className="empty-state">
          {vsicFilter
            ? contributorsOnly
              ? `Không có doanh nghiệp có đóng góp giá trị gia tăng số với VSIC «${vsicFilter}» trong mẫu.`
              : `Không có doanh nghiệp với VSIC/division «${vsicFilter}» trong mẫu — không bịa peer.`
            : 'Chưa có doanh nghiệp trong DB — chạy seed (`PYTHONPATH=. python -m backend.app.seed`).'}
        </div>
      ) : (
        <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Mã CK</th>
              <th>Tên</th>
              <th>VSIC</th>
              {contributorsOnly && <th>Giá trị gia tăng số</th>}
              {contributorsOnly && <th>Tỷ trọng</th>}
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
                    <Link to={`/companies?vsic=${encodeURIComponent(c.vsic_code || '')}`}>
                      {c.vsic_code}
                    </Link>
                  </td>
                  {contributorsOnly && (
                    <td>
                      {c.digital_va_contribution != null
                        ? formatMoney(c.digital_va_contribution, 'VND')
                        : '—'}
                    </td>
                  )}
                  {contributorsOnly && (
                    <td>
                      {c.digital_va_share_pct != null
                        ? `${Number(c.digital_va_share_pct).toFixed(1)}%`
                        : '—'}
                    </td>
                  )}
                  <td>
                    {c.website_url ? (
                      <a href={c.website_url} target="_blank" rel="noreferrer">
                        {c.website_url.replace(/^https?:\/\//, '')}
                      </a>
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
