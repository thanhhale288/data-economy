import { useEffect, useState } from 'react'
import { api } from '../api'

const CRAWLERS = [
  { id: 'all', label: 'Chạy tất cả' },
  { id: 'gso', label: 'GSO Macro' },
  { id: 'oecd', label: 'OECD' },
  { id: 'companies', label: 'Doanh nghiệp' },
  { id: 'marketplace', label: 'Marketplace' },
  { id: 'metrics', label: 'Digital Metrics' },
  { id: 'features', label: 'Feature Engineering' },
  { id: 'ml', label: 'ML Training' },
]

export default function Pipeline() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(null)

  const loadJobs = () => {
    api.getPipelineJobs()
      .then(setJobs)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadJobs() }, [])

  const handleTrigger = async (crawler) => {
    setTriggering(crawler)
    try {
      await api.triggerCrawl(crawler)
      setTimeout(loadJobs, 2000)
    } catch (e) {
      console.error(e)
    } finally {
      setTriggering(null)
    }
  }

  const statusBadge = (status) => {
    const map = {
      success: 'badge-success',
      running: 'badge-info',
      failed: 'badge-danger',
      pending: 'badge-warning',
    }
    return map[status] || 'badge-warning'
  }

  if (loading) return <div className="loading">Đang tải...</div>

  return (
    <div>
      <h2 className="page-title">Pipeline Monitor</h2>

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

      <table>
        <thead>
          <tr>
            <th>Job</th>
            <th>Trạng thái</th>
            <th>Records</th>
            <th>Bắt đầu</th>
            <th>Kết thúc</th>
            <th>Lỗi</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((j) => (
            <tr key={j.id}>
              <td>{j.job_name}</td>
              <td><span className={`badge ${statusBadge(j.status)}`}>{j.status}</span></td>
              <td>{j.records_processed}</td>
              <td>{j.started_at ? new Date(j.started_at).toLocaleString('vi-VN') : '—'}</td>
              <td>{j.finished_at ? new Date(j.finished_at).toLocaleString('vi-VN') : '—'}</td>
              <td style={{ color: '#e94560', fontSize: 12 }}>{j.error_message || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
