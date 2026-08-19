import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api'
import { formatMoney, formatGrouped, formatIndex } from '../format'
import SampleHonestyBanner from '../SampleHonestyBanner'

function formatVND(n) {
  return formatMoney(n, 'VND')
}

function periodLabel(p) {
  if (!p) return ''
  return String(p).slice(0, 10)
}

function bctcSourceKind(url) {
  if (!url) return null
  const u = String(url).toLowerCase()
  if (u.includes('cafef')) return 'cafef'
  if (u.startsWith('seed:')) return 'seed'
  if (u.startsWith('fallback:')) return 'fallback'
  if (u.startsWith('http')) return 'live'
  return 'other'
}

function isHttpUrl(url) {
  if (!url) return false
  const u = String(url).toLowerCase()
  return u.startsWith('http://') || u.startsWith('https://')
}

function latestByPeriod(rows) {
  if (!rows?.length) return null
  return [...rows].sort((a, b) => new Date(b.period) - new Date(a.period))[0]
}

/** Prefer CafeF HTTP source when present; otherwise newest period (may be seed). */
function pickPreferredFinancial(rows) {
  if (!rows?.length) return null
  const cafefRows = rows.filter((r) => bctcSourceKind(r.source_url) === 'cafef')
  if (cafefRows.length) return latestByPeriod(cafefRows)
  return latestByPeriod(rows)
}

function bctcSourceDisplay(url) {
  const kind = bctcSourceKind(url)
  if (kind === 'cafef') {
    return {
      kind,
      label: 'CafeF',
      href: isHttpUrl(url) ? url : null,
    }
  }
  if (kind === 'seed') {
    return { kind, label: 'seed (BCTC mẫu)', href: null }
  }
  if (kind === 'fallback') {
    return { kind, label: 'fallback', href: null }
  }
  if (kind === 'live') {
    return {
      kind,
      label: 'live',
      href: isHttpUrl(url) ? url : null,
    }
  }
  if (isHttpUrl(url)) {
    return { kind: kind || 'other', label: 'HTTP', href: url }
  }
  return { kind: kind || 'unknown', label: kind || 'unknown', href: null }
}

function formatWhen(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('vi-VN')
  } catch {
    return String(iso)
  }
}

