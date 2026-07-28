import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { api } from '../api'
import { formatGrouped, formatMacroVa, formatMoney } from '../format'
import MetricInfoTip from '../MetricInfoTip'
import SampleHonestyBanner from '../SampleHonestyBanner'

/** KPI help copy — formulas match CONTEXT.md / proposal-v2 (do not invent). */
const KPI_TIPS = {
  iip: {
    title: 'Chỉ số sản xuất công nghiệp (IIP / SXCN)',
    formula: 'Nguồn: GSO/NSO · chuỗi IIP_C (VSIC Section C)',
    blurb:
      'Đo mức sản xuất theo tháng của ngành chế biến, chế tạo. Đây là chỉ số công bố từ thống kê chính thức, không phải số do nền tảng tự tính.',
  },
  vaC: {
    title: 'Giá trị gia tăng ngành CBCT',
    formula: 'Nguồn: GSO/NSO SDMX · giá so sánh 2010 (VA_C)',
    blurb:
      'Giá trị gia tăng quốc gia của ngành chế biến, chế tạo, đơn vị tỷ VND. Khác IIP (chỉ số sản xuất) và khác Digital VA cấp doanh nghiệp trong mẫu.',
  },
  digitalVa: {
    title: 'Tổng giá trị gia tăng số (mẫu DN)',
    formula:
      'Digital_VA = (Online_revenue × Gross_margin) + (Cost_savings × Adoption_score) − Digital_investment',
    blurb:
      'Tổng ước lượng giá trị gia tăng kinh tế số của các doanh nghiệp trong mẫu ~28 DN niêm yết (cộng từng DN). Không phải giá trị gia tăng ngành GSO, không đồng nghĩa với doanh thu hay IIP, và không đại diện toàn Section C.',
  },
  adoption: {
    title: 'Mức độ số hóa (trung bình)',
    formula: 'Trung bình cộng điểm số hóa (0–1) của DN mẫu',
    blurb:
      'Mức độ số hóa kênh bán trung bình (mean) của DN mẫu ~28 (website, sàn TMĐT, tín hiệu giao dịch…). Dùng trong tính Digital VA và các feature dự báo — không phải chuẩn toàn ngành.',
  },
  iipGrowth: {
    title: 'Tăng trưởng IIP',
    formula: 'MoM = so kỳ liền trước · YoY = so cùng kỳ năm trước',
    blurb:
      'MoM cho biết sản xuất tháng này nhanh/chậm hơn tháng trước; YoY loại bỏ yếu tố mùa vụ bằng cách so với cùng tháng năm ngoái. Đường nhỏ là xu hướng 12 kỳ gần nhất.',
  },
  forecast: {
    title: 'Dự báo IIP 6 tháng',
    formula: 'Giá trị dự báo cuối kỳ so với IIP mới nhất',
    blurb:
      'Giá trị IIP mô hình dự báo cho tháng cuối trong 6 tháng tới, kèm mức thay đổi so với kỳ thực tế gần nhất. Chỉ là ước lượng từ mô hình, không phải số công bố.',
  },
  vaMix: {
    title: 'Cơ cấu giá trị gia tăng số (trong mẫu)',
    formula: 'GTGT số từng ngành ÷ tổng GTGT số của mẫu',
    blurb:
      'Ngành (VSIC) đóng góp nhiều giá trị gia tăng số nhất trong nhóm DN mẫu. Đây là cơ cấu nội bộ mẫu, không phải tỷ trọng trên toàn ngành chế biến, chế tạo.',
  },
  coverage: {
    title: 'Độ phủ dữ liệu',
    formula: 'Số DN có Digital metrics ÷ tổng DN mẫu',
    blurb:
      'Tỷ lệ doanh nghiệp trong mẫu đã có chỉ số số hóa (Digital metrics). Độ phủ càng cao thì các số tổng hợp phía trên càng đại diện.',
  },
}

