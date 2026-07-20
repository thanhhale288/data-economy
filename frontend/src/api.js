const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}/api${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    let detail = ''
    try {
      const body = await res.json()
      detail = body?.detail ? `: ${body.detail}` : ''
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(`API error: ${res.status}${detail}`)
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
  trainModels: () => request('/ml/train', { method: 'POST' }),
  forecast: (model, horizon) => request('/ml/forecast', {
    method: 'POST',
    body: JSON.stringify({ model_name: model, horizon_months: horizon }),
  }),
  benchmark: (data) => request('/benchmark/compare', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
}
