/**
 * Dashboard IIP anomaly chip — hide unless the latest IIP period is actually flagged.
 * Isolation Forest payload from GET /api/ml/anomaly (do not invent alerts).
 *
 * Hallmark · component: banner · genre: editorial · theme: existing-dashboard
 * states: default (shown) · hidden (unavailable / not flagged / error)
 * contrast: pass (reuses .banner-warn / .badge-warning tokens)
 */

/** YYYY-MM from an ISO date or period string. */
export function periodKey(period) {
  if (period == null || period === '') return ''
  return String(period).slice(0, 7)
}

function lastPointByPeriod(points) {
  let latest = null
  let latestKey = ''
  for (const point of points) {
    const key = periodKey(point?.period)
    if (!key) continue
    if (!latest || key >= latestKey) {
      latest = point
      latestKey = key
    }
  }
  return latest
}

/**
 * The IIP point for the latest Dashboard period, only when it is flagged.
 *
 * @param {object | null} anomaly GET /api/ml/anomaly payload
 * @param {string | Date | null} latestPeriod Dashboard summary.latest_period
 *   (period of iip_latest), else last IIP series period, else last scored point
 * @returns {object | null} flagged point `{ period, value, score, is_anomaly }` or null
 */
export function latestIipAnomalyPoint(anomaly, latestPeriod) {
  if (!anomaly || anomaly.available !== true) return null
  const iip = anomaly.iip
  if (!iip || iip.available !== true) return null
  const points = Array.isArray(iip.points) ? iip.points : []
  if (!points.length) return null

  const preferred = periodKey(latestPeriod)
  const point = preferred
    ? points.find((p) => periodKey(p.period) === preferred) || null
    : lastPointByPeriod(points)

  if (!point || point.is_anomaly !== true) return null
  return point
}
