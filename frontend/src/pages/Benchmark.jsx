import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { INSUFFICIENT_PEERS_DEMO_VSIC } from '../benchmarkIndustryContext'
import BenchmarkForm from '../components/benchmark/BenchmarkForm'
import BenchmarkHeader from '../components/benchmark/BenchmarkHeader'
import BenchmarkResults from '../components/benchmark/BenchmarkResults'
import BenchmarkWarnings from '../components/benchmark/BenchmarkWarnings'
import { EXTRACT_LOW_CONFIDENCE } from '../components/benchmark/benchmarkLabels'
import {
  EMPTY_FORM,
  coerceComparePayload,
  formFromExtract,
  formFromPrefill,
  lowConfidenceFields,
  resolveFeedbackSourceType,
  roundMoneyField,
  snapshotFormFields,
} from '../components/benchmark/formUtils'

export default function Benchmark() {
  const [searchParams] = useSearchParams()
  const vsicFromUrl = searchParams.get('vsic') || ''
  const [form, setForm] = useState({
    ...EMPTY_FORM,
    vsic_code: vsicFromUrl || '',
  })
  const [prefillSource, setPrefillSource] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const [extractMeta, setExtractMeta] = useState(null)
  const [requireConfirm, setRequireConfirm] = useState(false)
  const [humanConfirmed, setHumanConfirmed] = useState(false)
  const [prefillSnapshot, setPrefillSnapshot] = useState(null)
  const [narrative, setNarrative] = useState(null)
  const [narrativeLoading, setNarrativeLoading] = useState(false)
  const [narrativeError, setNarrativeError] = useState(null)
  const [feedbackOrigin, setFeedbackOrigin] = useState(null)
  const feedbackPostedRef = useRef(false)

  useEffect(() => {
    if (vsicFromUrl) {
      setForm((prev) => ({ ...prev, vsic_code: vsicFromUrl }))
    }
  }, [vsicFromUrl])

  const handleChange = (field, value) => {
    const originIsPrefillOrExtract = (
      Boolean(extractMeta)
      || feedbackOrigin === 'cafef_prefill'
      || feedbackOrigin === 'docai_extract'
    )
    if (!originIsPrefillOrExtract && !prefillSnapshot) {
      setPrefillSnapshot(snapshotFormFields(form))
      setFeedbackOrigin('manual')
    }
    setForm((prev) => ({ ...prev, [field]: value }))
    setPrefillSource(null)
    if (requireConfirm) setHumanConfirmed(false)
    feedbackPostedRef.current = false
  }

  const handleMoneyBlur = (field) => {
    setForm((prev) => {
      const next = roundMoneyField(prev[field])
      if (next === prev[field]) return prev
      return { ...prev, [field]: next }
    })
  }

  const loadNarrative = async (compareResult) => {
    if (!compareResult) {
      setNarrative(null)
      setNarrativeError(null)
      return
    }
    setNarrativeLoading(true)
    setNarrativeError(null)
    try {
      const payload = await api.benchmarkNarrative(compareResult)
      setNarrative(payload)
    } catch (err) {
      console.error(err)
      setNarrative(null)
      setNarrativeError(err.message || 'Không tạo được giải thích benchmark.')
    } finally {
      setNarrativeLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    postFeedbackSignal()
    setLoading(true)
    setError(null)
    try {
      const res = await api.benchmark(coerceComparePayload(form))
      setResult(res)
      await loadNarrative(res)
    } catch (err) {
      console.error(err)
      setResult(null)
      setNarrative(null)
      setError(err.message || 'Không so sánh được benchmark.')
    } finally {
      setLoading(false)
    }
  }

  const handleUploadExtract = async (file) => {
    if (!file) return
    setExtracting(true)
    setError(null)
    setResult(null)
    setNarrative(null)
    setNarrativeError(null)
    setPrefillSource(null)
    try {
      const extracted = await api.benchmarkExtract(file)
      setForm((prev) => formFromExtract(extracted.fields, prev))
      setPrefillSnapshot(snapshotFormFields(extracted.fields || {}))
      setExtractMeta({
        confidence: extracted.confidence || {},
        warnings: extracted.warnings || [],
        source_type: extracted.source_type || 'unknown',
        filename: file.name,
      })
      setFeedbackOrigin('docai_extract')
      feedbackPostedRef.current = false
      setRequireConfirm(true)
      setHumanConfirmed(false)
    } catch (err) {
      console.error(err)
      setExtractMeta(null)
      setPrefillSnapshot(null)
      setFeedbackOrigin(null)
      feedbackPostedRef.current = false
      setRequireConfirm(false)
      setHumanConfirmed(false)
      setError(err.message || 'Không trích xuất được BCTC.')
    } finally {
      setExtracting(false)
    }
  }

  const loadPrefill = async (stockCode) => {
    setLoading(true)
    setError(null)
    setResult(null)
    setNarrative(null)
    setNarrativeError(null)
    setExtractMeta(null)
    setRequireConfirm(false)
    setHumanConfirmed(false)
    setFeedbackOrigin('cafef_prefill')
    feedbackPostedRef.current = false
    try {
      const data = await api.benchmarkPrefill(stockCode)
      const next = formFromPrefill(data)
      setForm(next)
      setPrefillSnapshot(snapshotFormFields(next))
      setPrefillSource(data.stock_code || stockCode)
      setRequireConfirm(true)
    } catch (err) {
      console.error(err)
      setPrefillSource(null)
      setPrefillSnapshot(null)
      setFeedbackOrigin(null)
      setRequireConfirm(false)
      setError(
        err.message?.includes('404')
          ? `Không tìm thấy BCTC đủ trường để nạp «${stockCode}».`
          : (err.message || `Không nạp được ${stockCode}.`)
      )
    } finally {
      setLoading(false)
    }
  }

  const postFeedbackSignal = (sourceType) => {
    if (feedbackPostedRef.current) return
    if (!prefillSnapshot) return
    feedbackPostedRef.current = true
    const after = snapshotFormFields(form)
    const resolved = sourceType || resolveFeedbackSourceType({
      extractMeta,
      feedbackOrigin,
      prefillSource,
    })
    api.benchmarkFeedback({
      before: prefillSnapshot,
      after,
      ticker: form.stock_code || prefillSource || null,
      source_type: resolved,
    }).catch((err) => {
      console.warn('feedback signal failed', err)
    })
  }

  const handleConfirmChange = (checked) => {
    setHumanConfirmed(checked)
    if (checked) {
      postFeedbackSignal()
    }
  }

  const setInsufficientPeerDemo = () => {
    setForm((prev) => ({
      ...prev,
      vsic_code: INSUFFICIENT_PEERS_DEMO_VSIC,
    }))
    setPrefillSource(null)
    setResult(null)
    setNarrative(null)
    setNarrativeError(null)
    setError(null)
    setExtractMeta(null)
    setRequireConfirm(false)
    setHumanConfirmed(false)
    setPrefillSnapshot(null)
    setFeedbackOrigin(null)
    feedbackPostedRef.current = false
  }

  const lowFields = lowConfidenceFields(extractMeta?.confidence, EXTRACT_LOW_CONFIDENCE)
  const isLowConfidence = (field) => lowFields.includes(field)
  const compareLockedByConfirm = requireConfirm && !humanConfirmed

  return (
    <div className="benchmark-page">
      <BenchmarkHeader
        vsicCode={form.vsic_code}
        peerScopeFromResult={result?.peer_scope}
      />
      <BenchmarkForm
        form={form}
        loading={loading}
        extracting={extracting}
        extractMeta={extractMeta}
        requireConfirm={requireConfirm}
        humanConfirmed={humanConfirmed}
        compareLockedByConfirm={compareLockedByConfirm}
        prefillSource={prefillSource}
        isLowConfidence={isLowConfidence}
        onChange={handleChange}
        onMoneyBlur={handleMoneyBlur}
        onSubmit={handleSubmit}
        onUpload={handleUploadExtract}
        onPrefill={loadPrefill}
        onInsufficientDemo={setInsufficientPeerDemo}
        onConfirmChange={handleConfirmChange}
      />
      {error && (
        <div className="banner banner-warn mt-md" role="alert">
          {error}
        </div>
      )}
      {result && (
        <div className="mt-lg">
          <BenchmarkWarnings warnings={result.warnings || []} />
          <BenchmarkResults
            result={result}
            narrative={narrative}
            narrativeLoading={narrativeLoading}
            narrativeError={narrativeError}
          />
        </div>
      )}
    </div>
  )
}
