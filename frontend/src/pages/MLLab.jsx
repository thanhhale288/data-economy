import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar,
} from 'recharts'
import { api } from '../api'

export default function MLLab() {
  const [models, setModels] = useState([])
  const [predictions, setPredictions] = useState([])
  const [selectedModel, setSelectedModel] = useState('xgboost')
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading] = useState(true)
  const [training, setTraining] = useState(false)

  useEffect(() => {
    Promise.all([api.getModels(), api.getPredictions()])
      .then(([m, p]) => {
        setModels(m)
        setPredictions(p)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleTrain = async () => {
    setTraining(true)
    try {
      await api.trainModels()
      const [m, p] = await Promise.all([api.getModels(), api.getPredictions()])
      setModels(m)
      setPredictions(p)
    } catch (e) {
      console.error(e)
    } finally {
      setTraining(false)
    }
  }

  const handleForecast = async () => {
    try {
      const result = await api.forecast(selectedModel, 6)
      setForecast(result)
    } catch (e) {
      console.error(e)
    }
  }

  const modelPredictions = predictions.filter((p) => p.model_name === selectedModel)
  const chartData = modelPredictions.map((p) => ({
    period: p.period?.slice(0, 7),
    actual: p.actual_value,
    predicted: p.predicted_value,
  }))

  const metricsData = models
    .filter((m) => m.is_active)
    .map((m) => ({
      name: m.model_name,
      mae: m.metrics?.mae || 0,
      rmse: m.metrics?.rmse || 0,
      mape: m.metrics?.mape || 0,
    }))

  if (loading) return <div className="loading">Đang tải...</div>

  return (
    <div>
      <h2 className="page-title">ML Lab — Dự báo IIP</h2>

      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <button className="btn btn-primary" onClick={handleTrain} disabled={training}>
          {training ? 'Đang huấn luyện...' : 'Huấn luyện models'}
        </button>
        <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}
          style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #ddd' }}>
          <option value="arima">ARIMA</option>
          <option value="xgboost">XGBoost</option>
          <option value="lstm">LSTM</option>
        </select>
        <button className="btn btn-primary" onClick={handleForecast}>Dự báo 6 tháng</button>
      </div>

      <div className="cards">
        {models.filter((m) => m.is_active).map((m) => (
          <div className="card" key={m.id}>
            <div className="label">{m.model_name.toUpperCase()} ({m.model_type})</div>
            <div className="value" style={{ fontSize: 16 }}>
              MAE: {m.metrics?.mae ?? '—'} | RMSE: {m.metrics?.rmse ?? '—'}
            </div>
            <div className="sub">MAPE: {m.metrics?.mape ?? '—'}%</div>
          </div>
        ))}
      </div>

      <div className="chart-container">
        <h3>So sánh metric giữa các model</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={metricsData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="mae" fill="#e94560" name="MAE" />
            <Bar dataKey="rmse" fill="#0f3460" name="RMSE" />
            <Bar dataKey="mape" fill="#16a085" name="MAPE" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {chartData.length > 0 && (
        <div className="chart-container">
          <h3>Actual vs Predicted — {selectedModel.toUpperCase()}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="actual" stroke="#0f3460" strokeWidth={2} name="Actual" />
              <Line type="monotone" dataKey="predicted" stroke="#e94560" strokeWidth={2} strokeDasharray="5 5" name="Predicted" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {forecast && (
        <div className="chart-container">
          <h3>Dự báo {forecast.horizon} tháng — {forecast.model}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={forecast.forecasts}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="predicted_value" stroke="#e94560" strokeWidth={2} name="Forecast" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
