import { useEffect, useState } from 'react'
import { api } from '../api'

const CRAWLERS = [
  { id: 'all', label: 'Chạy tất cả' },
  { id: 'gso', label: 'GSO Macro' },
  { id: 'oecd', label: 'OECD' },
  { id: 'companies', label: 'Doanh nghiệp' },
  { id: 'marketplace', label: 'Marketplace' },
  { id: 'metrics', label: 'Digital Metrics' },
  { id: 'cleaning', label: 'Data Cleaning' },
  { id: 'features', label: 'Feature Engineering' },
  { id: 'ml', label: 'ML Training' },
]

const FAMILY_LABELS = {
  gso: 'GSO',
  oecd: 'OECD',
  companies: 'Doanh nghiệp',
  marketplace: 'Marketplace',
  data_cleaning: 'Data cleaning',
}

function formatTs(value) {
  return value ? new Date(value).toLocaleString('vi-VN') : '—'
}

/** Compact crawl/job logs for cards — full text stays in title tooltip. */
function shortenLog(text, maxLen = 88) {
  if (text == null || text === '') return null
  let s = String(text)
    .replace(/https?:\/\/\S+/gi, '')
    .replace(/Parsed\s+(\d+)\s+records\s+from\s*/gi, '$1 rec ')
    .replace(/\s+from\s*(?=[(;|]|$)/gi, ' ')
    .replace(/\bn=(\d+)\b/g, 'n=$1')
    .replace(/\s*[|;]\s*/g, ' · ')
    .replace(/\s{2,}/g, ' ')
    .replace(/\s+([.,;:])/g, '$1')
    .replace(/(\s·\s)+/g, ' · ')
    .trim()
  if (!s) return '—'
  if (s.length <= maxLen) return s
  return `${s.slice(0, maxLen - 1).trimEnd()}…`
}

function driftBadge(flag) {
  if (flag === true) return { className: 'badge-danger', label: 'drift' }
  if (flag === false) return { className: 'badge-success', label: 'stable' }
  return { className: 'badge-warning', label: 'unknown' }
}

function formatMetric(value) {
  if (value == null || Number.isNaN(Number(value))) return '—'
  return Number(value).toFixed(2)
}

export default function Pipeline() {
  const [jobs, setJobs] = useState([])
  const [status, setStatus] = useState(null)
  const [quality, setQuality] = useState(null)
  const [mlMonitor, setMlMonitor] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [triggering, setTriggering] = useState(null)

  const loadAll = async () => {
    setError(null)
    try {
      const [jobList, monitorStatus, qualityReport, monitoring] = await Promise.all([
        api.getPipelineJobs(),
        api.getPipelineStatus(),
        api.getPipelineQuality(),
        api.getMlMonitoring(),
      ])
      setJobs(jobList)
      setStatus(monitorStatus)
      setQuality(qualityReport)
      setMlMonitor(monitoring)
    } catch (e) {
      setError(e.message || 'Không tải được pipeline monitor')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    Promise.all([
      api.getPipelineJobs(),
      api.getPipelineStatus(),
      api.getPipelineQuality(),
      api.getMlMonitoring(),
    ])
      .then(([jobList, monitorStatus, qualityReport, monitoring]) => {
        if (cancelled) return
        setJobs(jobList)
        setStatus(monitorStatus)
        setQuality(qualityReport)
        setMlMonitor(monitoring)
      })
      .catch((e) => {
        if (!cancelled) setError(e.message || 'Không tải được pipeline monitor')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const handleTrigger = async (crawler) => {
    setTriggering(crawler)
    try {
      await api.triggerCrawl(crawler)
      setTimeout(() => {
        setLoading(true)
        loadAll()
      }, 2000)
    } catch (e) {
      setError(e.message || 'Trigger thất bại')
    } finally {
      setTriggering(null)
    }
  }

  const statusBadge = (s) => {
    const map = {
      success: 'badge-success',
      running: 'badge-info',
      failed: 'badge-danger',
      pending: 'badge-warning',
    }
    return map[s] || 'badge-warning'
  }

  if (loading && !jobs.length && !status && !quality && !mlMonitor) {
    return <div className="loading">Đang tải...</div>
  }

  const summary = quality?.available ? quality.summary : null
  const mlCounters = mlMonitor?.counters

  return (
    <div>
      <h2 className="page-title">Pipeline Monitor</h2>
      <p className="page-subtitle">
        Theo dõi health nguồn, lần chạy gần nhất, ML quality/drift contract và lịch sử job.
        Trạng thái fallback/unavailable hiện rõ — không giả lập nguồn hay drift khi thiếu artifact.
      </p>

      {error && (
        <div className="banner banner-warn mb-md" role="alert">
          {error}
        </div>
      )}

      <div className="toolbar pipeline-actions">
        {CRAWLERS.map((c) => (
          <button
            key={c.id}
            className={c.id === 'all' ? 'btn btn-primary' : 'btn'}
            disabled={triggering === c.id}
            onClick={() => handleTrigger(c.id)}
          >
            {triggering === c.id ? 'Đang chạy...' : c.label}
          </button>
        ))}
      </div>

      <div className="chart-container">
        <h3>Source health</h3>
        <p className="chart-note mt-0">
          Trạng thái nguồn từ DB + job gần nhất — fallback/unavailable hiện rõ.
          Card <strong>CafeF / BCTC</strong> cho biết có bao nhiêu báo cáo gắn URL CafeF
          so với seed/fallback.
          {status?.sample_size != null ? ` · Mẫu DB: ${status.sample_size} DN` : ''}
        </p>
        {!status?.source_health?.length ? (
          <div className="empty-state">Chưa có source_health từ API.</div>
        ) : (
          <div className="cards">
            {status.source_health.map((src) => {
              const badge =
                src.status === 'ok'
                  ? 'badge-success'
                  : src.status === 'fallback'
                    ? 'badge-warning'
                    : src.status === 'unavailable'
                      ? 'badge-danger'
                      : 'badge-warning'
              return (
                <div className="card" key={src.source}>
                  <div className="label">{src.label}</div>
                  <div className="mt-sm">
                    <span className={`badge ${badge}`}>{src.status}</span>
                    {src.records != null && (
                      <span className="sub muted gap-inline-sm">
                        {src.records} records
                      </span>
                    )}
                  </div>
                  <div className="sub muted log-snip mt-sm" title={src.detail || undefined}>
                    {shortenLog(src.detail) || '—'}
                  </div>
                  <div className="sub muted">
                    Last success: {formatTs(src.last_success_at)}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <div className="chart-container">
        <h3>Lần chạy cuối (crawl + cleaning)</h3>
        {status?.note && <p className="chart-note">{status.note}</p>}
        {status?.last_runs?.some((r) => r.family === 'data_cleaning' && !r.status) && (
          <div className="banner banner-warn mb-sm" role="status">
            Job <code>data_cleaning</code> chưa từng chạy — bấm «Data Cleaning» hoặc{' '}
            <code>make bootstrap</code>. Chưa có parquet sạch / cleaning_report.
          </div>
        )}
        {!status?.last_runs?.length ? (
          <div className="empty-state">Chưa có tóm tắt last run từ API.</div>
        ) : (
          <div className="cards">
            {status.last_runs.map((run) => (
              <div className="card" key={run.family}>
                <div className="label">{FAMILY_LABELS[run.family] || run.family}</div>
                <div className="value card-value-md">
                  {run.status ? (
                    <span className={`badge ${statusBadge(run.status)}`}>{run.status}</span>
                  ) : (
                    <span className="badge badge-warning">chưa chạy</span>
                  )}
                </div>
                <div className="sub muted">
                  {run.job_name || 'chưa có job'} · {formatTs(run.finished_at)}
                </div>
                {run.records_processed != null && (
                  <div className="sub">{run.records_processed} records</div>
                )}
                {run.error_message && (
                  <div className="sub log-snip text-danger" title={run.error_message}>
                    {shortenLog(run.error_message)}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="chart-container">
        <h3>Tóm tắt quality report</h3>
        {!quality?.available ? (
          <div className="empty-state">
            <p>
              {quality?.message
                || 'Chưa có cleaning_report.json — chạy Data Cleaning / make bootstrap.'}
            </p>
            {quality?.report_path && (
              <p className="chart-note mt-sm">
                Đường dẫn kỳ vọng: <code>{quality.report_path}</code>
              </p>
            )}
          </div>
        ) : (
          <>
            <div className="metric-strip">
              <span className="metric-chip">
                <strong>NaN / gap filled</strong>
                <span>{summary?.nan_filled ?? '—'}</span>
              </span>
              <span className="metric-chip">
                <strong>Outliers handled</strong>
                <span>{summary?.outliers_handled ?? '—'}</span>
              </span>
              <span className="metric-chip">
                <strong>MP outliers flagged</strong>
                <span>{summary?.marketplace_outliers_flagged ?? '—'}</span>
              </span>
              <span className="metric-chip">
                <strong>VSIC fail</strong>
                <span>{summary?.vsic_fails ?? '—'}</span>
              </span>
            </div>
          </>
        )}
      </div>

      <div className="chart-container">
        <h3>ML monitoring (quality / drift)</h3>
        <p className="chart-note mt-0">
          Contract từ <code>GET /api/ml/monitoring</code>. Drift chỉ có khi có baseline artifact —
          thiếu metrics/baseline → null + warning, không bịa.
        </p>
        {!mlMonitor ? (
          <div className="empty-state">Chưa tải được ML monitoring.</div>
        ) : (
          <>
            {mlMonitor.warnings?.length > 0 && (
              <div className="banner banner-warn mb-sm" role="status">
                {mlMonitor.warnings.join(' · ')}
              </div>
            )}
            <div className="metric-strip" role="region" aria-label="ML monitoring counters">
              <span className="metric-chip">
                <strong>Models tracked</strong>
                <span>{mlCounters?.models_tracked ?? '—'}</span>
              </span>
              <span className="metric-chip">
                <strong>With metrics</strong>
                <span>{mlCounters?.models_with_metrics ?? '—'}</span>
              </span>
              <span className="metric-chip">
                <strong>Missing metrics</strong>
                <span>{mlCounters?.models_missing_metrics ?? '—'}</span>
              </span>
              <span className="metric-chip">
                <strong>Drift flagged</strong>
                <span>{mlCounters?.models_with_drift ?? '—'}</span>
              </span>
              <span className="metric-chip">
                <strong>Artifacts on disk</strong>
                <span>{mlCounters?.artifacts_on_disk ?? '—'}</span>
              </span>
              <span className="metric-chip">
                <strong>Baseline</strong>
                <span>{mlCounters?.baseline_available ? 'yes' : 'no'}</span>
              </span>
              <span className="metric-chip">
                <strong>Feedback signals</strong>
                <span>{mlCounters?.feedback_signals_count ?? '—'}</span>
              </span>
            </div>
            {!mlMonitor.models?.length ? (
              <div className="empty-state">Chưa có model snapshot.</div>
            ) : (
              <div className="table-scroll mt-md">
                <table>
                  <thead>
                    <tr>
                      <th>Model</th>
                      <th>Drift</th>
                      <th>MAPE</th>
                      <th>MAE</th>
                      <th>Samples</th>
                      <th>Artifact</th>
                      <th>As of</th>
                      <th>Warning</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mlMonitor.models.map((m) => {
                      const badge = driftBadge(m.drift_flag)
                      return (
                        <tr key={m.model_name}>
                          <td>{m.model_name}</td>
                          <td>
                            <span className={`badge ${badge.className}`}>{badge.label}</span>
                            {m.drift_score != null && (
                              <span className="sub muted gap-inline-sm">
                                Δ {formatMetric(m.drift_score)}
                              </span>
                            )}
                          </td>
                          <td>{formatMetric(m.metrics?.mape)}</td>
                          <td>{formatMetric(m.metrics?.mae)}</td>
                          <td>{m.sample_count ?? '—'}</td>
                          <td>
                            <span
                              className={`badge ${m.artifact_present ? 'badge-success' : 'badge-warning'}`}
                            >
                              {m.artifact_present ? 'yes' : 'no'}
                            </span>
                          </td>
                          <td>{formatTs(m.as_of)}</td>
                          <td className="log-snip" title={m.warning || undefined}>
                            {shortenLog(m.warning, 48) || '—'}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>

      <div className="chart-container">
        <h3>Lịch sử job</h3>
        {!jobs.length ? (
          <div className="empty-state">
            Chưa có pipeline_jobs — bấm trigger hoặc chạy scheduler.
          </div>
        ) : (
          <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Job</th>
                <th>Trạng thái</th>
                <th>Records</th>
                <th>Bắt đầu</th>
                <th>Kết thúc</th>
                <th>Chi tiết / Lỗi</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.id}>
                  <td>{j.job_name}</td>
                  <td>
                    <span className={`badge ${statusBadge(j.status)}`}>{j.status}</span>
                  </td>
                  <td>{j.records_processed}</td>
                  <td>{formatTs(j.started_at)}</td>
                  <td>{formatTs(j.finished_at)}</td>
                  <td
                    className={`log-snip${j.error_message ? ' text-danger' : ''}`}
                    title={j.error_message || j.detail || undefined}
                  >
                    {shortenLog(j.error_message || j.detail, 72) || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </div>
    </div>
  )
}
