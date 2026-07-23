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

export default function Pipeline() {
  const [jobs, setJobs] = useState([])
  const [status, setStatus] = useState(null)
  const [quality, setQuality] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [triggering, setTriggering] = useState(null)

  const loadAll = async () => {
    setError(null)
    try {
      const [jobList, monitorStatus, qualityReport] = await Promise.all([
        api.getPipelineJobs(),
        api.getPipelineStatus(),
        api.getPipelineQuality(),
      ])
      setJobs(jobList)
      setStatus(monitorStatus)
      setQuality(qualityReport)
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
    ])
      .then(([jobList, monitorStatus, qualityReport]) => {
        if (cancelled) return
        setJobs(jobList)
        setStatus(monitorStatus)
        setQuality(qualityReport)
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

  if (loading && !jobs.length && !status && !quality) {
    return <div className="loading">Đang tải...</div>
  }

  const summary = quality?.available ? quality.summary : null

  return (
    <div>
      <h2 className="page-title">Pipeline Monitor</h2>
      <p className="page-subtitle">
        Module 3 · job crawl + data_cleaning · quality từ parquet / cleaning_report
      </p>

      {error && (
        <div className="empty-state" style={{ marginBottom: 16 }}>
          {error}
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 24 }}>
        {CRAWLERS.map((c) => (
          <button
            key={c.id}
            className="btn btn-primary"
            disabled={triggering === c.id}
            onClick={() => handleTrigger(c.id)}
          >
            {triggering === c.id ? 'Đang chạy...' : c.label}
          </button>
        ))}
      </div>

      <div className="chart-container" style={{ marginBottom: 24 }}>
        <h3>Source health</h3>
        <p className="chart-note" style={{ marginTop: 0 }}>
          Trạng thái nguồn từ DB + job gần nhất — fallback/unavailable hiện rõ.
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
                  <div style={{ marginTop: 8 }}>
                    <span className={`badge ${badge}`}>{src.status}</span>
                    {src.records != null && (
                      <span className="sub muted" style={{ marginLeft: 8 }}>
                        {src.records} records
                      </span>
                    )}
                  </div>
                  <div className="sub muted" style={{ marginTop: 8 }}>
                    {src.detail || '—'}
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

      <div className="chart-container" style={{ marginBottom: 24 }}>
        <h3>Lần chạy cuối (crawl + cleaning)</h3>
        {status?.note && <p className="chart-note">{status.note}</p>}
        {status?.last_runs?.some((r) => r.family === 'data_cleaning' && !r.status) && (
          <div className="banner banner-warn" style={{ marginBottom: 12 }}>
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
                <div className="value" style={{ fontSize: 18 }}>
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
                  <div className="sub" style={{ color: '#0d9488', fontSize: 12 }}>
                    {run.error_message}
                  </div>
                )}
                {run.detail && !run.error_message && (
                  <div className="sub muted" style={{ fontSize: 12 }}>{run.detail}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="chart-container" style={{ marginBottom: 24 }}>
        <h3>Tóm tắt quality report</h3>
        {!quality?.available ? (
          <div className="empty-state">
            <p>
              {quality?.message
                || 'Chưa có cleaning_report.json — chạy Data Cleaning / make bootstrap.'}
            </p>
            {quality?.report_path && (
              <p className="chart-note" style={{ marginTop: 8 }}>
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
            <p className="chart-note">
              Nguồn: {quality.report_path}
              {summary?.series_missing?.length
                ? ` · series_missing: ${summary.series_missing.join(', ')}`
                : ' · series_missing: none'}
              {summary?.artifacts?.length
                ? ` · artifacts: ${summary.artifacts.join(', ')}`
                : ''}
            </p>
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
                    style={{
                      color: j.error_message ? 'var(--danger)' : undefined,
                      fontSize: 12,
                    }}
                  >
                    {j.error_message || j.detail || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
