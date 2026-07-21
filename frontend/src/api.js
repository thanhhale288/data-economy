const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function formatApiError(status, detail) {
  const d = typeof detail === 'string' ? detail : ''
  if (status === 404) {
    if (/forecast|artifact|model/i.test(d)) {
      return `API 404: ${d || 'Thiếu artifact — chạy make bootstrap / train ML.'}`
    }
    if (/prefill|BCTC/i.test(d)) {
      return `API 404: ${d || 'Không có BCTC đủ field để prefill.'}`
    }
    if (/cleaning_report|quality/i.test(d)) {
      return `API 404: ${d || 'Thiếu cleaning_report — chạy data_cleaning.'}`
    }
    return d ? `API 404: ${d}` : 'API 404: không tìm thấy tài nguyên.'
  }
  if (status === 503 || status === 502) {
    return `API ${status}: dịch vụ tạm unavailable${d ? ` — ${d}` : ''}.`
  }
  return `API error: ${status}${d ? `: ${d}` : ''}`
}

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}/api${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    let detail = ''
    try {
      const body = await res.json()
      detail = body?.detail
        ? (typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail))
        : ''
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(formatApiError(res.status, detail))
  }
  return res.json()
}

export const api = {
  getSummary: () => request('/dashboard/summary'),
  getIip: (vsic = 'C') => request(`/dashboard/iip?vsic_code=${vsic}`),
  getHeatmap: () => request('/dashboard/heatmap'),
  getOecdVsGso: () => request('/dashboard/oecd-vs-gso'),
  getCompanies: () => request('/companies/'),
  getCompany: (code) => request(`/companies/${code}`),
  getPipelineJobs: () => request('/pipeline/jobs'),
  getPipelineStatus: () => request('/pipeline/status'),
  getPipelineQuality: () => request('/pipeline/quality'),
  triggerCrawl: (crawler) => request('/pipeline/trigger', {
    method: 'POST',
    body: JSON.stringify({ crawler }),
  }),
  getModels: () => request('/ml/models'),
  getPredictions: (model) => request(`/ml/predictions${model ? `?model_name=${model}` : ''}`),
  getFeatureImportance: (model = 'xgboost') =>
    request(`/ml/feature-importance?model_name=${encodeURIComponent(model)}`),
  trainModels: () => request('/ml/train', { method: 'POST' }),
  forecast: (model, horizon) => request('/ml/forecast', {
    method: 'POST',
    body: JSON.stringify({ model_name: model, horizon_months: horizon }),
  }),
  benchmark: (data) => request('/benchmark/compare', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  benchmarkPrefill: (stockCode) => request(`/benchmark/prefill/${encodeURIComponent(stockCode)}`),
}
