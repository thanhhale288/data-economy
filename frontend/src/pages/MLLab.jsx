import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, Scatter, ComposedChart,
} from 'recharts'
import { api } from '../api'
import MetricInfoTip from '../MetricInfoTip'
import { formatIndex } from '../format'

const MODEL_OPTIONS = [
  { id: 'arima', label: 'ARIMA', color: '#164654' },
  { id: 'xgboost', label: 'XGBoost', color: '#367ea2' },
  { id: 'lightgbm', label: 'LightGBM', color: '#2a9d8f' },
  { id: 'lstm', label: 'LSTM', color: '#7fbde0' },
]

const TREE_IMPORTANCE_MODELS = new Set(['xgboost', 'lightgbm'])

/** Plain-language help for each IIP forecast model (hover / focus tip). */
const MODEL_TIPS = {
  arima: {
    title: 'ARIMA',
    formula: 'Nhóm STATISTICAL — mô hình thống kê',
    blurb:
      'Dự báo IIP theo chuỗi thời gian: nhìn xu hướng và chu kỳ trong quá khứ của chính chỉ số đó. Không dựa vào nhiều biến ngoài (doanh thu số, adoption…). Phù hợp khi muốn baseline “chỉ từ lịch sử IIP”.',
  },
  xgboost: {
    title: 'XGBoost',
    formula: 'Nhóm ML — học máy (cây quyết định tăng cường)',
    blurb:
      'Học quan hệ từ nhiều đặc trưng (feature) — ví dụ tín hiệu số hóa, biến kinh tế — rồi dự báo IIP. Thường giải thích được feature nào quan trọng (xem biểu đồ Feature importance).',
  },
  lightgbm: {
    title: 'LightGBM',
    formula: 'Nhóm ML — gradient boosting (leaf-wise)',
    blurb:
      'Cùng họ cây quyết định tăng cường với XGBoost, thường nhanh hơn trên bảng đặc trưng thưa. Target vẫn là IIP; so sánh song song với XGBoost trên cùng feature frame.',
  },
  lstm: {
    title: 'LSTM',
    formula: 'Nhóm DL — học sâu (mạng nơ-ron)',
    blurb:
      'Mạng nơ-ron chuyên chuỗi thời gian: nhớ pattern dài hạn trong dữ liệu lịch sử để dự báo IIP. Mạnh khi chuỗi phức tạp, nhưng khó giải thích từng bước hơn ARIMA/XGBoost.',
  },
}

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

function buildAnomalyTimeline(seriesBlock) {
  if (!seriesBlock?.points?.length) return []
  return seriesBlock.points.map((pt) => ({
    period: periodLabel(pt.period),
    value: pt.value ?? null,
    score: pt.score ?? null,
    anomaly: pt.is_anomaly ? pt.value : null,
  }))
}

