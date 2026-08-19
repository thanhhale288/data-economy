import { formatGrouped, parseGrouped } from '../../format.js'

export const MONEY_FIELDS = [
  'operating_revenue',
  'profit_before_tax',
  'operating_expenses',
  'cost_of_goods',
  'remuneration',
  'total_assets',
  'total_equity',
  'current_assets',
  'current_liabilities',
]

export const EMPTY_FORM = {
  stock_code: '',
  vsic_code: '',
  operating_revenue: '',
  profit_before_tax: '',
  employees: '',
  operating_expenses: '',
  cost_of_goods: '',
  remuneration: '',
  total_assets: '',
  total_equity: '',
  current_assets: '',
  current_liabilities: '',
}

export function displayNum(value, { money = false } = {}) {
  if (value == null || value === '') return ''
  const n = typeof value === 'number' ? value : parseGrouped(value)
  if (n == null) return String(value)
  if (money) {
    // Form inputs: show rounded grouped digits without suffix (label already has VND).
    const rounded = Math.round(n / 1000) * 1000
    return formatGrouped(rounded, { maxFractionDigits: 0 })
  }
  return formatGrouped(n, { maxFractionDigits: 0 })
}

export function formFromPrefill(data) {
  const money = (v) => displayNum(v, { money: true })
  return {
    stock_code: data.stock_code ?? '',
    vsic_code: data.vsic_code ?? '',
    operating_revenue: money(data.operating_revenue),
    profit_before_tax: money(data.profit_before_tax),
    employees: displayNum(data.employees),
    operating_expenses: money(data.operating_expenses),
    cost_of_goods: money(data.cost_of_goods),
    remuneration: money(data.remuneration),
    total_assets: money(data.total_assets),
    total_equity: money(data.total_equity),
    current_assets: money(data.current_assets),
    current_liabilities: money(data.current_liabilities),
  }
}

export function formFromExtract(fields, prevForm) {
  const money = (v) => displayNum(v, { money: true })
  return {
    ...prevForm,
    operating_revenue: money(fields?.operating_revenue),
    profit_before_tax: money(fields?.profit_before_tax),
    employees: displayNum(fields?.employees),
    total_assets: money(fields?.total_assets),
    total_equity: money(fields?.total_equity),
  }
}

/** Snapshot of allowlisted numeric/string fields for Task #64 feedback diffs. */
export function snapshotFormFields(formLike) {
  const keys = [
    'stock_code',
    'vsic_code',
    'operating_revenue',
    'profit_before_tax',
    'employees',
    'operating_expenses',
    'cost_of_goods',
    'remuneration',
    'total_assets',
    'total_equity',
    'current_assets',
    'current_liabilities',
  ]
  const out = {}
  for (const key of keys) {
    const raw = formLike?.[key]
    if (raw === '' || raw == null) {
      out[key] = null
      continue
    }
    if (key === 'stock_code' || key === 'vsic_code') {
      out[key] = String(raw)
      continue
    }
    const n = typeof raw === 'number' ? raw : parseGrouped(raw)
    out[key] = n == null ? String(raw) : n
  }
  return out
}

/** Task #78 — classify confirm source without using cleared prefillSource after edits. */
export function resolveFeedbackSourceType({ extractMeta, feedbackOrigin, prefillSource }) {
  if (extractMeta) return extractMeta.source_type || 'docai_extract'
  if (feedbackOrigin === 'cafef_prefill' || prefillSource) return 'cafef_prefill'
  return 'manual'
}

/** Coerce grouped form strings to the POST /api/benchmark/compare payload. */
export function coerceComparePayload(form) {
  const payload = { ...form }
  for (const key of MONEY_FIELDS) {
    if (payload[key] === '' || payload[key] == null) payload[key] = null
    else payload[key] = parseGrouped(payload[key])
  }
  payload.operating_revenue = parseGrouped(payload.operating_revenue)
  payload.profit_before_tax = parseGrouped(payload.profit_before_tax)
  payload.employees = parseGrouped(payload.employees)
  payload.stock_code = payload.stock_code || null
  return payload
}

export function roundMoneyField(value) {
  const n = parseGrouped(value)
  if (n == null) return value
  const rounded = Math.round(n / 1000) * 1000
  return formatGrouped(rounded, { maxFractionDigits: 0 })
}

export function lowConfidenceFields(confidence, threshold) {
  return Object.entries(confidence || {})
    .filter(([, score]) => typeof score === 'number' && score > 0 && score < threshold)
    .map(([key]) => key)
}