/** Plain-language help for each IIP forecast model (hover / focus tip). */
const MODEL_TIPS = {
  arima: {
    title: 'ARIMA',
    formula: 'Nhóm thống kê — mô hình chuỗi thời gian',
    blurb:
      'Dự báo IIP theo chuỗi thời gian: nhìn xu hướng và chu kỳ trong quá khứ của chính chỉ số đó. Không dựa vào nhiều biến ngoài (doanh thu số, mức độ số hóa…). Phù hợp khi muốn baseline “chỉ từ lịch sử IIP”.',
  },
  xgboost: {
    title: 'XGBoost',
    formula: 'Nhóm học máy — cây quyết định tăng cường',
    blurb:
      'Học quan hệ từ nhiều đặc trưng (feature) — ví dụ tín hiệu số hóa, biến kinh tế — rồi dự báo IIP. Thường giải thích được feature nào quan trọng (xem trang Phòng thí nghiệm ML).',
  },
  lstm: {
    title: 'LSTM',
    formula: 'Nhóm học sâu — mạng nơ-ron',
    blurb:
      'Mạng nơ-ron chuyên chuỗi thời gian: nhớ pattern dài hạn trong dữ liệu lịch sử để dự báo IIP. Mạnh khi chuỗi phức tạp, nhưng khó giải thích từng bước hơn ARIMA/XGBoost.',
  },
}

