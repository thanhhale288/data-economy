import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { api } from '../api'
import { formatCompact } from '../format'
import MetricInfoTip from '../MetricInfoTip'

/** KPI help copy — formulas match CONTEXT.md / proposal-v2 (do not invent). */
const KPI_TIPS = {
  iip: {
    title: 'Chỉ số sản xuất công nghiệp (IIP / SXCN)',
    formula: 'Nguồn: GSO/NSO · chuỗi IIP_C (VSIC Section C)',
    blurb:
      'Đo mức sản xuất theo tháng của ngành chế biến, chế tạo. Đây là chỉ số công bố từ thống kê chính thức, không phải số do nền tảng tự tính.',
  },
  digitalVa: {
    title: 'Tổng Digital VA',
    formula:
      'Digital_VA = (Online_revenue × Gross_margin) + (Cost_savings × Adoption_score) − Digital_investment',
    blurb:
      'Tổng ước lượng giá trị gia tăng kinh tế số của các doanh nghiệp trong mẫu (cộng Digital VA từng DN). Không đồng nghĩa với doanh thu hay với IIP.',
  },
  adoption: {
    title: 'Digital Adoption',
    formula: 'Điểm tổng hợp kênh / checkout / hoạt động (0–1)',
    blurb:
      'Mức độ số hóa kênh bán trung bình của DN mẫu (website, sàn TMĐT, tín hiệu giao dịch…). Dùng trong tính Digital VA và các feature dự báo.',
  },
}

function formatNumber(n) {
  return formatCompact(n)
}

function periodLabel(p) {
  if (!p) return ''
  return String(p).slice(0, 7)
}

function heatRgb(intensity) {
  const t = Math.max(0, Math.min(1, intensity ?? 0))
  // blue scale — matches --accent (#367ea2)
  return {
    r: Math.round(255 - t * (255 - 54)),
    g: Math.round(255 - t * (255 - 126)),
    b: Math.round(255 - t * (255 - 162)),
  }
}

function heatColor(intensity) {
  const { r, g, b } = heatRgb(intensity)
  return `rgb(${r},${g},${b})`
}

