import { extractWarningCopy } from '../../extractWarningCopy'
import { INSUFFICIENT_PEERS_DEMO_VSIC } from '../../benchmarkIndustryContext'
import { EXTRACT_LOW_CONFIDENCE } from './benchmarkLabels'

function MoneyField({
  label,
  field,
  value,
  onChange,
  onBlur,
  required,
  lowConfidence,
}) {
  return (
    <div className="form-group">
      <label>{label}</label>
      <input
        inputMode="numeric"
        value={value}
        onChange={(e) => onChange(field, e.target.value)}
        onBlur={() => onBlur(field)}
        className={lowConfidence ? 'field-low-confidence' : undefined}
        required={required}
      />
    </div>
  )
}

export default function BenchmarkForm({
  form,
  loading,
  extracting,
  extractMeta,
  requireConfirm,
  humanConfirmed,
  compareLockedByConfirm,
  prefillSource,
  isLowConfidence,
  onChange,
  onMoneyBlur,
  onSubmit,
  onUpload,
  onPrefill,
  onInsufficientDemo,
  onConfirmChange,
}) {
  const demoVsic = INSUFFICIENT_PEERS_DEMO_VSIC
  const lowConfidenceFields = Object.entries(extractMeta?.confidence || {})
    .filter(([, score]) => typeof score === 'number' && score > 0 && score < EXTRACT_LOW_CONFIDENCE)
    .map(([key]) => key)

  return (
    <>
      <div className="toolbar mb-md">
        <label
          className={`btn btn-primary${extracting ? ' is-busy' : ''}`}
          htmlFor="benchmark-upload-input"
        >
          {extracting ? 'Đang trích xuất...' : 'Upload BCTC để prefill'}
        </label>
        <input
          id="benchmark-upload-input"
          className="visually-hidden"
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.webp,.tif,.tiff,.bmp"
          disabled={extracting || loading}
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) onUpload(file)
            e.target.value = ''
          }}
        />
        <button
          type="button"
          className="btn"
          onClick={() => onPrefill('RAL')}
          disabled={loading}
        >
          Nạp RAL từ BCTC
        </button>
        <button type="button" className="btn" onClick={() => onPrefill('REE')} disabled={loading}>
          Nạp REE (cùng ngành 27)
        </button>
        <button
          type="button"
          id="insufficient-peers-demo"
          className="btn"
          onClick={onInsufficientDemo}
          disabled={loading}
          title={`Đổi VSIC sang ${demoVsic} để xem trường hợp không có DN cùng ngành`}
        >
          Xem khi không có DN cùng ngành (VSIC {demoVsic})
        </button>
      </div>

      {extractMeta && (
        <div className="banner banner-warn mb-md" role="status">
          File <strong>{extractMeta.filename}</strong> đã được trích xuất ({extractMeta.source_type}).
          {extractMeta.warnings?.length > 0 && (
            <ul className="extract-meta-detail extract-warning-list">
              {extractMeta.warnings.map((token, i) => (
                <li key={`${i}-${token}`}>{extractWarningCopy(token)}</li>
              ))}
            </ul>
          )}
          {lowConfidenceFields.length > 0 && (
            <div className="extract-meta-detail">
              Confidence thấp (&lt; {EXTRACT_LOW_CONFIDENCE}): {lowConfidenceFields.join(', ')}.
              Hãy kiểm tra kỹ trước khi compare.
            </div>
          )}
        </div>
      )}

      {!prefillSource && !form.operating_revenue && !extractMeta && (
        <div className="banner banner-warn mb-md" role="status">
          Form trống — upload BCTC, bấm «Nạp RAL từ BCTC», hoặc nhập tay các chỉ tiêu.
        </div>
      )}

      <form onSubmit={onSubmit} className="chart-container">
        <div className="form-grid">
          <div className="form-group">
            <label>Mã VSIC</label>
            <input value={form.vsic_code} onChange={(e) => onChange('vsic_code', e.target.value)} required />
          </div>
          <MoneyField
            label="Doanh thu hoạt động (VND)"
            field="operating_revenue"
            value={form.operating_revenue}
            onChange={onChange}
            onBlur={onMoneyBlur}
            required
            lowConfidence={isLowConfidence('operating_revenue')}
          />
          <MoneyField
            label="Lợi nhuận trước thuế (VND)"
            field="profit_before_tax"
            value={form.profit_before_tax}
            onChange={onChange}
            onBlur={onMoneyBlur}
            required
            lowConfidence={isLowConfidence('profit_before_tax')}
          />
          <MoneyField
            label="Số lao động"
            field="employees"
            value={form.employees}
            onChange={onChange}
            onBlur={onMoneyBlur}
            required
            lowConfidence={isLowConfidence('employees')}
          />
        </div>

        <div className="singstat-form-block">
          <MoneyField
            label="Chi phí hoạt động (VND)"
            field="operating_expenses"
            value={form.operating_expenses}
            onChange={onChange}
            onBlur={onMoneyBlur}
          />
          <p className="singstat-of-which">Trong đó</p>
          <div className="form-grid singstat-of-which-grid">
            <MoneyField
              label="Giá vốn hàng bán & NVL (VND)"
              field="cost_of_goods"
              value={form.cost_of_goods}
              onChange={onChange}
              onBlur={onMoneyBlur}
            />
            <MoneyField
              label="Chi phí nhân công (thuyết minh) (VND)"
              field="remuneration"
              value={form.remuneration}
              onChange={onChange}
              onBlur={onMoneyBlur}
            />
          </div>
        </div>

        <div className="form-grid mt-sm">
          <MoneyField
            label="Tổng tài sản (VND)"
            field="total_assets"
            value={form.total_assets}
            onChange={onChange}
            onBlur={onMoneyBlur}
            lowConfidence={isLowConfidence('total_assets')}
          />
          <MoneyField
            label="Vốn chủ sở hữu (VND)"
            field="total_equity"
            value={form.total_equity}
            onChange={onChange}
            onBlur={onMoneyBlur}
            lowConfidence={isLowConfidence('total_equity')}
          />
          <MoneyField
            label="Tài sản ngắn hạn (VND)"
            field="current_assets"
            value={form.current_assets}
            onChange={onChange}
            onBlur={onMoneyBlur}
          />
          <MoneyField
            label="Nợ ngắn hạn (VND)"
            field="current_liabilities"
            value={form.current_liabilities}
            onChange={onChange}
            onBlur={onMoneyBlur}
          />
        </div>
        {requireConfirm && (
          <label className="confirm-check">
            <input
              type="checkbox"
              checked={humanConfirmed}
              onChange={(e) => onConfirmChange(e.target.checked)}
            />
            <span>
              {extractMeta
                ? 'Tôi đã kiểm tra/chỉnh sửa dữ liệu prefill từ file trước khi so sánh'
                : 'Tôi đã kiểm tra/chỉnh sửa dữ liệu nạp từ CafeF trước khi so sánh'}
            </span>
          </label>
        )}
        {compareLockedByConfirm && (
          <div className="banner banner-warn mt-sm" role="status">
            {extractMeta
              ? 'Cần xác nhận dữ liệu prefill từ file trước khi bấm compare.'
              : 'Cần xác nhận dữ liệu nạp từ CafeF trước khi bấm compare.'}
          </div>
        )}
        <button type="submit" className="btn btn-primary mt-md" disabled={loading || compareLockedByConfirm}>
          {loading ? 'Đang so sánh...' : 'So sánh benchmark'}
        </button>
      </form>
    </>
  )
}
