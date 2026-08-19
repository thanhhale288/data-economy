import assert from 'node:assert/strict'
import { test } from 'node:test'
import { extractWarningCopy, extractWarningCopies } from './extractWarningCopy.js'

test('ocr_unavailable is Vietnamese, not the raw token alone', () => {
  const copy = extractWarningCopy('ocr_unavailable')
  assert.ok(copy.includes('OCR'))
  assert.ok(copy.includes('CafeF'))
  assert.ok(copy.includes('PDF chữ') || copy.includes('selectable text'))
  assert.notEqual(copy, 'ocr_unavailable')
  assert.ok(!copy.startsWith('ocr_unavailable'))
})

test('pages_capped:15 explains the first N pages', () => {
  const copy = extractWarningCopy('pages_capped:15')
  assert.ok(copy.includes('15'))
  assert.ok(copy.includes('trang'))
  assert.notEqual(copy, 'pages_capped:15')
})

test('pages_capped:N uses the token N', () => {
  assert.ok(extractWarningCopy('pages_capped:8').includes('8'))
})

test('maps other known extract tokens', () => {
  assert.ok(extractWarningCopy('no_extractable_fields').includes('BCTC'))
  assert.ok(extractWarningCopy('ocr_text_empty').includes('OCR'))
  assert.ok(extractWarningCopy('pdf_has_no_pages').includes('PDF'))
  assert.match(extractWarningCopy('ocr_failed:RuntimeError'), /RuntimeError/)
  assert.match(extractWarningCopy('ocr_low_confidence:0.12'), /0\.12/)
  assert.match(extractWarningCopy('pdf_rasterize_failed:PdfiumError'), /PdfiumError/)
  assert.ok(extractWarningCopy('missing_field:operating_revenue').includes('doanh thu'))
})

test('unknown tokens keep a generic VI sentence plus the raw token', () => {
  const token = 'some_new_backend_flag'
  const copy = extractWarningCopy(token)
  assert.ok(copy.includes(token))
  assert.notEqual(copy, token)
  assert.ok(copy.startsWith('Cảnh báo trích xuất chưa được giải thích:'))
})

test('extractWarningCopies maps every token and does not drop unknowns', () => {
  const copies = extractWarningCopies(['ocr_unavailable', 'pages_capped:15', 'weird_token'])
  assert.equal(copies.length, 3)
  assert.ok(copies[0].includes('OCR'))
  assert.ok(copies[1].includes('15'))
  assert.ok(copies[2].includes('weird_token'))
})
