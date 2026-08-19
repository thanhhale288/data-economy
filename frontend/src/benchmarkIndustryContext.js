/**
 * Benchmark Wave A — breadcrumb + industry context builders.
 * Peer set = seeded listed BCTC (VSIC 2-digit division), not GSO census.
 * Missing VSIC → null / N/A. Do not invent industry codes or ratio tables.
 */

/** Same listed-sample size already used in WARNING_LABELS / SampleHonestyBanner. */
export const LISTED_PEER_SAMPLE_HINT = '~28'

/** Existing FE demo: VSIC 1100 has no seeded peers → insufficient_peers. */
export const INSUFFICIENT_PEERS_DEMO_VSIC = '1100'

export const NA_LABEL = 'N/A'

export const INDUSTRY_CONTEXT_COPY = {
  title: 'Ngành đối chiếu',
  peersReminder:
    `Peer là doanh nghiệp niêm yết đã seed, có BCTC trong nền tảng (mẫu ${LISTED_PEER_SAMPLE_HINT} DN) — không phải tổng điều tra GSO / census ngành VSIC.`,
  noGsoTables:
    'Trang này không có bảng tỷ lệ ngành GSO. Thiếu mã VSIC hoặc số nguồn thì hiện N/A — không bịa.',
  insufficientDemoPrefix: 'Xem trường hợp chưa đủ peer (insufficient_peers):',
  insufficientDemoLink: `VSIC ${INSUFFICIENT_PEERS_DEMO_VSIC}`,
}

/**
 * First 2 characters of a VSIC code — same idea as backend `vsic_division_prefix`.
 * Empty or shorter than 2 → null (do not invent a division).
 *
 * @param {unknown} vsicCode
 * @returns {string | null}
 */
export function vsicDivisionPrefix(vsicCode) {
  if (vsicCode == null) return null
  const raw = String(vsicCode).trim()
  if (raw.length < 2) return null
  return raw.slice(0, 2)
}

/**
 * @param {unknown} vsicCode
 * @returns {string | null} `vsic_division:{prefix}` or null
 */
export function expectedPeerScope(vsicCode) {
  const prefix = vsicDivisionPrefix(vsicCode)
  return prefix ? `vsic_division:${prefix}` : null
}

/**
 * Prefer API `peer_scope` after compare; else the form/prefill expectation.
 *
 * @param {unknown} vsicCode
 * @param {unknown} [peerScopeFromResult]
 * @returns {{ value: string | null, sourced: 'result' | 'form' | null }}
 */
export function resolvePeerScope(vsicCode, peerScopeFromResult) {
  if (typeof peerScopeFromResult === 'string') {
    const trimmed = peerScopeFromResult.trim()
    if (trimmed) return { value: trimmed, sourced: 'result' }
  }
  const expected = expectedPeerScope(vsicCode)
  if (expected) return { value: expected, sourced: 'form' }
  return { value: null, sourced: null }
}

/**
 * Path cue: Benchmark → VSIC {2-digit}. Omit the division crumb when VSIC is empty.
 *
 * @param {unknown} vsicCode
 * @returns {{ id: string, label: string, current: boolean }[]}
 */
export function buildBreadcrumbCrumbs(vsicCode) {
  const division = vsicDivisionPrefix(vsicCode)
  const crumbs = [{ id: 'benchmark', label: 'Benchmark', current: !division }]
  if (division) {
    crumbs.push({ id: 'vsic', label: `VSIC ${division}`, current: true })
  }
  return crumbs
}

/**
 * @param {unknown} value
 * @returns {string}
 */
export function displayOrNA(value) {
  if (value == null || value === '') return NA_LABEL
  return String(value)
}

/**
 * Structured industry-context fields for the block above the form.
 *
 * @param {unknown} vsicCode form / URL / prefill VSIC
 * @param {{ peerScopeFromResult?: unknown }} [opts]
 */
export function buildIndustryContext(vsicCode, opts = {}) {
  const division = vsicDivisionPrefix(vsicCode)
  const scope = resolvePeerScope(vsicCode, opts.peerScopeFromResult)
  return {
    title: INDUSTRY_CONTEXT_COPY.title,
    division,
    divisionDisplay: displayOrNA(division),
    peerScope: scope.value,
    peerScopeDisplay: displayOrNA(scope.value),
    peerScopeSourced: scope.sourced,
    listedSampleHint: LISTED_PEER_SAMPLE_HINT,
    demoVsic: INSUFFICIENT_PEERS_DEMO_VSIC,
    copy: INDUSTRY_CONTEXT_COPY,
  }
}
