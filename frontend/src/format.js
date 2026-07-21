/**
 * Display helpers — space-grouped digits when the absolute integer has ≥5 digits.
 * Example: 1234 → "1234", 12345 → "12 345", 5.2e12 → "5 200 000 000 000".
 */

function splitSignAndAbs(n) {
  const num = Number(n)
  if (!Number.isFinite(num)) return null
  const sign = num < 0 ? '-' : ''
  return { sign, abs: Math.abs(num) }
}

/** Group an integer digit string with spaces (only when length ≥ 5). */
export function groupDigits(intStr) {
  const raw = String(intStr).replace(/^0+(?=\d)/, '') || '0'
  if (raw.length < 5) return raw
  return raw.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

/**
 * Format a finite number with space thousands separators on the integer part.
 * Keeps a short decimal part when present (no grouping on fraction).
 */
export function formatGrouped(n, { maxFractionDigits = 6 } = {}) {
  const parts = splitSignAndAbs(n)
  if (!parts) return '—'

  // Avoid scientific notation for large magnitudes
  let fixed = parts.abs.toFixed(maxFractionDigits)
  if (fixed.includes('e') || fixed.includes('E')) {
    fixed = parts.abs.toLocaleString('en-US', {
      useGrouping: false,
      maximumFractionDigits: maxFractionDigits,
    })
  }
  // Trim trailing zeros after decimal
  if (fixed.includes('.')) {
    fixed = fixed.replace(/\.?0+$/, '')
  }
  const [intPart, frac] = fixed.split('.')
  const grouped = groupDigits(intPart)
  return frac != null && frac.length > 0
    ? `${parts.sign}${grouped}.${frac}`
    : `${parts.sign}${grouped}`
}

/** Parse user/API strings that may contain spaces or commas. */
export function parseGrouped(value) {
  if (value == null || value === '') return null
  if (typeof value === 'number') return Number.isFinite(value) ? value : null
  const cleaned = String(value).replace(/[\s,]/g, '').trim()
  if (!cleaned) return null
  const n = Number(cleaned)
  return Number.isFinite(n) ? n : null
}

/** Compact VND-scale labels; coefficients still use space grouping when ≥5 digits. */
export function formatCompactVnd(n) {
  const parts = splitSignAndAbs(n)
  if (!parts) return '—'
  const { sign, abs } = parts
  if (abs >= 1e12) return `${sign}${formatGrouped(abs / 1e12, { maxFractionDigits: 2 })} nghìn tỷ`
  if (abs >= 1e9) return `${sign}${formatGrouped(abs / 1e9, { maxFractionDigits: 1 })} tỷ`
  if (abs >= 1e6) return `${sign}${formatGrouped(abs / 1e6, { maxFractionDigits: 1 })} triệu`
  return formatGrouped(abs)
}

/** Dashboard-style compact (T/B/M); full space group below 1e6. */
export function formatCompact(n) {
  const parts = splitSignAndAbs(n)
  if (!parts) return '—'
  const { sign, abs } = parts
  if (abs >= 1e12) return `${sign}${formatGrouped(abs / 1e12, { maxFractionDigits: 1 })}T`
  if (abs >= 1e9) return `${sign}${formatGrouped(abs / 1e9, { maxFractionDigits: 1 })}B`
  if (abs >= 1e6) return `${sign}${formatGrouped(abs / 1e6, { maxFractionDigits: 1 })}M`
  return `${sign}${formatGrouped(abs)}`
}