export default function MLLab() {
  const [models, setModels] = useState([])
  const [predictions, setPredictions] = useState([])
  const [iip, setIip] = useState([])
  const [importance, setImportance] = useState(null)
  const [anomaly, setAnomaly] = useState(null)
  const [anomalyError, setAnomalyError] = useState(null)
  const [selectedModel, setSelectedModel] = useState('xgboost')
  const [forecast, setForecast] = useState(null)
  const [forecastError, setForecastError] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [training, setTraining] = useState(false)

  const importanceModel = TREE_IMPORTANCE_MODELS.has(selectedModel)
    ? selectedModel
    : 'xgboost'

  const reloadCore = async () => {
    const [m, p, iipSeries, fi] = await Promise.all([
      api.getModels(),
      api.getPredictions(),
      api.getIip(),
      api.getFeatureImportance(importanceModel).catch(() => null),
    ])
    setModels(m)
    setPredictions(p)
    setIip(iipSeries)
    setImportance(fi)
    try {
      const anom = await api.getAnomalies()
      setAnomaly(anom)
      setAnomalyError(null)
    } catch (e) {
      setAnomaly(null)
      setAnomalyError(e.message || 'Không tải được anomaly')
    }
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

  useEffect(() => {
    if (!TREE_IMPORTANCE_MODELS.has(selectedModel)) return undefined
    let cancelled = false
    const load = selectedModel === 'lightgbm'
      ? api.getLightgbmFeatureImportance()
      : api.getFeatureImportance(selectedModel)
    load
      .then((fi) => {
        if (!cancelled) setImportance(fi)
      })
      .catch(() => {
        if (!cancelled) setImportance(null)
      })
    return () => { cancelled = true }
  }, [selectedModel])

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
      const result = selectedModel === 'lightgbm'
        ? await api.forecastLightgbm(6)
        : await api.forecast(selectedModel, 6)
      setForecast(result)
    } catch (err) {
      setForecast(null)
      setForecastError(
        err?.message?.includes('404')
          ? `Chưa có artifact forecast cho model «${selectedModel}» — chạy make bootstrap / train ML.`
          : `Không tải được forecast (${selectedModel}): ${err.message}`
      )
    }
  }

  const handleReloadAnomaly = async () => {
    setAnomalyError(null)
    try {
      const anom = await api.getAnomalies()
      setAnomaly(anom)
    } catch (e) {
      setAnomalyError(e.message || 'Không tải được anomaly')
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
    ? importance.features.slice(0, 10).map((f) => ({
        feature: f.feature,
        gain: f.gain,
      }))
    : []

  const iipAnomalyTimeline = buildAnomalyTimeline(anomaly?.iip)
  const vaAnomalyTimeline = buildAnomalyTimeline(anomaly?.va)
  const iipAnomalyCount = anomaly?.iip?.n_anomalies ?? 0
  const vaAnomalyCount = anomaly?.va?.n_anomalies ?? 0

  const noRegistry = latestModels.length === 0
  const noPredictions = predictions.length === 0

  return (
    <div>
      <h2 className="page-title">ML Lab — So sánh model IIP</h2>
      <p className="page-subtitle">
        So sánh ARIMA / XGBoost / LightGBM / LSTM trên cùng chuỗi IIP. Metric trống hoặc artifact
        thiếu hiện N/A / cảnh báo — không bịa MAE hay đường dự báo.
      </p>

      {loadError && (
        <div className="banner banner-warn mb-md" role="alert">{loadError}</div>
      )}

      {noRegistry && (
        <div className="empty-state mb-md">
          Chưa có model trong <code>model_registry</code> — chạy <code>make bootstrap</code> hoặc
          nút train bên dưới.
        </div>
      )}
      <div className="toolbar">
        <select
          value={selectedModel}
          onChange={(e) => {
            setSelectedModel(e.target.value)
            setForecast(null)
            setForecastError(null)
          }}
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
              <div className="card-label-row">
                <div className="label">{opt.label}{m?.model_type ? ` (${m.model_type})` : ''}</div>
                {MODEL_TIPS[opt.id] ? (
                  <MetricInfoTip {...MODEL_TIPS[opt.id]} placement="below" />
                ) : null}
              </div>
              {m ? (
                <>
                  <div className="value card-value-sm">
                    MAE: {formatIndex(m.metrics?.mae)} | RMSE: {formatIndex(m.metrics?.rmse)}
                  </div>
                  <div className="sub">
                    MAPE: {formatIndex(m.metrics?.mape, { suffix: '%' })}
                    {status ? ` · status: ${status}` : ''}
                    {!m.is_active ? ' · inactive' : ''}
                  </div>
                </>
              ) : (
                <div className="sub">Chưa có trong registry</div>
              )}
            </div>
          )
        })}
      </div>

      <div className="chart-container">
        <div className="card-label-row" style={{ marginBottom: '0.5rem' }}>
          <h3 style={{ margin: 0 }}>Anomaly timeline (IIP / VA)</h3>
          <button className="btn" type="button" onClick={handleReloadAnomaly}>
            Tải lại anomaly
          </button>
        </div>
        {anomalyError && (
          <div className="banner banner-warn mb-sm" role="status">{anomalyError}</div>
        )}
        {!anomaly && !anomalyError && (
          <div className="empty-state">Chưa có phản hồi anomaly từ API.</div>
        )}
        {anomaly && !anomaly.available && (
          <div className="empty-state">
            {anomaly.message
              || 'Chuỗi IIP/VA chưa đủ dài để chạy Isolation Forest — không bịa điểm bất thường.'}
          </div>
        )}
        {anomaly?.available && (
          <>
            <p className="page-subtitle" style={{ marginTop: 0 }}>
              IIP anomalies: {iipAnomalyCount}
              {anomaly.va ? ` · VA anomalies: ${vaAnomalyCount}` : ''}
              {anomaly.threshold != null ? ` · threshold: ${formatIndex(anomaly.threshold)}` : ''}
            </p>
            {iipAnomalyTimeline.length === 0 ? (
              <div className="empty-state">IIP series unavailable — không vẽ timeline giả.</div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={iipAnomalyTimeline}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                  <YAxis tickFormatter={(v) => formatIndex(v)} />
                  <Tooltip formatter={(value) => formatIndex(value)} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#164654"
                    strokeWidth={2}
                    name="IIP"
                    dot={false}
                    connectNulls={false}
                  />
                  <Scatter dataKey="anomaly" fill="#c45c26" name="Anomaly" />
                </ComposedChart>
              </ResponsiveContainer>
            )}
            {anomaly.va?.available && vaAnomalyTimeline.length > 0 && (
              <ResponsiveContainer width="100%" height={260}>
                <ComposedChart data={vaAnomalyTimeline}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                  <YAxis tickFormatter={(v) => formatIndex(v)} />
                  <Tooltip formatter={(value) => formatIndex(value)} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#367ea2"
                    strokeWidth={2}
                    name="VA"
                    dot={false}
                    connectNulls={false}
                  />
                  <Scatter dataKey="anomaly" fill="#c45c26" name="VA anomaly" />
                </ComposedChart>
              </ResponsiveContainer>
            )}
            {(anomaly.warnings?.length > 0) && (
              <div className="banner banner-warn mt-sm" role="status">
                {anomaly.warnings.join(' · ')}
              </div>
            )}
          </>
        )}
      </div>

      <div className="chart-container">
        <h3>So sánh metric (registry)</h3>
        {metricsData.length === 0 ? (
          <div className="empty-state">
            Chưa có MAE/RMSE/MAPE trong registry — chạy make bootstrap / train để cập nhật.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={metricsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={(v) => formatIndex(v)} />
              <Tooltip formatter={(value) => formatIndex(value)} />
              <Legend />
              <Bar dataKey="mae" fill="#367ea2" name="MAE" />
              <Bar dataKey="rmse" fill="#164654" name="RMSE" />
              <Bar dataKey="mape" fill="#7fbde0" name="MAPE %" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="chart-container">
        <h3>Holdout — actual vs predicted</h3>
        {noPredictions ? (
          <div className="empty-state">
            Chưa có hàng trong <code>model_predictions</code> — cửa sổ holdout được ghi khi train
            (make bootstrap / nút huấn luyện).
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={holdoutCompare}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => formatIndex(v)} />
              <Tooltip formatter={(value) => formatIndex(value)} />
              <Legend />
              <Line type="monotone" dataKey="actual" stroke="#164654" strokeWidth={2} name="Actual IIP" dot={false} connectNulls={false} />
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
              <YAxis tickFormatter={(v) => formatIndex(v)} />
              <Tooltip formatter={(value) => formatIndex(value)} />
              <Legend />
              <Line type="monotone" dataKey="actual" stroke="#164654" strokeWidth={2} name="Actual" connectNulls={false} />
              <Line type="monotone" dataKey="predicted" stroke="#367ea2" strokeWidth={2} strokeDasharray="5 5" name="Predicted" connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="chart-container">
        <h3>Forecast vs actual IIP — {selectedModel.toUpperCase()}</h3>
        {forecastError && (
          <div className="banner banner-warn mb-sm" role="status">{forecastError}</div>
        )}
        {!forecast && !forecastError && (
          <div className="empty-state">
            Chưa có đường dự báo trên biểu đồ. Bấm «Dự báo 6 tháng» phía trên để xem dự báo so với IIP thực tế.
          </div>
        )}
        {forecast && (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={forecastVsActual}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => formatIndex(v)} />
              <Tooltip formatter={(value) => formatIndex(value)} />
              <Legend />
              <Line type="monotone" dataKey="actual" stroke="#164654" strokeWidth={2} name="IIP actual" connectNulls={false} dot={false} />
              <Line type="monotone" dataKey="forecast" stroke="#367ea2" strokeWidth={2} strokeDasharray="5 5" name="Forecast" connectNulls={false} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
        {!iip.length && (
          <div className="banner banner-warn mt-sm" role="status">
            Chưa có chuỗi IIP trên API — cần dữ liệu IIP trước khi đối chiếu forecast.
          </div>
        )}
      </div>

      <div className="chart-container">
        <h3>Feature importance ({importanceModel})</h3>
        {!importance || !importance.available ? (
          <div className="empty-state">
            {importance?.message
              || `Chưa có ${importanceModel}_importance.json — chạy make bootstrap / train.`}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(280, importanceBars.length * 22)}>
            <BarChart data={importanceBars} layout="vertical" margin={{ left: 120 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tickFormatter={(v) => formatIndex(v)} />
              <YAxis type="category" dataKey="feature" width={110} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(value) => formatIndex(value)} />
              <Bar dataKey="gain" fill="#367ea2" name="Gain" />
            </BarChart>
          </ResponsiveContainer>
        )}
        {!TREE_IMPORTANCE_MODELS.has(selectedModel) && (
          <div className="banner banner-warn mt-sm" role="status">
            Model «{selectedModel}» không có feature-importance artifact — chỉ XGBoost/LightGBM.
            Đang hiện importance của «{importanceModel}».
          </div>
        )}
      </div>
    </div>
  )
}
