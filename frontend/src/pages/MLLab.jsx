import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar,
} from 'recharts'
import { api } from '../api'

const MODEL_OPTIONS = [
  { id: 'arima', label: 'ARIMA', color: '#1e3a5f' },
  { id: 'xgboost', label: 'XGBoost', color: '#0d9488' },
  { id: 'lstm', label: 'LSTM', color: '#2563eb' },
]

function periodLabel(p) {
  if (!p) return ''
  return String(p).slice(0, 7)
}

function metricOrNull(value) {
  return value == null || Number.isNaN(Number(value)) ? null : Number(value)
}

/** Latest registry row per model_name (prefer is_active, then trained_at). */
function pickLatestModels(models) {
  const byName = new Map()
  for (const m of models || []) {
    const name = m.model_name
    const prev = byName.get(name)
    if (!prev) {
      byName.set(name, m)
      continue
    }
    if (m.is_active && !prev.is_active) {
      byName.set(name, m)
      continue
    }
    if (!m.is_active && prev.is_active) continue
    const tNew = m.trained_at ? Date.parse(m.trained_at) : 0
    const tOld = prev.trained_at ? Date.parse(prev.trained_at) : 0
    if (tNew >= tOld) byName.set(name, m)
  }
  return MODEL_OPTIONS.map((opt) => byName.get(opt.id)).filter(Boolean)
}

function buildHoldoutCompare(predictions) {
  const byPeriod = {}
  for (const p of predictions || []) {
    const key = periodLabel(p.period)
    if (!key) continue
    if (!byPeriod[key]) byPeriod[key] = { period: key }
    if (p.actual_value != null) byPeriod[key].actual = p.actual_value
    if (p.model_name && p.predicted_value != null) {
      byPeriod[key][p.model_name] = p.predicted_value
    }
  }
  return Object.values(byPeriod).sort((a, b) => a.period.localeCompare(b.period))
}

