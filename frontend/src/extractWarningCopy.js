/** Map POST /api/benchmark/extract warning tokens → Vietnamese honesty copy. */

const FIELD_LABELS = {
  operating_revenue: 'doanh thu hoạt động',
  profit_before_tax: 'lợi nhuận trước thuế',
  employees: 'số lao động',
  total_assets: 'tổng tài sản',
  total_equity: 'vốn chủ sở hữu',
  current_assets: 'tài sản ngắn hạn',
  current_liabilities: 'nợ ngắn hạn',
  operating_expenses: 'chi phí hoạt động',
  cost_of_goods: 'giá vốn hàng bán',
  remuneration: 'chi phí nhân công',
}

const EXACT = {
  ocr_unavailable:
    'Máy chủ chưa có OCR. Dùng nạp CafeF (prefill) hoặc PDF chữ chọn được (selectable text) — bản scan sẽ để form trống.',
  no_extractable_fields:
    'Không đọc được chỉ tiêu BCTC từ file. Form để trống — nhập tay hoặc nạp CafeF; không điền 0.',
  ocr_text_empty:
    'OCR không đọc được chữ trên file. Thử PDF chữ hoặc nạp CafeF.',
  pdf_has_no_pages: 'PDF không có trang để đọc.',
  pdf_text_empty:
    'PDF không có lớp chữ (có thể là bản scan). Form để trống nếu OCR cũng không đọc được.',
  pdf_text_sparse:
    'PDF ít chữ; hệ thống có thể đã chuyển sang OCR. Kiểm tra lại số trước khi so sánh.',
  unit_detected_million_vnd:
    'Đã nhận đơn vị triệu đồng và quy đổi sang VND đầy đủ — hãy kiểm tra lại số.',
  unit_detected_thousand_vnd:
    'Đã nhận đơn vị nghìn đồng và quy đổi sang VND đầy đủ — hãy kiểm tra lại số.',
}

function fieldLabel(key) {
  return FIELD_LABELS[key] || key
}

function unknownCopy(token) {
  return `Cảnh báo trích xuất chưa được giải thích: ${token}`
}

/**
 * @param {unknown} token
 * @returns {string}
 */
export function extractWarningCopy(token) {
  if (token == null || typeof token !== 'string') {
    return unknownCopy(String(token))
  }
  const t = token.trim()
  if (!t) return unknownCopy(token)
  if (EXACT[t]) return EXACT[t]

  if (t.startsWith('pages_capped:')) {
    const n = t.slice('pages_capped:'.length)
    if (/^\d+$/.test(n)) {
      return `Chỉ đọc ${n} trang đầu của file; các trang sau không được trích.`
    }
  }

  if (t.startsWith('ocr_failed:')) {
    const reason = t.slice('ocr_failed:'.length) || 'không rõ'
    return `OCR lỗi (${reason}). Không bịa số — form giữ trống.`
  }

  if (t.startsWith('ocr_low_confidence:')) {
    const score = t.slice('ocr_low_confidence:'.length)
    return `OCR kém tin cậy (${score}). Các chỉ tiêu để trống, không điền 0.`
  }

  if (t.startsWith('pdf_rasterize_failed:')) {
    const reason = t.slice('pdf_rasterize_failed:'.length) || 'không rõ'
    return `Không chuyển PDF thành ảnh để OCR (${reason}). Form giữ trống.`
  }

  if (t.startsWith('missing_field:')) {
    const key = t.slice('missing_field:'.length)
    return `Thiếu ${fieldLabel(key)} trên file — để trống, không điền 0.`
  }

  if (t.startsWith('label_without_amount:')) {
    const key = t.slice('label_without_amount:'.length)
    return `Thấy nhãn ${fieldLabel(key)} nhưng không đọc được số — để trống.`
  }

  if (t.startsWith('ambiguous_field:')) {
    const key = t.slice('ambiguous_field:'.length)
    return `Có nhiều số khác nhau cho ${fieldLabel(key)} — để trống, không chọn hộ.`
  }

  if (t.startsWith('low_confidence_field:')) {
    const rest = t.slice('low_confidence_field:'.length)
    const key = rest.split(':')[0]
    return `Độ tin cậy thấp cho ${fieldLabel(key)} — để trống, hãy nhập tay.`
  }

  if (t.startsWith('employees_unparseable:')) {
    return 'Không đọc được số lao động từ dòng đã nhận diện — để trống, không điền 0.'
  }

  return unknownCopy(t)
}

/**
 * @param {unknown} tokens
 * @returns {string[]}
 */
export function extractWarningCopies(tokens) {
  if (!Array.isArray(tokens) || tokens.length === 0) return []
  return tokens.map((token) => extractWarningCopy(token))
}
