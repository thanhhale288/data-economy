import { formatGrouped, formatMoney } from '../../format.js'
import {
  COMPARISON_LABELS,
  DEBT_COMPARISON_LABELS,
  HIGHER_IS_WORSE,
  METRIC_LABELS,
  METRIC_SHORT,
} from './benchmarkLabels.js'

export function formatRatio(value, metricKey) {
  if (value == null) return '—'
  if (typeof value !== 'number') return value
  if (metricKey === 'revenue_per_worker' || metricKey === 'profit_per_worker') {
    const abs = Math.abs(value)
    if (abs >= 1e6 && abs < 1e9) {
      return `${formatGrouped(value / 1e6, { maxFractionDigits: 0 })}M VND`
    }
    return formatMoney(value, 'VND')
  }
  if (
    metricKey === 'debt_to_equity'
    || metricKey === 'asset_turnover'
    || metricKey === 'current_ratio'
  ) {
    return `${formatGrouped(value, { maxFractionDigits: 2 })}×`
  }
  if (value < 10) return `${(value * 100).toFixed(2)}%`
  return formatGrouped(value, { maxFractionDigits: 2 })
}

export function comparisonLabel(metricKey, comp) {
  const map = HIGHER_IS_WORSE.has(metricKey) ? DEBT_COMPARISON_LABELS : COMPARISON_LABELS
  return map[comp] || comp
}

export function comparisonBadgeClass(metricKey, comp) {
  if (comp === 'insufficient_peers' || comp === 'average' || !comp) return 'badge-warning'
  const worseIsHigh = HIGHER_IS_WORSE.has(metricKey)
  if (comp === 'above_average') return worseIsHigh ? 'badge-danger' : 'badge-success'
  if (comp === 'below_average') return worseIsHigh ? 'badge-success' : 'badge-danger'
  return 'badge-warning'
}

/** Strength 0–100 for ranking (invert leverage). */
export function strengthScore(metricKey, percentile) {
  if (percentile == null) return null
  return HIGHER_IS_WORSE.has(metricKey) ? 100 - percentile : percentile
}

export function buildBenchmarkSummary(result, metricEntries) {
  if (!result || !metricEntries.length) return null
  const scored = metricEntries
    .map(([key]) => {
      const pct = result.percentiles?.[key]
      const strength = strengthScore(key, pct)
      if (strength == null) return null
      return { key, pct, strength, label: METRIC_LABELS[key] || key }
    })
    .filter(Boolean)

  if (!scored.length) {
    return {
      empty:
        'Chưa có đủ doanh nghiệp cùng ngành trong dữ liệu để xếp hạng. '
        + 'Các chỉ số của doanh nghiệp vẫn được tính từ báo cáo tài chính đã nhập.',
    }
  }

  const aboveMedian = scored.filter((s) => s.strength >= 50).length
  const weakest = scored.reduce((a, b) => (b.strength < a.strength ? b : a))
  const strongest = scored.reduce((a, b) => (b.strength > a.strength ? b : a))

  return {
    aboveMedian,
    total: scored.length,
    strongest,
    weakest,
    weakestIsLeverage: HIGHER_IS_WORSE.has(weakest.key),
  }
}

/** Plain-Vietnamese reading of a percentile. */
export function describeRank(metricKey, pct) {
  if (pct == null) return 'chưa xếp hạng được'
  if (HIGHER_IS_WORSE.has(metricKey)) {
    return `vay nợ nhiều hơn khoảng ${pct}% doanh nghiệp cùng ngành`
  }
  return `cao hơn khoảng ${pct}% doanh nghiệp cùng ngành`
}

/** Share/ratio as percent string; null → null (caller renders N/A). */
export function formatSharePct(value) {
  if (value == null || typeof value !== 'number') return null
  return `${(value * 100).toFixed(2)}%`
}

export function shareToPct(value) {
  if (value == null || typeof value !== 'number') return null
  return Math.max(0, Math.min(100, value * 100))
}

export function presentMetricEntries(result) {
  if (!result) return []
  return Object.entries(METRIC_LABELS).filter(([key]) => result[key] != null)
}

export function buildRadarData(metricEntries, result) {
  return metricEntries
    .map(([key]) => {
      const firmPct = result?.percentiles?.[key]
      if (firmPct == null) return null
      return {
        metric: METRIC_SHORT[key] || key,
        firm: strengthScore(key, firmPct),
        peerMedian: 50,
      }
    })
    .filter(Boolean)
}

export function insufficientPeersFromResult(result) {
  return (result?.warnings || []).includes('insufficient_peers')
    || result?.peer_count === 0
}
