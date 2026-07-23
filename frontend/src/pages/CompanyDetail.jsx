import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api'
import { formatCompactVnd, formatGrouped } from '../format'

function formatVND(n) {
  return formatCompactVnd(n)
}

function periodLabel(p) {
  if (!p) return ''
  return String(p).slice(0, 10)
}

function formatWhen(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('vi-VN')
  } catch {
    return String(iso)
  }
}

function latestByPeriod(rows) {
  if (!rows?.length) return null
  return [...rows].sort((a, b) => new Date(b.period) - new Date(a.period))[0]
}

const CHANNEL_ORDER = ['website', 'shopee', 'tiktok', 'lazada']

export default function CompanyDetail() {
  const { code } = useParams()
  const [company, setCompany] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    api.getCompany(code)
      .then((data) => {
        if (!cancelled) setCompany(data)
      })
      .catch((err) => {
        if (!cancelled) {
          setCompany(null)
          setError(err.message || 'Không tải được doanh nghiệp')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [code])

  if (loading) return <div className="loading">Đang tải...</div>
  if (error || !company) {
    return (
      <div>
        <Link to="/companies">← Quay lại</Link>
        <div className="empty-state" style={{ marginTop: 16 }}>
          {error || 'Không tìm thấy doanh nghiệp'}
        </div>
      </div>
    )
  }

  const latestFin = latestByPeriod(company.financial_reports)
  const latestMetric = latestByPeriod(company.digital_metrics)
  const presence = company.digital_presence || []
  const listings = company.marketplace_listings || []
  const mktListings = listings.filter((ml) =>
    ['shopee', 'tiktok', 'lazada'].includes(String(ml.platform || '').toLowerCase())
  )
  const quality = company.data_quality
  const caseStudy = company.case_study
  const timeline = company.crawl_timeline || []

  const channelFlags = company.digital_channels || {}
  const expectedChannels = CHANNEL_ORDER.filter(
    (ch) => channelFlags[ch] === true || presence.some((p) => p.channel_type === ch)
  )
  // Always show website / shopee / tiktok slots for Module 2 readability
  const channelSlots = ['website', 'shopee', 'tiktok'].map((ch) => {
    const dp = presence.find((p) => p.channel_type === ch)
    const flagged = channelFlags[ch] === true
    return { channel: ch, dp, flagged }
  })

  const channelData = presence.map((dp) => ({
    name: dp.channel_type,
    confidence: (dp.match_confidence || 0) * 100,
  }))

  const productData = mktListings.map((ml) => ({
    name: (ml.product_name || ml.platform || '').slice(0, 22),
    revenue: ml.revenue_est || 0,
  }))

  const qualityBadge =
    quality?.status === 'ok'
      ? 'badge-success'
      : quality?.status === 'partial'
        ? 'badge-warning'
        : 'badge-warning'

  return (
    <div>
      <Link to="/companies">← Quay lại danh sách</Link>
      {company.vsic_division && (
        <span style={{ marginLeft: 12 }}>
          <Link to={`/companies?vsic=${company.vsic_division}`}>
            Peer VSIC {company.vsic_division}
          </Link>
          {' · '}
          <Link to={`/benchmark?vsic=${company.vsic_code || company.vsic_division}`}>
            Benchmark ngành này
          </Link>
        </span>
      )}

      <div className="company-header" style={{ marginTop: 16 }}>
        <div>
          <h2>{company.name} ({company.stock_code})</h2>
          <p style={{ color: '#888', marginTop: 4 }}>{company.description || '—'}</p>
          <div className="metric-strip" style={{ marginTop: 12, marginBottom: 0 }}>
            <span className="metric-chip">
              <strong>Sàn</strong> {company.exchange}
            </span>
            <span className="metric-chip">
              <strong>VSIC</strong> {company.vsic_code}
              {company.vsic?.name_vi ? ` — ${company.vsic.name_vi}` : ''}
            </span>
            <span className="metric-chip">
              <strong>Website</strong>{' '}
              {company.website_url ? (
                <a href={company.website_url} target="_blank" rel="noreferrer">
                  {company.website_url.replace(/^https?:\/\//, '')}
                </a>
              ) : (
                '—'
              )}
            </span>
            <span className="metric-chip">
              <strong>TMĐT</strong>{' '}
              <span className={`badge ${company.has_ecommerce_site ? 'badge-success' : 'badge-warning'}`}>
                {company.has_ecommerce_site ? 'Có' : 'Không'}
              </span>
            </span>
          </div>
        </div>
      </div>

      {caseStudy && (
        <div className="chart-container" style={{ borderLeft: '4px solid #0d9488' }}>
          <h3>{caseStudy.title}</h3>
          <p className="chart-note" style={{ marginTop: 0 }}>
            Hồ sơ case study từ dữ liệu đã lưu trong hệ thống.
          </p>
          <ul style={{ margin: '8px 0 0', paddingLeft: 18, lineHeight: 1.6 }}>
            {caseStudy.highlights?.map((h) => (
              <li key={h}>{h}</li>
            ))}
          </ul>
          {caseStudy.notes?.length > 0 && (
            <div className="banner banner-warn" style={{ marginTop: 12 }}>
              {caseStudy.notes.join(' ')}
            </div>
          )}
        </div>
      )}

      <div className="chart-container" style={{ borderLeft: '4px solid var(--accent, #0f3460)' }}>
        <h3>Câu chuyện số liệu</h3>
        <ol style={{ margin: '8px 0 0', paddingLeft: 22, lineHeight: 1.65, fontSize: 14 }}>
          <li>
            <strong>Hiện diện số</strong> —{' '}
            {presence.length
              ? `${presence.filter((p) => p.is_active !== false).length} kênh đã ghi nhận.`
              : 'Chưa có digital_presence (không bịa kênh).'}
          </li>
          <li>
            <strong>Online estimate</strong> —{' '}
            {latestMetric?.online_revenue_est != null
              ? formatVND(latestMetric.online_revenue_est)
              : mktListings.length
                ? 'Có listing nhưng chưa có digital_metrics — chạy job metrics.'
                : 'Không có listing Shopee/TikTok/Lazada → online có thể = 0.'}
          </li>
          <li>
            <strong>Digital VA</strong> —{' '}
            {latestMetric?.digital_va_contribution != null
              ? formatVND(latestMetric.digital_va_contribution)
              : 'Chưa tính (thiếu metrics / margin). Công thức khóa trong CONTEXT.'}
          </li>
          <li>
            <strong>Chất lượng dữ liệu</strong> —{' '}
            {quality
              ? `${quality.score}/${quality.max_score} (${quality.status})`
              : 'Chưa có score.'}
          </li>
        </ol>
      </div>

      {(company.peers || []).length > 0 && (
        <div className="chart-container">
          <h3>Peer cùng phân ngành (VSIC {company.vsic_division})</h3>
          <p className="chart-note" style={{ marginTop: 0 }}>
            Mẫu niêm yết trong DB — percentile Benchmark dùng cùng phạm vi này.
          </p>
          <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.6 }}>
            {company.peers.map((p) => (
              <li key={p.stock_code}>
                <Link to={`/companies/${p.stock_code}`}>{p.stock_code}</Link>
                {' — '}
                {p.name}
                <span className="muted"> ({p.vsic_code})</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="cards">
        <div className="card">
          <div className="label">Doanh thu (BCTC)</div>
          <div className="value" style={{ fontSize: 20 }}>{formatVND(latestFin?.revenue)}</div>
          <div className="sub muted">{latestFin ? periodLabel(latestFin.period) : 'Chưa có BCTC'}</div>
        </div>
        <div className="card">
          <div className="label">Doanh thu TMĐT (ước tính)</div>
          <div className="value" style={{ fontSize: 20 }}>
            {formatVND(latestMetric?.online_revenue_est)}
          </div>
          <div className="sub muted">
            {latestMetric
              ? `Kỳ ${periodLabel(latestMetric.period)} · chỉ listing Shopee/TikTok/Lazada`
              : 'Chưa có digital_metrics'}
          </div>
        </div>
        <div className="card">
          <div className="label">Digital VA</div>
          <div className="value" style={{ fontSize: 20 }}>
            {formatVND(latestMetric?.digital_va_contribution)}
          </div>
          <div className="sub muted">Công thức CONTEXT — không đổi</div>
        </div>
        <div className="card">
          <div className="label">Đóng góp ngành (Digital VA)</div>
          <div className="value" style={{ fontSize: 20 }}>
            {latestMetric?.industry_share_pct != null
              ? `${latestMetric.industry_share_pct.toFixed(1)}%`
              : '—'}
          </div>
          <div className="sub muted">Tỷ trọng trong nhóm VSIC cùng mẫu</div>
        </div>
      </div>

      {!latestFin && (
        <div className="banner banner-warn">
          Chưa có BCTC (financial_reports) cho {company.stock_code}. Chạy crawl/seed tài chính.
        </div>
      )}
      {!latestMetric && (
        <div className="banner banner-warn">
          Chưa có chỉ số digital_metrics cho DN này. Chạy job metrics /{' '}
          <code>make bootstrap</code>.
        </div>
      )}

      <div className="chart-container">
        <h3>Kênh bán số</h3>
        <p className="chart-note" style={{ marginTop: 0 }}>
          Website / Shopee / TikTok — trạng thái từ digital_presence (vắng mặt = chưa có dữ liệu).
        </p>
        <div className="cards" style={{ marginBottom: 0 }}>
          {channelSlots.map(({ channel, dp, flagged }) => (
            <div className="card" key={channel}>
              <div className="label" style={{ textTransform: 'capitalize' }}>{channel}</div>
              {dp ? (
                <>
                  <div style={{ fontSize: 13, marginTop: 6, wordBreak: 'break-all' }}>
                    <a href={dp.url} target="_blank" rel="noreferrer">{dp.url}</a>
                  </div>
                  <div className="sub muted" style={{ marginTop: 8 }}>
                    Checkout: {dp.has_checkout ? 'Có' : 'Không'} · Confidence:{' '}
                    {dp.match_confidence != null
                      ? `${(dp.match_confidence * 100).toFixed(0)}%`
                      : '—'}
                  </div>
                  <div className="sub muted">Crawl: {formatWhen(dp.crawled_at)}</div>
                </>
              ) : (
                <div className="empty-state" style={{ marginTop: 8, padding: 12 }}>
                  {flagged
                    ? 'Flag kênh = true nhưng chưa có digital_presence.'
                    : 'Chưa có trong dữ liệu.'}
                </div>
              )}
            </div>
          ))}
        </div>
        {expectedChannels.length === 0 && presence.length === 0 && (
          <div className="empty-state" style={{ marginTop: 12 }}>
            Không có kênh bán số đã ghi nhận cho DN này.
          </div>
        )}
      </div>

      {channelData.length > 0 && (
        <div className="chart-container">
          <h3>Độ tin cậy match kênh</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={channelData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(v) => `${Number(v).toFixed(0)}%`} />
              <Bar dataKey="confidence" fill="#1e3a5f" name="Confidence %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="chart-container">
        <h3>Listing marketplace (ước lượng)</h3>
        {mktListings.length === 0 ? (
          <div className="empty-state">
            Không có listing Shopee/TikTok/Lazada cho {company.stock_code}.
            Doanh thu online ước tính dựa trên listing đã thu thập.
          </div>
        ) : (
          <>
            <table>
              <thead>
                <tr>
                  <th>Nền tảng</th>
                  <th>Sản phẩm</th>
                  <th>Giá</th>
                  <th>Units est.</th>
                  <th>Revenue est.</th>
                  <th>Rating</th>
                  <th>Crawl</th>
                </tr>
              </thead>
              <tbody>
                {mktListings.map((ml) => (
                  <tr key={ml.id}>
                    <td>{ml.platform}</td>
                    <td>
                      {ml.product_url ? (
                        <a href={ml.product_url} target="_blank" rel="noreferrer">
                          {ml.product_name}
                        </a>
                      ) : (
                        ml.product_name
                      )}
                    </td>
                    <td>{ml.price != null ? formatVND(ml.price) : '—'}</td>
                    <td>{ml.units_sold_est != null ? formatGrouped(ml.units_sold_est) : '—'}</td>
                    <td>{formatVND(ml.revenue_est)}</td>
                    <td>{ml.rating != null ? ml.rating.toFixed(1) : '—'}</td>
                    <td>{formatWhen(ml.crawled_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="chart-note">
              Ước lượng từ snapshot listing (seed/fallback khi live scrape tạm hoãn) —
              không phải doanh thu kiểm toán.
            </p>
            {productData.length > 0 && (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={productData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip formatter={(v) => formatVND(v)} />
                  <Bar dataKey="revenue" fill="#0d9488" name="Revenue est." />
                </BarChart>
              </ResponsiveContainer>
            )}
          </>
        )}
      </div>

      <div className="chart-container">
        <h3>
          Điểm chất liệu dữ liệu{' '}
          {quality && (
            <span className={`badge ${qualityBadge}`}>
              {quality.score}/{quality.max_score} · {quality.status}
            </span>
          )}
        </h3>
        {!quality ? (
          <div className="empty-state">Chưa có data_quality từ API.</div>
        ) : (
          <>
            <div className="metric-strip">
              {Object.entries(quality.components || {}).map(([k, v]) => (
                <span className="metric-chip" key={k}>
                  <strong>{k}</strong> {Number(v).toFixed(1)}
                </span>
              ))}
            </div>
            <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.55, fontSize: 13, color: '#555' }}>
              {(quality.notes || []).map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="chart-container">
        <h3>Timeline crawl (bằng chứng đã lưu)</h3>
        {timeline.length === 0 ? (
          <div className="empty-state">
            Chưa có mốc crawl từ digital_presence / marketplace_listings.
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Thời điểm</th>
                <th>Loại</th>
                <th>Nguồn</th>
                <th>Nhãn</th>
                <th>Trạng thái</th>
                <th>Chi tiết</th>
              </tr>
            </thead>
            <tbody>
              {timeline.map((ev, idx) => (
                <tr key={`${ev.event_type}-${ev.source}-${idx}`}>
                  <td>{formatWhen(ev.crawled_at)}</td>
                  <td>{ev.event_type}</td>
                  <td>{ev.source}</td>
                  <td>
                    {ev.url ? (
                      <a href={ev.url} target="_blank" rel="noreferrer">{ev.label}</a>
                    ) : (
                      ev.label
                    )}
                  </td>
                  <td>{ev.status}</td>
                  <td style={{ fontSize: 12, color: '#666' }}>{ev.detail || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="chart-note">
          Timeline suy ra từ timestamp từng dòng đã lưu (overwrite khi crawl lại) —
          chưa phải nhật ký append-only toàn cục (Module 3 pipeline).
        </p>
      </div>
    </div>
  )
}
