import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { api } from '../api'

function formatNumber(n) {
  if (n == null) return '—'
  if (n >= 1e12) return `${(n / 1e12).toFixed(1)}T`
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`
  return n.toLocaleString()
}

function periodLabel(p) {
  if (!p) return ''
  return String(p).slice(0, 7)
}

function heatColor(intensity) {
  const t = Math.max(0, Math.min(1, intensity ?? 0))
  // coral scale on white — matches existing dashboard accent (#e94560)
  const r = Math.round(255 - t * (255 - 233))
  const g = Math.round(255 - t * (255 - 69))
  const b = Math.round(255 - t * (255 - 96))
  return `rgb(${r},${g},${b})`
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
                ? `Chưa có artifact forecast cho model «${model}» — train ML trước (không bịa số).`
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

      <div className="cards">
        <div className="card">
          <div className="label">IIP (SXCN)</div>
          <div className="value">{summary?.iip_latest?.toFixed(1) ?? '—'}</div>
          {summary?.iip_growth_pct != null && (
            <div className={`sub ${summary.iip_growth_pct >= 0 ? 'up' : 'down'}`}>
              {summary.iip_growth_pct > 0 ? '+' : ''}{summary.iip_growth_pct}% so với kỳ trước
            </div>
          )}
        </div>
        <div className="card">
          <div className="label">Doanh nghiệp mẫu</div>
          <div className="value">{summary?.total_companies ?? 0}</div>
          <div className="sub">{summary?.companies_with_ecommerce ?? 0} có kênh TMĐT</div>
        </div>
        <div className="card">
          <div className="label">Digital Adoption</div>
          <div className="value">
            {summary?.avg_digital_adoption != null
              ? `${(summary.avg_digital_adoption * 100).toFixed(0)}%`
              : '—'}
          </div>
        </div>
        <div className="card">
          <div className="label">Tổng Digital VA</div>
          <div className="value">{formatNumber(summary?.total_digital_va)}</div>
          <div className="sub muted">Công thức CONTEXT — không đổi</div>
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
            Chưa có chuỗi IIP_C trong DB. Chạy seed/crawl GSO — không bịa số.
          </div>
        ) : (
          <>
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
                  stroke="#e94560"
                  strokeWidth={2}
                  dot={false}
                  name="IIP thực tế (GSO)"
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  stroke="#0f3460"
                  strokeWidth={2}
                  strokeDasharray="6 4"
                  dot={false}
                  name={forecast ? `Dự báo (${forecast.model})` : 'Dự báo'}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
            {forecastError && (
              <div className="banner banner-warn">{forecastError}</div>
            )}
            {forecast && !forecastError && (
              <p className="chart-note">
                Dự báo {forecast.horizon} tháng từ `/api/ml/forecast` · model {forecast.model}
              </p>
            )}
          </>
        )}
      </div>

      <div className="chart-container">
        <h3>OECD leading (peer) vs GSO lagging (IIP)</h3>
        {oecdMissing ? (
          <div className="empty-state">
            <p>
              <strong>Thiếu chuỗi OECD peer.</strong>{' '}
              {oecdGso?.oecd_note
                || 'MEI_IP@EA20 chưa có — không hiển thị số bịa (ADR-0001).'}
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
                    stroke="#e94560"
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
            <p className="chart-note">
              {oecdGso?.oecd_note
                || `Peer ${oecdGso?.oecd_country || 'EA20'} · ${oecdGso?.oecd_source || 'OECD_PEER'}`}
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
                  stroke="#e94560"
                  strokeWidth={2}
                  dot={false}
                  name="GSO IIP (VNM)"
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="oecd"
                  stroke="#0f3460"
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
            Chưa có Digital VA theo ngành. Chạy digital metrics / seed — không bịa.
          </div>
        ) : (
          <div className="heatmap-grid">
            {heatmap.map((cell) => (
              <div
                key={cell.vsic_code}
                className="heatmap-cell"
                style={{ background: heatColor(cell.intensity) }}
                title={`${cell.vsic_name || cell.vsic_code}: ${formatNumber(cell.digital_va)}`}
              >
                <div className="heatmap-code">VSIC {cell.vsic_code}</div>
                <div className="heatmap-name">{cell.vsic_name || '—'}</div>
                <div className="heatmap-va">{formatNumber(cell.digital_va)}</div>
                <div className="heatmap-meta">{cell.company_count} DN</div>
              </div>
            ))}
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
