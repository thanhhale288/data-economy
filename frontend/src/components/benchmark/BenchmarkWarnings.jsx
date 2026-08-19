import { WARNING_LABELS } from './benchmarkLabels'

export default function BenchmarkWarnings({ warnings }) {
  if (!warnings?.length) return null

  return (
    <div className="banner-stack">
      {warnings.map((code) => (
        <div
          key={code}
          className="banner banner-warn"
          role="status"
        >
          <span className="badge badge-warning warning-code">{code}</span>
          {WARNING_LABELS[code] || code}
        </div>
      ))}
    </div>
  )
}
