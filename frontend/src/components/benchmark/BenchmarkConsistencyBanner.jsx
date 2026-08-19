/**
 * Task #94 — BCTC consistency banner.
 *
 * Shows nothing when:
 *   - no report yet (null / undefined)
 *   - no DB record for the ticker (has_db_record=false) — silence is correct;
 *     the endpoint already records "no_db_record" in flags but we shouldn't
 *     alarm users about a data absence that's expected for new/unknown tickers.
 *   - all flags are "ok" (consistent data)
 *
 * Shows a warning banner only when at least one flag is "mismatch" (≥10% diff).
 */

export default function BenchmarkConsistencyBanner({ report }) {
  if (!report || !report.has_db_record) return null

  const mismatches = report.flags.filter((f) => f.severity === 'mismatch')
  if (mismatches.length === 0) return null

  return (
    <div className="banner banner-warn mt-md" role="status">
      <strong>Lệch BCTC lịch sử ({report.ticker} · kỳ {report.period}):</strong>{' '}
      {report.summary}
      <ul className="consistency-flag-list">
        {mismatches.map((f) => (
          <li key={f.extract_field}>
            <code>{f.extract_field}</code>
            {f.rel_deviation != null
              ? ` — lệch ${(f.rel_deviation * 100).toFixed(1)}%`
              : ''}
            {f.db_value != null && (
              <span className="consistency-db-hint">
                {' '}(DB: {f.db_value.toLocaleString('vi-VN')})
              </span>
            )}
          </li>
        ))}
      </ul>
      <p className="consistency-note">
        Kiểm tra lại trước khi bấm so sánh. Hệ thống không tự ghi đè dữ liệu lịch sử.
      </p>
    </div>
  )
}
