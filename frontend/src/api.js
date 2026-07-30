// Empty string = same-origin (/api/...). Do not use || — '' is falsy and would fall back to localhost.
const raw = import.meta.env.VITE_API_URL
const API_URL =
  raw === undefined || raw === null ? 'http://localhost:8000' : String(raw).replace(/\/$/, '')


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
  const headers = { ...(options.headers || {}) }
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  if (!isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }
  const res = await fetch(`${API_URL}/api${path}`, {
    headers,
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
  getVa: (indicator = 'VA_C', vsic = 'C') =>
    request(
      `/dashboard/va?indicator_code=${encodeURIComponent(indicator)}&vsic_code=${encodeURIComponent(vsic)}`,
    ),
  getHeatmap: () => request('/dashboard/heatmap'),
  getOecdVsGso: () => request('/dashboard/oecd-vs-gso'),
  getCompanies: (vsic) =>
    request(`/companies/${vsic ? `?vsic=${encodeURIComponent(vsic)}` : ''}`),
  getCompany: (code) => request(`/companies/${code}`),
  getPipelineJobs: () => request('/pipeline/jobs'),
  getPipelineStatus: () => request('/pipeline/status'),
  getPipelineQuality: () => request('/pipeline/quality'),
  getMlMonitoring: () => request('/ml/monitoring'),
  triggerCrawl: (crawler, tickers) =>
    request('/pipeline/trigger', {
      method: 'POST',
      body: JSON.stringify(
        tickers?.length ? { crawler, tickers } : { crawler },
      ),
    }),
  getModels: () => request('/ml/models'),
  getPredictions: (model) => request(`/ml/predictions${model ? `?model_name=${model}` : ''}`),
  getFeatureImportance: (model = 'xgboost') =>
    request(`/ml/feature-importance?model_name=${encodeURIComponent(model)}`),
  /** Task #58 — LightGBM importance helper (same endpoint, explicit model). */
  getLightgbmFeatureImportance: () =>
    request('/ml/feature-importance?model_name=lightgbm'),
  /** Task #57/#58 — Isolation Forest anomaly scores for IIP (+ optional VA). */
  getAnomalies: ({ vsic = 'C', includeVa = true, contamination } = {}) => {
    const params = new URLSearchParams({
      vsic_code: vsic,
      include_va: String(includeVa),
    })
    if (contamination != null) params.set('contamination', String(contamination))
    return request(`/ml/anomaly?${params.toString()}`)
  },
  trainModels: () => request('/ml/train', { method: 'POST' }),
  forecast: (model, horizon) => request('/ml/forecast', {
    method: 'POST',
    body: JSON.stringify({ model_name: model, horizon_months: horizon }),
  }),
  /** Task #58 — explicit LightGBM forecast helper. */
  forecastLightgbm: (horizon = 6) =>
    request('/ml/forecast', {
      method: 'POST',
      body: JSON.stringify({ model_name: 'lightgbm', horizon_months: horizon }),
    }),
  benchmark: (data) => request('/benchmark/compare', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  benchmarkPrefill: (stockCode) => request(`/benchmark/prefill/${encodeURIComponent(stockCode)}`),
  benchmarkExtract: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/benchmark/extract', {
      method: 'POST',
      body: form,
    })
  },
  /** Task #61 — Vietnamese narrative from BenchmarkResult numbers only. */
  benchmarkNarrative: (result) =>
    request('/benchmark/narrative', {
      method: 'POST',
      body: JSON.stringify(result),
    }),
  /** Task #64 — safe edit→confirm training signal (no raw PDF/bytes). */
  benchmarkFeedback: (payload) =>
    request('/benchmark/feedback', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  /** ADR-0003 / Task #50 — honesty label; empty universe stub is valid. */
  getUniverseCoverage: () => request('/universe/coverage'),
}
