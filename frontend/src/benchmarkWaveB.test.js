import assert from 'node:assert/strict'
import { test } from 'node:test'
import { WARNING_LABELS } from './components/benchmark/benchmarkLabels.js'
import {
  coerceComparePayload,
  resolveFeedbackSourceType,
  snapshotFormFields,
} from './components/benchmark/formUtils.js'
import { comparisonBadgeClass, formatRatio } from './components/benchmark/resultsModel.js'

test('coerceComparePayload turns empty money strings into null, not 0', () => {
  const payload = coerceComparePayload({
    stock_code: '',
    vsic_code: '2740',
    operating_revenue: '1 000 000',
    profit_before_tax: '100 000',
    employees: '200',
    operating_expenses: '',
    cost_of_goods: '',
    remuneration: '',
    total_assets: '2 000 000',
    total_equity: '1 000 000',
    current_assets: '',
    current_liabilities: '',
  })
  assert.equal(payload.stock_code, null)
  assert.equal(payload.vsic_code, '2740')
  assert.equal(payload.operating_revenue, 1000000)
  assert.equal(payload.operating_expenses, null)
  assert.equal(payload.cost_of_goods, null)
  assert.equal(payload.total_assets, 2000000)
})

test('snapshotFormFields keeps ticker/vsic as strings and blanks as null', () => {
  const snap = snapshotFormFields({
    stock_code: 'RAL',
    vsic_code: '2740',
    operating_revenue: '',
    profit_before_tax: '1 000',
  })
  assert.equal(snap.stock_code, 'RAL')
  assert.equal(snap.vsic_code, '2740')
  assert.equal(snap.operating_revenue, null)
  assert.equal(snap.profit_before_tax, 1000)
})

test('resolveFeedbackSourceType prefers extract then CafeF then manual', () => {
  assert.equal(
    resolveFeedbackSourceType({ extractMeta: { source_type: 'pdf_text' } }),
    'pdf_text',
  )
  assert.equal(
    resolveFeedbackSourceType({ extractMeta: null, feedbackOrigin: 'cafef_prefill' }),
    'cafef_prefill',
  )
  assert.equal(
    resolveFeedbackSourceType({ extractMeta: null, feedbackOrigin: 'manual' }),
    'manual',
  )
})

test('WARNING_LABELS cover API honesty codes without inventing GSO tables', () => {
  assert.match(WARNING_LABELS.prototype_listed_sample, /~28/)
  assert.match(WARNING_LABELS.insufficient_peers, /Chưa đủ/)
  assert.ok(!/census GSO \d/.test(Object.values(WARNING_LABELS).join(' ')))
})

test('debt_to_equity above average is danger, not success', () => {
  assert.equal(comparisonBadgeClass('debt_to_equity', 'above_average'), 'badge-danger')
  assert.equal(comparisonBadgeClass('roa', 'above_average'), 'badge-success')
})

test('formatRatio leaves null as em dash (no invented percentile)', () => {
  assert.equal(formatRatio(null, 'roa'), '—')
})
