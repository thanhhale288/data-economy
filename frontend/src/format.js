/**
 * Display helpers — space-grouped digits + money formatters.
 *
 * Money rules (product):
 * - Always show currency: `$100` or `1 000 000 VND`
 * - USD: round to whole units; VND: round to nearest thousand
 * - Large magnitudes use M / B (million / billion)
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

/**
 * Round money for display: USD → units; VND → nearest thousand.
 * Returns { sign, abs } after rounding, or null if non-finite.
 */
function roundMoneyParts(n, currency) {
  const parts = splitSignAndAbs(n)
  if (!parts) return null
  const { sign, abs } = parts
  if (currency === 'USD') {
    return { sign, abs: Math.round(abs) }
  }
  // VND: nearest thousand
  const rounded = Math.round(abs / 1000) * 1000
  return { sign, abs: rounded }
}

/**
 * Format money with currency mark always present.
 * @param {number} n
 * @param {'VND'|'USD'} [currency='VND']
 * @param {{ compact?: boolean }} [opts] — compact defaults true (M/B when ≥1e6)
 */
export function formatMoney(n, currency = 'VND', { compact = true } = {}) {
  if (n == null || n === '') return '—'
  const cur = currency === 'USD' ? 'USD' : 'VND'
  const parts = roundMoneyParts(n, cur)
  if (!parts) return '—'

  const { sign, abs } = parts

  if (abs === 0) {
    return cur === 'USD' ? `${sign}$0` : `${sign}0 VND`
  }

  // USD: M from 1e6, B from 1e9.
  // VND: keep full space-grouped form through millions (e.g. "1 000 000 VND");
  // compact with M from 1e9 and B from 1e12 so everyday triệu amounts stay readable.
  if (compact) {
    if (cur === 'USD') {
      if (abs >= 1e9) {
        const coef = formatGrouped(abs / 1e9, { maxFractionDigits: 1 })
        return `${sign}$${coef}B`
      }
      if (abs >= 1e6) {
        const coef = formatGrouped(abs / 1e6, { maxFractionDigits: 1 })
        return `${sign}$${coef}M`
      }
    } else {
      if (abs >= 1e12) {
        const coef = formatGrouped(abs / 1e12, { maxFractionDigits: 1 })
        return `${sign}${coef}T VND`
      }
      if (abs >= 1e9) {
        const coef = formatGrouped(abs / 1e9, { maxFractionDigits: 1 })
        return `${sign}${coef}B VND`
      }
    }
  }

  const grouped = groupDigits(String(Math.trunc(abs)))
  return cur === 'USD' ? `${sign}$${grouped}` : `${sign}${grouped} VND`
}

/**
 * Compact money for charts/KPIs — always VND with M/B (legacy name).
 * Prefer `formatMoney(n, 'VND')` in new code.
 */
export function formatCompactVnd(n) {
  return formatMoney(n, 'VND')
}

/**
 * Compact money — VND with M/B (Dashboard Digital VA & heatmap).
 * Prefer `formatMoney(n, 'VND')` in new code.
 */
export function formatCompact(n) {
  return formatMoney(n, 'VND')
}

/**
 * Format GSO manufacturing VA (`VA_C` / `VA_C_NOMINAL`).
 * Values in gso_macro are already **billion VND** (UNIT_MULT=9) — label as tỷ VND.
 * Do not reuse company Digital VA money formatters without this unit.
 */
export function formatMacroVa(n, { maxFractionDigits = 0 } = {}) {
  if (n == null || n === '') return '—'
  const parts = splitSignAndAbs(n)
  if (!parts) return '—'
  const grouped = formatGrouped(parts.abs, { maxFractionDigits })
  return `${parts.sign}${grouped} tỷ VND`
}
