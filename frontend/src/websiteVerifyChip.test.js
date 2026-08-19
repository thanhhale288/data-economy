import assert from 'node:assert/strict'
import { test } from 'node:test'
import { digitalChannelNames, websiteVerifyChip } from './websiteVerifyChip.js'

test('GEE fail provenance shows SSL fail chip, not no-ecommerce', () => {
  const chip = websiteVerifyChip({
    stock_code: 'GEE',
    website_url: 'https://gelex-electric.com',
    website_verify_status: 'fail',
    website_verify_reason: 'ssl_unverified',
    has_ecommerce_site: false,
  })
  assert.ok(chip)
  assert.equal(chip.status, 'fail')
  assert.equal(chip.badgeClass, 'badge-warning')
  assert.match(chip.label, /chưa verify/i)
  assert.match(chip.label, /SSL/i)
  assert.match(chip.title, /SSL|fetch/i)
  assert.ok(!/không có TMĐT/i.test(chip.label))
  assert.ok(!/không có thương mại điện tử$/i.test(chip.label))
  assert.ok(!/checkout/i.test(chip.label))
})

test('unknown status is chưa đo, not fail', () => {
  const chip = websiteVerifyChip({ website_verify_status: 'unknown' })
  assert.ok(chip)
  assert.equal(chip.status, 'unknown')
  assert.match(chip.label, /chưa đo/i)
  assert.equal(chip.badgeClass, 'badge-info')
})

test('OK ticker with a website is not tagged fail', () => {
  assert.equal(
    websiteVerifyChip({
      stock_code: 'RAL',
      website_url: 'https://rangdong.com.vn',
      website_verify_status: 'ok',
    }),
    null,
  )
  assert.equal(
    websiteVerifyChip({
      stock_code: 'RAL',
      website_url: 'https://rangdong.com.vn',
    }),
    null,
  )
})

test('nested digital_channels.website_verify is enough without API field', () => {
  const chip = websiteVerifyChip({
    digital_channels: {
      website: true,
      website_verify: { status: 'fail', reason: 'ssl_unverified' },
    },
  })
  assert.equal(chip.status, 'fail')
})

test('digitalChannelNames skips website_verify provenance objects', () => {
  const names = digitalChannelNames({
    website: true,
    shopee: false,
    tiktok: false,
    website_verify: { status: 'fail', reason: 'ssl_unverified' },
  })
  assert.deepEqual(names, ['website'])
})
