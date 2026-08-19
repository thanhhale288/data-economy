import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  INSUFFICIENT_PEERS_DEMO_VSIC,
  NA_LABEL,
  buildBreadcrumbCrumbs,
  buildIndustryContext,
  displayOrNA,
  expectedPeerScope,
  resolvePeerScope,
  vsicDivisionPrefix,
} from './benchmarkIndustryContext.js'

test('empty or short VSIC does not invent a division', () => {
  assert.equal(vsicDivisionPrefix(''), null)
  assert.equal(vsicDivisionPrefix('   '), null)
  assert.equal(vsicDivisionPrefix(null), null)
  assert.equal(vsicDivisionPrefix(undefined), null)
  assert.equal(vsicDivisionPrefix('1'), null)
  assert.equal(expectedPeerScope(''), null)
  assert.equal(expectedPeerScope('1'), null)
})

test('2-digit division is the first two characters (RAL 2740 → 27)', () => {
  assert.equal(vsicDivisionPrefix('2740'), '27')
  assert.equal(vsicDivisionPrefix('27'), '27')
  assert.equal(vsicDivisionPrefix(' 2740 '), '27')
  assert.equal(expectedPeerScope('2740'), 'vsic_division:27')
  assert.equal(expectedPeerScope('1100'), 'vsic_division:11')
})

test('breadcrumb omits division when VSIC is empty; does not invent a code', () => {
  const empty = buildBreadcrumbCrumbs('')
  assert.equal(empty.length, 1)
  assert.equal(empty[0].label, 'Benchmark')
  assert.equal(empty[0].current, true)
  assert.ok(!empty.some((c) => /VSIC/i.test(c.label)))

  const ral = buildBreadcrumbCrumbs('2740')
  assert.deepEqual(
    ral.map((c) => c.label),
    ['Benchmark', 'VSIC 27'],
  )
  assert.equal(ral[1].current, true)
})

test('industry context shows N/A when VSIC is missing — no GSO table', () => {
  const ctx = buildIndustryContext('')
  assert.equal(ctx.division, null)
  assert.equal(ctx.peerScope, null)
  assert.equal(ctx.divisionDisplay, NA_LABEL)
  assert.equal(ctx.peerScopeDisplay, NA_LABEL)
  assert.match(ctx.copy.noGsoTables, /GSO/)
  assert.match(ctx.copy.peersReminder, /không phải tổng điều tra GSO/)
  assert.ok(!/tỷ lệ ngành quốc gia \d/.test(JSON.stringify(ctx)))
})

test('prefers API peer_scope after compare; otherwise form expectation', () => {
  const fromForm = resolvePeerScope('2740', null)
  assert.deepEqual(fromForm, { value: 'vsic_division:27', sourced: 'form' })

  const fromResult = resolvePeerScope('2740', 'vsic_division:27')
  assert.deepEqual(fromResult, { value: 'vsic_division:27', sourced: 'result' })

  const empty = resolvePeerScope('', '   ')
  assert.deepEqual(empty, { value: null, sourced: null })
})

test('insufficient_peers demo VSIC stays 1100 (existing button)', () => {
  assert.equal(INSUFFICIENT_PEERS_DEMO_VSIC, '1100')
  const ctx = buildIndustryContext('1100')
  assert.equal(ctx.demoVsic, '1100')
  assert.equal(ctx.division, '11')
  assert.match(ctx.copy.insufficientDemoLink, /1100/)
  assert.match(ctx.copy.insufficientDemoPrefix, /insufficient_peers/)
})

test('displayOrNA hides missing sourced values as N/A', () => {
  assert.equal(displayOrNA(null), 'N/A')
  assert.equal(displayOrNA(''), 'N/A')
  assert.equal(displayOrNA('vsic_division:27'), 'vsic_division:27')
})