/** Compact inline SVG sparkline (no axes) for KPI trend. */
function Sparkline({ values, width = 132, height = 34, stroke = '#367ea2' }) {
  const nums = (values || []).filter((v) => typeof v === 'number' && !Number.isNaN(v))
  if (nums.length < 2) return null
  const min = Math.min(...nums)
  const max = Math.max(...nums)
  const span = max - min || 1
  const stepX = width / (nums.length - 1)
  const pad = 3
  const usable = height - pad * 2
  const points = nums.map((v, i) => {
    const x = i * stepX
    const y = pad + (1 - (v - min) / span) * usable
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  const last = points[points.length - 1].split(',')
  return (
    <svg
      className="sparkline"
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      role="img"
      aria-hidden="true"
      preserveAspectRatio="none"
    >
      <polyline
        points={points.join(' ')}
        fill="none"
        stroke={stroke}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={last[0]} cy={last[1]} r="2.6" fill={stroke} />
    </svg>
  )
}

function pctText(v) {
  if (v == null) return null
  return `${v > 0 ? '+' : ''}${v}%`
}

function formatNumber(n) {
  return formatMoney(n, 'VND')
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
  const [vaC, setVaC] = useState([])
  const [vaNominal, setVaNominal] = useState([])
  const [heatmap, setHeatmap] = useState([])
  const [oecdGso, setOecdGso] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [forecastError, setForecastError] = useState(null)
  const [coverageNote, setCoverageNote] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [s, i, va, van, h, og, cov] = await Promise.all([
          api.getSummary(),
          api.getIip(),
          api.getVa('VA_C'),
          api.getVa('VA_C_NOMINAL'),
          api.getHeatmap(),
          api.getOecdVsGso(),
          api.getUniverseCoverage().catch(() => null),
        ])
        if (cancelled) return
        setSummary(s)
        setIip(i)
        setVaC(va)
        setVaNominal(van)
        setHeatmap(h)
        setOecdGso(og)
        setCoverageNote(cov)

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
  const vaPeriodText = summary?.va_c_period
    ? periodLabel(summary.va_c_period)
    : '—'
  const vaSourceBadge = summary?.va_c_source || null
  const vaSourceFallback = String(vaSourceBadge || '').includes('FALLBACK')

  // Align VA_C + optional nominal by period for the macro chart.
  const vaByPeriod = new Map()
  for (const row of vaC) {
    const key = periodLabel(row.period)
    vaByPeriod.set(key, { period: key, va_c: row.value, va_nominal: null })
  }
  for (const row of vaNominal) {
    const key = periodLabel(row.period)
    const existing = vaByPeriod.get(key) || { period: key, va_c: null, va_nominal: null }
    existing.va_nominal = row.value
    vaByPeriod.set(key, existing)
  }
  const vaChart = [...vaByPeriod.values()].sort((a, b) => a.period.localeCompare(b.period))

  // Last 12 IIP points for the trend sparkline.
  const iipTrend = iip.slice(-12).map((r) => r.value)

  // Forecast KPI (2B): final horizon point + change vs latest actual, no CI/MAPE.
  const forecastRows = forecast?.forecasts || []
  const lastForecast = forecastRows.length ? forecastRows[forecastRows.length - 1] : null
  const latestActual = summary?.iip_latest ?? (iip.length ? iip[iip.length - 1].value : null)
  const forecastDelta =
    lastForecast?.predicted_value != null && latestActual
      ? ((lastForecast.predicted_value - latestActual) / latestActual) * 100
      : null

  // Digital VA composition (1A): top VSIC share within the sample.
  const vaRows = (heatmap || []).filter((r) => (r.digital_va ?? 0) > 0)
  const vaTotal = vaRows.reduce((sum, r) => sum + (r.digital_va || 0), 0)
  const vaTop = vaRows.length
    ? [...vaRows].sort((a, b) => (b.digital_va || 0) - (a.digital_va || 0)).slice(0, 3)
    : []
  const vaTopShare =
    vaTop.length && vaTotal > 0 ? (vaTop[0].digital_va / vaTotal) * 100 : null

  // Data coverage (4): companies with digital metrics over the sample.
  const totalCompanies = summary?.total_companies ?? 0
  const withMetrics = summary?.companies_with_metrics ?? 0
  const coveragePct =
    totalCompanies > 0 ? (withMetrics / totalCompanies) * 100 : null

  return (
    <div>
      <h2 className="page-title">Dashboard — Công nghiệp Chế biến, Chế tạo</h2>
      <p className="page-subtitle">
        VSIC Section C · kỳ gần nhất {periodText}
        {summary?.preferred_forecast_model
          ? ` · forecast model: ${summary.preferred_forecast_model}`
          : ''}
      </p>

      <SampleHonestyBanner style={{ marginBottom: 16 }} coverageNote={coverageNote} />

      {summary?.iip_latest == null && (
        <div className="banner banner-warn" style={{ marginBottom: 16 }}>
          Chưa có IIP Section C trong DB — chạy <code>make bootstrap</code> (seed + crawl GSO).
        </div>
      )}
      {summary?.va_c_latest == null && (
        <div className="banner banner-warn" style={{ marginBottom: 16 }}>
          Chưa có giá trị gia tăng ngành chế biến, chế tạo trong DB — chạy bootstrap / crawl GSO VA.
          Không ước từ IIP hay Digital VA mẫu.
        </div>
      )}
      {!summary?.preferred_forecast_model && summary?.iip_latest != null && (
        <div className="banner banner-warn" style={{ marginBottom: 16 }}>
          Chưa có model active trong registry — chạy bootstrap/train ML trước khi xem dự báo.
        </div>
      )}

      {summary?.va_c_latest != null && (
        <div className="metric-strip" role="region" aria-label="Giá trị gia tăng ngành CBCT">
          <div className="metric-chip">
            <strong>Giá trị gia tăng (giá so sánh 2010)</strong>
            <MetricInfoTip {...KPI_TIPS.vaC} />
            <span>{formatMacroVa(summary.va_c_latest)}</span>
            <span className="muted">kỳ {vaPeriodText}</span>
            {vaSourceBadge && (
              <span className={`badge ${vaSourceFallback ? 'badge-warning' : 'badge-info'}`}>
                {vaSourceBadge}
              </span>
            )}
            <span className="badge badge-info">≠ Digital VA mẫu</span>
          </div>
          {summary.va_c_nominal_latest != null && (
            <div className="metric-chip">
              <strong>Giá trị gia tăng (giá hiện hành)</strong>
              <span>{formatMacroVa(summary.va_c_nominal_latest)}</span>
              <span className="muted">
                {summary.va_c_nominal_period
                  ? `kỳ ${periodLabel(summary.va_c_nominal_period)}`
                  : ''}
              </span>
              {summary.va_c_nominal_source && (
                <span
                  className={`badge ${
                    String(summary.va_c_nominal_source).includes('FALLBACK')
                      ? 'badge-warning'
                      : 'badge-info'
                  }`}
                >
                  {summary.va_c_nominal_source}
                </span>
              )}
            </div>
          )}
          {summary.va_c_growth_pct != null && (
            <div className="metric-chip">
              <strong>So kỳ trước</strong>
              <span className={summary.va_c_growth_pct >= 0 ? 'up' : 'down'}>
                {pctText(summary.va_c_growth_pct)}
              </span>
            </div>
          )}
          {summary.va_c_yoy_pct != null && (
            <div className="metric-chip">
              <strong>So cùng kỳ năm trước</strong>
              <span className={summary.va_c_yoy_pct >= 0 ? 'up' : 'down'}>
                {pctText(summary.va_c_yoy_pct)}
              </span>
            </div>
          )}
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
              {pctText(summary.iip_growth_pct)} so với kỳ trước (MoM)
            </div>
          )}
          <div className="sub muted">Kỳ {periodText}</div>
          {summary?.iip_latest == null && (
            <div className="sub muted">Chưa có chuỗi IIP</div>
          )}
        </div>
        <div className="card">
          <div className="card-label-row">
            <div className="label">Doanh nghiệp mẫu</div>
            <span className="badge badge-warning">mẫu ~28 · không phải Section C</span>
          </div>
          <div className="value">{summary?.total_companies ?? 0}</div>
          <div className="sub">{summary?.companies_with_ecommerce ?? 0} có kênh TMĐT</div>
          <div className="sub muted">
            <Link to="/companies">Xem danh sách →</Link>
          </div>
        </div>
        <div className="card">
          <div className="card-label-row">
            <div className="label">Mức độ số hóa</div>
            <MetricInfoTip {...KPI_TIPS.adoption} />
          </div>
          <div className="value">
            {summary?.avg_digital_adoption != null
              ? `${(summary.avg_digital_adoption * 100).toFixed(0)}%`
              : '—'}
          </div>
          <div className="sub muted">
            Trung bình DN mẫu{' '}
            <span className="badge badge-info">trong mẫu</span>
          </div>
        </div>
        <div className="card">
          <div className="card-label-row">
            <div className="label">Tổng giá trị gia tăng số (mẫu DN)</div>
            <MetricInfoTip {...KPI_TIPS.digitalVa} />
          </div>
          <div className="value">{formatNumber(summary?.total_digital_va)}</div>
          <div className="sub muted">
            Cộng dồn mẫu · kỳ {periodText}{' '}
            <span className="badge badge-warning">≠ VA_C GSO</span>
          </div>
        </div>
      </div>

      <div className="cards cards-kpi">
        <div className="card">
          <div className="card-label-row">
            <div className="label">Tăng trưởng IIP</div>
            <MetricInfoTip {...KPI_TIPS.iipGrowth} placement="below" />
          </div>
          <div className={`value ${(summary?.iip_growth_pct ?? 0) >= 0 ? 'up' : 'down'}`}>
            {pctText(summary?.iip_growth_pct) ?? '—'}
            <span className="value-unit"> MoM</span>
          </div>
          {summary?.iip_yoy_pct != null ? (
            <div className={`sub ${summary.iip_yoy_pct >= 0 ? 'up' : 'down'}`}>
              {pctText(summary.iip_yoy_pct)} so cùng kỳ năm trước (YoY)
            </div>
          ) : (
            <div className="sub muted">Chưa đủ dữ liệu cho YoY</div>
          )}
          {iipTrend.length >= 2 && (
            <Sparkline values={iipTrend} />
          )}
        </div>

        <div className="card">
          <div className="card-label-row">
            <div className="label">Dự báo 6 tháng</div>
            <MetricInfoTip {...KPI_TIPS.forecast} placement="below" />
          </div>
          {lastForecast?.predicted_value != null ? (
            <>
              <div className="value">{lastForecast.predicted_value.toFixed(1)}</div>
              {forecastDelta != null && (
                <div className={`sub ${forecastDelta >= 0 ? 'up' : 'down'}`}>
                  {pctText(Number(forecastDelta.toFixed(1)))} so với kỳ mới nhất
                </div>
              )}
              <div className="sub muted">
                {forecast?.model ? `Model ${forecast.model}` : 'Mô hình dự báo'}
                {lastForecast.period ? ` · ${periodLabel(lastForecast.period)}` : ''}
              </div>
            </>
          ) : (
            <>
              <div className="value">—</div>
              <div className="sub muted">Chưa có đường dự báo</div>
            </>
          )}
        </div>

        <div className="card">
          <div className="card-label-row">
            <div className="label">Cơ cấu giá trị gia tăng số</div>
            <MetricInfoTip {...KPI_TIPS.vaMix} placement="below" />
          </div>
          {vaTop.length ? (
            <>
              <div className="value">
                {vaTopShare != null ? `${vaTopShare.toFixed(0)}%` : '—'}
              </div>
              <div className="sub">
                Ngành dẫn đầu: {vaTop[0].vsic_name || `VSIC ${vaTop[0].vsic_code}`}
              </div>
              <ul className="mini-rank">
                {vaTop.map((r) => (
                  <li key={r.vsic_code}>
                    <span className="mini-rank-name">
                      {r.vsic_name || `VSIC ${r.vsic_code}`}
                    </span>
                    <span className="mini-rank-val">
                      {vaTotal > 0 ? `${((r.digital_va / vaTotal) * 100).toFixed(0)}%` : '—'}
                    </span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <>
              <div className="value">—</div>
              <div className="sub muted">Chưa có giá trị gia tăng số theo ngành</div>
            </>
          )}
        </div>

        <div className="card">
          <div className="card-label-row">
            <div className="label">Độ phủ dữ liệu</div>
            <MetricInfoTip {...KPI_TIPS.coverage} placement="below" />
          </div>
          <div className="value">
            {coveragePct != null ? `${coveragePct.toFixed(0)}%` : '—'}
          </div>
          <div className="sub">
            {withMetrics}/{totalCompanies} DN có Digital metrics
          </div>
          <div className="sub muted">
            {summary?.companies_with_ecommerce ?? 0} có kênh TMĐT
          </div>
        </div>
      </div>

      {summary?.model_metrics && Object.keys(summary.model_metrics).length > 0 && (
        <div className="metric-strip">
          {Object.entries(summary.model_metrics).map(([name, m]) => {
            const tip = MODEL_TIPS[String(name).toLowerCase()]
            return (
              <div className="metric-chip" key={name}>
                <strong>{name}</strong>
                {tip ? <MetricInfoTip {...tip} placement="below" /> : null}
                <span>MAE {m?.mae ?? '—'}</span>
                <span>RMSE {m?.rmse ?? '—'}</span>
                <span>MAPE {m?.mape != null ? `${m.mape}%` : '—'}</span>
              </div>
            )
          })}
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
        <h3>Giá trị gia tăng ngành chế biến, chế tạo — GSO/NSO</h3>
        <p className="chart-note" style={{ marginTop: 0 }}>
          Giá trị gia tăng quốc gia chế biến, chế tạo (tỷ VND). Không phải Digital VA mẫu DN,
          không phải IIP, không phải GRDP tỉnh×ngành.
          {vaSourceBadge ? (
            <>
              {' '}
              <span className={`badge ${vaSourceFallback ? 'badge-warning' : 'badge-info'}`}>
                {vaSourceBadge}
              </span>
            </>
          ) : null}
        </p>
        {vaChart.length === 0 ? (
          <div className="empty-state">
            Chưa có chuỗi giá trị gia tăng ngành trong DB. Chạy bootstrap / crawl GSO VA —
            không ước từ IIP hay Digital VA.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={vaChart}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 11 }} minTickGap={24} />
              <YAxis
                tickFormatter={(v) => formatGrouped(v, { maxFractionDigits: 0 })}
                width={88}
                label={{ value: 'tỷ VND', angle: -90, position: 'insideLeft', offset: 8, style: { fontSize: 11 } }}
              />
              <Tooltip
                formatter={(value, _name, item) => [
                  formatMacroVa(value),
                  item?.dataKey === 'va_nominal'
                    ? 'Giá trị gia tăng (giá hiện hành)'
                    : 'Giá trị gia tăng (giá so sánh 2010)',
                ]}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="va_c"
                stroke="#367ea2"
                strokeWidth={2}
                dot={false}
                name="Giá trị gia tăng (giá so sánh 2010)"
                connectNulls={false}
              />
              {vaNominal.length > 0 && (
                <Line
                  type="monotone"
                  dataKey="va_nominal"
                  stroke="#164654"
                  strokeWidth={2}
                  strokeDasharray="6 4"
                  dot={false}
                  name="Giá trị gia tăng (giá hiện hành)"
                  connectNulls={false}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
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
        <h3>Heatmap Digital VA theo VSIC (trong mẫu)</h3>
        {heatmap.length === 0 ? (
          <div className="empty-state">
            Chưa có Digital VA theo ngành trong mẫu. Chạy digital metrics / seed.
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
