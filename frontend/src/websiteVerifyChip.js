/**
 * Hallmark · component: chip · genre: editorial · theme: existing-dashboard
 * states: default (fail) · unknown · hidden (ok / missing)
 * contrast: pass (reuses .badge-warning / .badge-info / .metric-chip tokens)
 *
 * Map stored website_verify_status → Vietnamese honesty chip.
 * Fail = chưa verify được (SSL/fetch). Unknown = chưa đo.
 * Do not say “không có TMĐT” from fail. Do not say checkout no.
 */

const FAIL = 'fail'
const UNKNOWN = 'unknown'
const OK = 'ok'

function nestedVerify(channels) {
  if (!channels || typeof channels !== 'object') return {}
  const nested = channels.website_verify
  if (nested && typeof nested === 'object') return nested
  return {
    status: channels.website_verify_status,
    reason: channels.website_verify_reason,
  }
}

function normalizeStatus(raw) {
  if (raw == null) return null
  const status = String(raw).trim().toLowerCase()
  if (status === FAIL || status === UNKNOWN || status === OK) return status
  return null
}

/**
 * Boolean channel flags only — skip nested website_verify provenance.
 * @param {Record<string, unknown> | null | undefined} channels
 * @returns {string[]}
 */
export function digitalChannelNames(channels) {
  if (!channels || typeof channels !== 'object') return []
  return Object.entries(channels)
    .filter(([, value]) => value === true)
    .map(([key]) => key)
}

/**
 * @param {object | null | undefined} company CompanyOut / list row
 * @returns {{ status: string, label: string, title: string, badgeClass: string } | null}
 */
export function websiteVerifyChip(company) {
  if (!company) return null
  const nested = nestedVerify(company.digital_channels)
  const status =
    normalizeStatus(company.website_verify_status) || normalizeStatus(nested.status)
  const reason = company.website_verify_reason || nested.reason || ''

  if (!status || status === OK) return null

  if (status === FAIL) {
    const ssl = String(reason).toLowerCase().includes('ssl')
    return {
      status: FAIL,
      label: ssl ? 'chưa verify (SSL)' : 'chưa verify được',
      title:
        'Website chính thức chưa verify được (SSL/fetch). Không suy ra không có thương mại điện tử.',
      badgeClass: 'badge-warning',
    }
  }

  if (status === UNKNOWN) {
    return {
      status: UNKNOWN,
      label: 'chưa đo',
      title: 'Website chưa được đo. Không suy checkout hay TMĐT từ trạng thái này.',
      badgeClass: 'badge-info',
    }
  }

  return null
}