/** Map API data-quality notes to plain Vietnamese (no jargon, no "/"). */
function humanizeQualityNote(note) {
  const raw = String(note || '').replace(/\s+/g, ' ').trim()
  if (!raw) return ''

  if (raw.startsWith('Điểm chất lượng')) {
    return 'Điểm này cho biết dữ liệu kênh bán và sản phẩm trên sàn đã được thu thập và xác minh đến đâu. Nó không đo mức độ chính xác của doanh thu thị trường.'
  }
  if (raw.includes('digital_presence') && (raw.includes('Shopee') || raw.includes('TikTok') || raw.includes('Lazada'))) {
    return 'Chưa ghi nhận gian hàng trên Shopee, TikTok hay Lazada. Hệ thống chỉ hiển thị kênh khi đã có bằng chứng, không tự thêm.'
  }
  if (raw.includes('listing') && (raw.includes('Shopee') || raw.includes('online est'))) {
    return 'Chưa có sản phẩm nào trên Shopee, TikTok hay Lazada. Ước tính doanh thu online có thể bằng 0.'
  }
  if (raw.includes('Website URL') || raw.includes('digital_presence.website')) {
    return 'Hồ sơ có địa chỉ website, nhưng chưa xác minh được kênh website đang hoạt động.'
  }
  if (raw.includes('Thiếu kênh website')) {
    return 'Chưa có kênh website đã được xác minh.'
  }
  if (raw.includes('match_confidence')) {
    return 'Chưa có điểm tin cậy khớp tên cho các kênh đang hoạt động.'
  }
  if (raw.includes('Listing marketplace') || raw.includes('price×units') || raw.includes('revenue_est')) {
    const m = raw.match(/\((\d+)\s*\/\s*(\d+)\s*đủ\)/)
    if (m) {
      return `Một số sản phẩm trên sàn còn thiếu giá hoặc số lượng bán (đã đủ ${m[1]} trên ${m[2]} sản phẩm).`
    }
    return 'Một số sản phẩm trên sàn còn thiếu giá hoặc số lượng bán.'
  }
  if (raw.includes('digital_metrics') || raw.includes('compute_all_digital_metrics')) {
    return 'Chưa có chỉ số số hóa đã tính. Cần chạy bước tính chỉ số số hóa trong quy trình dữ liệu.'
  }

  // Fallback: strip slashes and soften obvious technical tokens
  return raw
    .replace(/\//g, ' · ')
    .replace(/digital_presence/gi, 'dữ liệu kênh số')
    .replace(/digital_metrics/gi, 'chỉ số số hóa')
    .replace(/online est\.?/gi, 'ước tính doanh thu online')
    .replace(/match_confidence/gi, 'điểm tin cậy khớp tên')
}

const CHANNEL_ORDER = ['website', 'shopee', 'tiktok', 'lazada']

export default function CompanyDetail() {
  const { code } = useParams()
  const [company, setCompany] = useState(null)
  const [coverageNote, setCoverageNote] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [listingVsic, setListingVsic] = useState({})

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setListingVsic({})
    Promise.all([
      api.getCompany(code),
      api.getUniverseCoverage().catch(() => null),
    ])
      .then(([data, cov]) => {
        if (!cancelled) {
          setCompany(data)
          setCoverageNote(cov)
        }
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

  useEffect(() => {
    if (!company) {
      setListingVsic({})
      return
    }
    const listings = (company.marketplace_listings || []).filter((ml) =>
      ['shopee', 'tiktok', 'lazada'].includes(String(ml.platform || '').toLowerCase()),
    )
    const ac = new AbortController()
    let cancelled = false
    setListingVsic({})

    Promise.all(
      listings.map(async (ml) => {
        const name = String(ml.product_name || '').trim()
        if (!name) {
          return [ml.id, { vsic_code: null, reason: 'chưa phân loại' }]
        }
        try {
          const res = await api.categorizeProduct(name, { signal: ac.signal })
          return [ml.id, res]
        } catch {
          if (ac.signal.aborted) return null
          return [ml.id, { vsic_code: null, reason: 'chưa phân loại' }]
        }
      }),
    ).then((rows) => {
      if (cancelled) return
      const next = {}
      for (const row of rows) {
        if (row) next[row[0]] = row[1]
      }
      setListingVsic(next)
    })

    return () => {
      cancelled = true
      ac.abort()
    }
  }, [company])

  if (loading) return <div className="loading">Đang tải...</div>
  if (error || !company) {
    return (
      <div>
        <Link to="/companies">← Quay lại</Link>
        <div className="empty-state mt-md">
          {error || 'Không tìm thấy doanh nghiệp'}
        </div>
      </div>
    )
  }

  const latestFin = pickPreferredFinancial(company.financial_reports)
  const finSource = latestFin ? bctcSourceDisplay(latestFin.source_url) : null
  const latestMetric = latestByPeriod(company.digital_metrics)
  const presence = company.digital_presence || []
  const listings = company.marketplace_listings || []
  const mktListings = listings.filter((ml) =>
    ['shopee', 'tiktok', 'lazada'].includes(String(ml.platform || '').toLowerCase())
  )
  const quality = company.data_quality
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

  // Null revenue must not become 0 on the chart (honesty — missing ≠ zero).
  const productData = mktListings
    .filter((ml) => ml.revenue_est != null)
    .map((ml) => ({
      name: (ml.product_name || ml.platform || '').slice(0, 22),
      revenue: ml.revenue_est,
    }))

  const qualityBadge =
    quality?.status === 'ok'
      ? 'badge-success'
      : quality?.status === 'partial'
        ? 'badge-warning'
        : 'badge-warning'

  return (
    <div>
      <div className="page-nav">
        <Link to="/companies" className="page-nav-back">
          ← Quay lại danh sách
        </Link>
        {company.vsic_division && (
          <div className="page-nav-actions">
            <Link
              to={`/companies?vsic=${company.vsic_division}`}
              className="page-nav-chip"
            >
              Peer cùng ngành (VSIC {company.vsic_division})
            </Link>
            <Link
              to={`/benchmark?vsic=${company.vsic_code || company.vsic_division}`}
              className="page-nav-chip page-nav-chip--accent"
            >
              So sánh benchmark ngành
            </Link>
          </div>
        )}
      </div>

      <div className="company-header mt-md">
        <div>
          <h2>{company.name} ({company.stock_code})</h2>
          <p className="muted-text mt-sm">{company.description || '—'}</p>
          <div className="metric-strip mt-sm mb-0">
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

      <SampleHonestyBanner
        className="mt-md mb-md"
        coverageNote={coverageNote}
      />

      <div className="chart-container story-panel">
        <h3>Câu chuyện số liệu</h3>
        <ol className="narrative-list">
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
          <div className="peer-list" role="list">
            {company.peers.map((p) => (
              <div className="peer-row" role="listitem" key={p.stock_code}>
                <Link className="peer-ticker" to={`/companies/${p.stock_code}`}>
                  {p.stock_code}
                </Link>
                <div className="peer-meta">
                  <span className="peer-name">{p.name}</span>
                  {p.vsic_code && (
                    <span className="peer-vsic">VSIC {p.vsic_code}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="cards">
        <div className="card">
          <div className="label">Doanh thu (BCTC)</div>
          <div className="value" style={{ fontSize: 20 }}>{formatVND(latestFin?.revenue)}</div>
          <div className="sub muted">{latestFin ? periodLabel(latestFin.period) : 'Chưa có BCTC'}</div>
          {latestFin && finSource && (
            <div className="sub muted">
              Nguồn:{' '}
              {finSource.href ? (
                <a href={finSource.href} target="_blank" rel="noreferrer">
                  {finSource.label === 'CafeF' ? 'Xem trên CafeF' : finSource.label}
                </a>
              ) : (
                finSource.label
              )}
              {latestFin.report_type ? ` · ${latestFin.report_type}` : ''}
              {finSource.kind === 'seed' || finSource.kind === 'fallback'
                ? ' — chưa phải kỳ CafeF live'
                : ''}
            </div>
          )}
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
          <div className="sub muted">
            Industry-ratio chưa áp — online chỉ từ listing
          </div>
        </div>
        <div className="card">
          <div className="label">
            Digital VA{' '}
            <span className="badge badge-warning">mẫu ~28</span>
          </div>
          <div className="value" style={{ fontSize: 20 }}>
            {formatVND(latestMetric?.digital_va_contribution)}
          </div>
          <div className="sub muted">Công thức CONTEXT — không đổi · không phải VA_C GSO</div>
        </div>
        <div className="card">
          <div className="label">Đóng góp ngành (Digital VA)</div>
          <div className="value" style={{ fontSize: 20 }}>
            {latestMetric?.industry_share_pct != null
              ? formatIndex(latestMetric.industry_share_pct, { suffix: '%' })
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

      <div className="chart-container">
        <h3>Listing marketplace (ước lượng)</h3>
        {mktListings.length === 0 ? (
          <div className="empty-state">
            Không có listing Shopee/TikTok/Lazada cho {company.stock_code}.
            Doanh thu online ước tính dựa trên listing đã thu thập.
          </div>
        ) : (
          <>
            <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Nền tảng</th>
                  <th>Sản phẩm</th>
                  <th>VSIC dự đoán</th>
                  <th>Giá</th>
                  <th>Units est.</th>
                  <th>Revenue est.</th>
                  <th>Rating</th>
                  <th>Nguồn</th>
                  <th>Crawl</th>
                </tr>
              </thead>
              <tbody>
                {mktListings.map((ml) => {
                  const src = (ml.source || 'seed').toLowerCase()
                  const badgeClass =
                    src === 'live'
                      ? 'badge-success'
                      : src === 'fallback'
                        ? 'badge-warning'
                        : 'badge-info'
                  return (
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
                    <td>
                      {listingVsic[ml.id]?.vsic_code ? (
                        listingVsic[ml.id].vsic_code
                      ) : (
                        <span
                          className="muted-text"
                          title={listingVsic[ml.id]?.reason || 'chưa phân loại'}
                        >
                          —
                        </span>
                      )}
                    </td>
                    <td>{ml.price != null ? formatVND(ml.price) : '—'}</td>
                    <td>{ml.units_sold_est != null ? formatGrouped(ml.units_sold_est) : '—'}</td>
                    <td>{formatVND(ml.revenue_est)}</td>
                    <td>{ml.rating != null ? formatIndex(ml.rating) : '—'}</td>
                    <td>
                      <span className={`badge ${badgeClass}`}>{src}</span>
                    </td>
                    <td>{formatWhen(ml.crawled_at)}</td>
                  </tr>
                  )
                })}
              </tbody>
            </table>
            </div>
            <p className="chart-note">
              Badge nguồn ∈ live|seed|fallback. Nhãn <strong>live</strong> có thể lấy từ{' '}
              <strong>bản cache allowlist</strong> (ADR-0002) khi sàn chặn scrape — chưa chắc
              vừa scrape được trong lần chạy này; không phải doanh thu kiểm toán. Thiếu
              units/revenue hiện «—», không điền 0.
            </p>
            {productData.length > 0 && (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={productData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip formatter={(v) => formatVND(v)} />
                  <Bar dataKey="revenue" fill="#367ea2" name="Revenue est." />
                </BarChart>
              </ResponsiveContainer>
            )}
            {mktListings.length > 0 && productData.length === 0 && (
              <p className="chart-note">
                Có listing nhưng chưa có revenue_est — không vẽ cột giả = 0.
              </p>
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
                  <strong>{k}</strong> {formatIndex(v)}
                </span>
              ))}
            </div>
            {(quality.notes || []).length > 0 && (
              <div className="note-stack" role="list">
                {(quality.notes || []).map((n) => {
                  const text = humanizeQualityNote(n)
                  if (!text) return null
                  return (
                    <p className="info-note" role="listitem" key={n}>
                      {text}
                    </p>
                  )
                })}
              </div>
            )}
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
          <div className="table-scroll">
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
                  <td style={{ fontSize: 12, color: 'var(--muted)' }}>{ev.detail || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
        <p className="chart-note">
          Timeline suy ra từ timestamp từng dòng đã lưu (overwrite khi crawl lại) —
          chưa phải nhật ký append-only toàn cục (Module 3 pipeline).
        </p>
      </div>
    </div>
  )
}