export default function MLLab() {
  const [models, setModels] = useState([])
  const [predictions, setPredictions] = useState([])
  const [iip, setIip] = useState([])
  const [importance, setImportance] = useState(null)
  const [selectedModel, setSelectedModel] = useState('xgboost')
  const [forecast, setForecast] = useState(null)
  const [forecastError, setForecastError] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [training, setTraining] = useState(false)

  const reloadCore = async () => {
    const [m, p, iipSeries, fi] = await Promise.all([
      api.getModels(),
      api.getPredictions(),
      api.getIip(),
      api.getFeatureImportance('xgboost').catch(() => null),
    ])
    setModels(m)
    setPredictions(p)
    setIip(iipSeries)
    setImportance(fi)
  }

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setLoadError(null)
    reloadCore()
      .catch((e) => {
        if (!cancelled) setLoadError(e.message || 'Không tải được ML Lab')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const handleTrain = async () => {
    setTraining(true)
    setLoadError(null)
    try {
      await api.trainModels()
      await reloadCore()
      setForecast(null)
      setForecastError(null)
    } catch (e) {
      setLoadError(e.message || 'Train thất bại')
    } finally {
      setTraining(false)
    }
  }

  const handleForecast = async () => {
    setForecastError(null)
    setForecast(null)
    try {
      const result = await api.forecast(selectedModel, 6)
      setForecast(result)
    } catch (err) {
      setForecast(null)
      setForecastError(
        err?.message?.includes('404')
          ? `Chưa có artifact forecast cho model «${selectedModel}» — chạy make bootstrap / train ML (không bịa số).`
          : `Không tải được forecast (${selectedModel}): ${err.message}`
      )
    }
  }

  if (loading) return <div className="loading">Đang tải...</div>

  const latestModels = pickLatestModels(models)
  const metricsData = latestModels
    .map((m) => {
      const mae = metricOrNull(m.metrics?.mae)
      const rmse = metricOrNull(m.metrics?.rmse)
      const mape = metricOrNull(m.metrics?.mape)
      if (mae == null && rmse == null && mape == null) return null
      return { name: m.model_name, mae, rmse, mape, status: m.metrics?.status }
    })
    .filter(Boolean)

  const holdoutCompare = buildHoldoutCompare(predictions)
  const selectedHoldout = holdoutCompare
    .filter((row) => row.actual != null || row[selectedModel] != null)
    .map((row) => ({
      period: row.period,
      actual: row.actual ?? null,
      predicted: row[selectedModel] ?? null,
    }))

  const forecastVsActual = [
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
  if (iip.length && forecast?.forecasts?.length) {
    const lastActual = iip[iip.length - 1]
    const bridgeIdx = iip.length - 1
    if (forecastVsActual[bridgeIdx]) {
      forecastVsActual[bridgeIdx] = {
        ...forecastVsActual[bridgeIdx],
        forecast: lastActual.value,
      }
    }
  }

  const importanceBars = (importance?.available && importance.features?.length)
    ? importance.features.slice(0, 15).map((f) => ({
        feature: f.feature,
        gain: f.gain,
      }))
    : []

  const noRegistry = latestModels.length === 0
  const noPredictions = predictions.length === 0

  return (
    <div>
      <h2 className="page-title">ML Lab — So sánh model IIP</h2>
      <p className="page-subtitle">
        Module 4: so sánh ARIMA / XGBoost / LSTM từ registry #12, holdout actual vs predicted,
        forecast vs IIP, feature importance (artifact thật — không bịa số).
      </p>

      {loadError && (
        <div className="banner banner-warn" style={{ marginBottom: 16 }}>{loadError}</div>
      )}

      {noRegistry && (
        <div className="empty-state" style={{ marginBottom: 16 }}>
          Chưa có model trong <code>model_registry</code> — chạy <code>make bootstrap</code> hoặc
          nút train bên dưới. Không hiển thị metric giả.
        </div>
      )}

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 24, alignItems: 'center' }}>
        <select
          value={selectedModel}
          onChange={(e) => {
            setSelectedModel(e.target.value)
            setForecast(null)
            setForecastError(null)
          }}
          style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #ddd' }}
        >
          {MODEL_OPTIONS.map((m) => (
            <option key={m.id} value={m.id}>{m.label}</option>
          ))}
        </select>
        <button className="btn btn-primary" type="button" onClick={handleForecast}>
          Dự báo 6 tháng ({selectedModel})
        </button>
        <button
          className="btn"
          type="button"
          onClick={handleTrain}
          disabled={training}
          title="Tuỳ chọn — Pipeline cũng có job ML Training"
        >
          {training ? 'Đang huấn luyện...' : 'Huấn luyện models (tuỳ chọn)'}
        </button>
      </div>

      <div className="cards">
        {MODEL_OPTIONS.map((opt) => {
          const m = latestModels.find((row) => row.model_name === opt.id)
          const status = m?.metrics?.status
          return (
            <div className="card" key={opt.id}>
              <div className="label">{opt.label}{m?.model_type ? ` (${m.model_type})` : ''}</div>
              {m ? (
                <>
                  <div className="value" style={{ fontSize: 16 }}>
                    MAE: {m.metrics?.mae ?? '—'} | RMSE: {m.metrics?.rmse ?? '—'}
                  </div>
                  <div className="sub">
                    MAPE: {m.metrics?.mape ?? '—'}%
                    {status ? ` · status: ${status}` : ''}
                    {!m.is_active ? ' · inactive' : ''}
                  </div>
                </>
              ) : (
                <div className="sub">Chưa đăng ký — không bịa metric</div>
              )}
            </div>
          )
        })}
      </div>

      <div className="chart-container">
        <h3>So sánh metric (3 model)</h3>
        {metricsData.length === 0 ? (
          <div className="empty-state">
            Chưa có MAE/RMSE/MAPE trong registry — chạy make bootstrap / train xong mới có số thật.
          </div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={metricsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="mae" fill="#0d9488" name="MAE" />
                <Bar dataKey="rmse" fill="#1e3a5f" name="RMSE" />
                <Bar dataKey="mape" fill="#2563eb" name="MAPE %" />
              </BarChart>
            </ResponsiveContainer>
            <p className="chart-note">Nguồn: GET /api/ml/models · metrics từ train #12 (null → không vẽ thành 0).</p>
          </>
        )}
      </div>

      <div className="chart-container">
        <h3>Holdout — actual vs predicted (cả 3 model)</h3>
        {noPredictions ? (
          <div className="empty-state">
            Chưa có hàng trong <code>model_predictions</code> — cửa sổ holdout ghi khi train
            (make bootstrap / nút huấn luyện). Không vẽ đường giả.
          </div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={holdoutCompare}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="actual" stroke="#333" strokeWidth={2} name="Actual IIP" dot={false} connectNulls={false} />
                {MODEL_OPTIONS.map((opt) => (
                  <Line
                    key={opt.id}
                    type="monotone"
                    dataKey={opt.id}
                    stroke={opt.color}
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name={`${opt.label} pred`}
                    dot={false}
                    connectNulls={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
            <p className="chart-note">Nguồn: GET /api/ml/predictions · holdout train #12</p>
          </>
        )}
      </div>

      <div className="chart-container">
        <h3>Actual vs Predicted — {selectedModel.toUpperCase()}</h3>
        {selectedHoldout.every((r) => r.predicted == null) ? (
          <div className="empty-state">
            Không có prediction holdout cho «{selectedModel}» — chọn model khác hoặc train lại.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={selectedHoldout}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="actual" stroke="#1e3a5f" strokeWidth={2} name="Actual" connectNulls={false} />
              <Line type="monotone" dataKey="predicted" stroke="#0d9488" strokeWidth={2} strokeDasharray="5 5" name="Predicted" connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="chart-container">
        <h3>Forecast vs actual IIP — {selectedModel.toUpperCase()}</h3>
        {forecastError && (
          <div className="banner banner-warn" style={{ marginBottom: 12 }}>{forecastError}</div>
        )}
        {!forecast && !forecastError && (
          <div className="empty-state">
            Bấm «Dự báo 6 tháng» để overlay forecast lên chuỗi IIP thật (Dashboard pattern).
          </div>
        )}
        {forecast && (
          <>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={forecastVsActual}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="actual" stroke="#1e3a5f" strokeWidth={2} name="IIP actual" connectNulls={false} dot={false} />
                <Line type="monotone" dataKey="forecast" stroke="#0d9488" strokeWidth={2} strokeDasharray="5 5" name="Forecast" connectNulls={false} dot={false} />
              </LineChart>
            </ResponsiveContainer>
            <p className="chart-note">
              Actual: GET /api/dashboard/iip · Forecast: POST /api/ml/forecast ({forecast.horizon} tháng).
              Artifact thiếu → banner, không bịa đường tăng trưởng.
            </p>
          </>
        )}
        {!iip.length && (
          <div className="banner banner-warn" style={{ marginTop: 12 }}>
            Chưa có chuỗi IIP trên API — không ghép forecast với actual giả.
          </div>
        )}
      </div>

      <div className="chart-container">
        <h3>Feature importance (XGBoost)</h3>
        {!importance || !importance.available ? (
          <div className="empty-state">
            {importance?.message
              || 'Chưa có xgboost_importance.json — chạy make bootstrap / train XGBoost (#12). Không bịa gain/weight.'}
          </div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={Math.max(280, importanceBars.length * 22)}>
              <BarChart data={importanceBars} layout="vertical" margin={{ left: 120 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="feature" width={110} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="gain" fill="#0d9488" name="Gain" />
              </BarChart>
            </ResponsiveContainer>
            <p className="chart-note">
              Nguồn: GET /api/ml/feature-importance · {importance.source || 'artifact #12'} · top {importanceBars.length} theo gain
            </p>
          </>
        )}
        {selectedModel !== 'xgboost' && (
          <div className="banner banner-warn" style={{ marginTop: 12 }}>
            Model «{selectedModel}» không có feature-importance artifact (ARIMA/LSTM) — chỉ XGBoost.
          </div>
        )}
      </div>
    </div>
  )
}