/** WCAG relative luminance of sRGB channels (0–255). */
function relativeLuminance(r, g, b) {
  const channel = (c) => {
    const s = c / 255
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
}

/** Readable foreground for a heat cell — white on dark blues, ink on pale cells. */
function heatTextColor(intensity) {
  const { r, g, b } = heatRgb(intensity)
  // Threshold ~0.45 ≈ intensity ≳ 0.55 on this scale; keeps AA-ish contrast for muted meta.
  return relativeLuminance(r, g, b) < 0.45 ? '#ffffff' : '#164654'
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [iip, setIip] = useState([])
  const [heatmap, setHeatmap] = useState([])
  const [oecdGso, setOecdGso] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [forecastError, setForecastError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [s, i, h, og] = await Promise.all([
          api.getSummary(),
          api.getIip(),
          api.getHeatmap(),
          api.getOecdVsGso(),
        ])
        if (cancelled) return
        setSummary(s)
        setIip(i)
        setHeatmap(h)
        setOecdGso(og)

        const model = s?.preferred_forecast_model || 'xgboost'
        try {
          const fc = await api.forecast(model, 6)
          if (!cancelled) {
            setForecast(fc)
            setForecastError(null)
          }
        } catch (err) {
          if (!cancelled) {
            setForecast(null)
            setForecastError(
              err?.message?.includes('404')
                ? `Chưa có artifact forecast cho model «${model}» — chạy make bootstrap / train ML.`
                : `Không tải được forecast (${model}): ${err.message}`
            )
          }
        }
      } catch (err) {
        console.error(err)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="loading">Đang tải dữ liệu...</div>

  const iipChart = [
    ...iip.map((row) => ({
      period: periodLabel(row.period),
      actual: row.value,
      forecast: null,
    })),
    ...(forecast?.forecasts || []).map((row) => ({
      period: periodLabel(row.period),
      actual: null,
      forecast: row.predicted_value,
    })),
  ]

  // Bridge last actual → first forecast for a continuous dashed line
  if (iip.length && forecast?.forecasts?.length) {
    const lastActual = iip[iip.length - 1]
    const bridgeIdx = iip.length - 1
    if (iipChart[bridgeIdx]) {
      iipChart[bridgeIdx] = {
        ...iipChart[bridgeIdx],
        forecast: lastActual.value,
      }
    }
  }

  const aligned = oecdGso?.aligned?.length
    ? oecdGso.aligned.map((row) => ({
        period: periodLabel(row.period),
        gso: row.gso,
        oecd: row.oecd,
      }))
    : []

  const oecdMissing = oecdGso?.oecd_status === 'missing' || !oecdGso?.oecd?.length
  const periodText = summary?.latest_period
    ? periodLabel(summary.latest_period)
    : '—'

  return (
    <div>
      <h2 className="page-title">Dashboard — Công nghiệp Chế biến, Chế tạo</h2>
      <p className="page-subtitle">
        VSIC Section C · kỳ gần nhất {periodText}
        {summary?.preferred_forecast_model
          ? ` · forecast model: ${summary.preferred_forecast_model}`
          : ''}
      </p>

      {summary?.iip_latest == null && (
        <div className="banner banner-warn" style={{ marginBottom: 16 }}>
          Chưa có IIP Section C trong DB — chạy <code>make bootstrap</code> (seed + crawl GSO).
        </div>
      )}
      {!summary?.preferred_forecast_model && summary?.iip_latest != null && (
        <div className="banner banner-warn" style={{ marginBottom: 16 }}>
          Chưa có model active trong registry — chạy bootstrap/train ML trước khi xem dự báo.
        </div>
      )}

      <div className="cards cards-kpi">
        <div className="card">
          <div className="card-label-row">
            <div className="label">IIP (SXCN)</div>
            <MetricInfoTip {...KPI_TIPS.iip} />
          </div>
          <div className="value">{summary?.iip_latest?.toFixed(1) ?? '—'}</div>
          {summary?.iip_growth_pct != null && (
            <div className={`sub ${summary.iip_growth_pct >= 0 ? 'up' : 'down'}`}>
              {summary.iip_growth_pct > 0 ? '+' : ''}{summary.iip_growth_pct}% so với kỳ trước
            </div>
          )}
          {summary?.iip_latest == null && (
            <div className="sub muted">Chưa có chuỗi IIP</div>
          )}
        </div>
        <div className="card">
          <div className="label">Doanh nghiệp mẫu</div>
          <div className="value">{summary?.total_companies ?? 0}</div>
          <div className="sub">{summary?.companies_with_ecommerce ?? 0} có kênh TMĐT</div>
          <div className="sub muted">
            <Link to="/companies">Xem danh sách →</Link>
          </div>
        </div>
        <div className="card">
          <div className="card-label-row">
            <div className="label">Digital Adoption</div>
            <MetricInfoTip {...KPI_TIPS.adoption} />
          </div>
          <div className="value">
            {summary?.avg_digital_adoption != null
              ? `${(summary.avg_digital_adoption * 100).toFixed(0)}%`
              : '—'}
          </div>
        </div>
        <div className="card">
          <div className="card-label-row">
            <div className="label">Tổng Digital VA</div>
            <MetricInfoTip {...KPI_TIPS.digitalVa} />
          </div>
          <div className="value">{formatNumber(summary?.total_digital_va)}</div>
          <div className="sub muted">Theo công thức Digital VA</div>
        </div>
      </div>

      {summary?.model_metrics && Object.keys(summary.model_metrics).length > 0 && (
        <div className="metric-strip">
          {Object.entries(summary.model_metrics).map(([name, m]) => (
            <div className="metric-chip" key={name}>
              <strong>{name}</strong>
              <span>MAE {m?.mae ?? '—'}</span>
              <span>RMSE {m?.rmse ?? '—'}</span>
              <span>MAPE {m?.mape != null ? `${m.mape}%` : '—'}</span>
            </div>
          ))}
        </div>
      )}

      <div className="chart-container">
        <h3>Chỉ số SXCN (IIP) Section C + dự báo</h3>
        {iip.length === 0 ? (
          <div className="empty-state">
            Chưa có chuỗi IIP_C trong DB. Chạy <code>make bootstrap</code> (seed + crawl GSO).
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={iipChart}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 11 }} minTickGap={24} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#367ea2"
                strokeWidth={2}
                dot={false}
                name="IIP thực tế (GSO)"
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="forecast"
                stroke="#164654"
                strokeWidth={2}
                strokeDasharray="6 4"
                dot={false}
                name={forecast ? `Dự báo (${forecast.model})` : 'Dự báo'}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
        {forecastError && (
          <div className="banner banner-warn">{forecastError}</div>
        )}
        {!forecast && !forecastError && iip.length > 0 && (
          <div className="empty-state" style={{ marginTop: 12 }}>
            Chưa tải được đường dự báo — chạy bootstrap/train ML.
          </div>
        )}
      </div>

      <div className="chart-container">
        <h3>OECD leading (peer) vs GSO lagging (IIP)</h3>
        {oecdMissing ? (
          <div className="empty-state">
            <p>
              <strong>Thiếu chuỗi OECD peer.</strong>{' '}
              <span className="badge badge-warning">unavailable</span>{' '}
              {oecdGso?.oecd_note
                || 'Chưa có dữ liệu OECD khu vực Euro (EA20) trong hệ thống.'}
            </p>
            {aligned.some((r) => r.gso != null) && (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={aligned}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" tick={{ fontSize: 11 }} minTickGap={24} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="gso"
                    stroke="#367ea2"
                    strokeWidth={2}
                    dot={false}
                    name="GSO IIP (VNM)"
                    connectNulls={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        ) : (
          <>
            <p className="chart-note" style={{ marginTop: 0 }}>
              {oecdGso?.oecd_note
                || 'OECD không có dữ liệu sản xuất công nghiệp của Việt Nam, nên biểu đồ dùng chỉ số khu vực Euro (EA20) làm đối sánh với IIP của GSO.'}
              {' '}
              <span className={`badge ${
                String(oecdGso?.oecd_source || '').includes('FALLBACK')
                  ? 'badge-warning'
                  : 'badge-info'
              }`}
              >
                {oecdGso?.oecd_source || 'OECD_PEER'}
              </span>
            </p>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={aligned}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} minTickGap={24} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="gso"
                  stroke="#367ea2"
                  strokeWidth={2}
                  dot={false}
                  name="GSO IIP (VNM)"
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="oecd"
                  stroke="#164654"
                  strokeWidth={2}
                  dot={false}
                  name={`OECD MEI (${oecdGso?.oecd_country || 'EA20'})`}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </>
        )}
      </div>

      <div className="chart-container">
        <h3>Heatmap đóng góp Kinh tế số theo VSIC</h3>
        {heatmap.length === 0 ? (
          <div className="empty-state">
            Chưa có Digital VA theo ngành. Chạy digital metrics / seed.
          </div>
        ) : (
          <div className="heatmap-grid">
            {heatmap.map((cell) => {
              const division = cell.division || String(cell.vsic_code || '').slice(0, 2)
              const fg = heatTextColor(cell.intensity)
              const isDark = fg === '#ffffff'
              return (
                <Link
                  key={cell.vsic_code}
                  to={`/companies?vsic=${encodeURIComponent(division)}`}
                  className="heatmap-cell"
                  data-heat={isDark ? 'dark' : 'light'}
                  style={{
                    background: heatColor(cell.intensity),
                    '--heatmap-fg': fg,
                    color: 'var(--heatmap-fg)',
                    textDecoration: 'none',
                  }}
                  title={`${cell.vsic_name || cell.vsic_code}: ${formatNumber(cell.digital_va)} — click xem DN`}
                >
                  <div className="heatmap-code">VSIC {cell.vsic_code}</div>
                  <div className="heatmap-name">{cell.vsic_name || '—'}</div>
                  <div className="heatmap-va">{formatNumber(cell.digital_va)}</div>
                  <div className="heatmap-meta">{cell.company_count} DN · div {division}</div>
                </Link>
              )
            })}
          </div>
        )}
        {/* keep a simple bar fallback via recharts Cell for accessibility of scale */}
        {heatmap.length > 0 && (
          <div className="heatmap-legend">
            <span>Thấp</span>
            <span className="heatmap-legend-bar" />
            <span>Cao (Digital VA)</span>
          </div>
        )}
      </div>
    </div>
  )
}
