import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts'
import { formatIndex } from '../../format'
import MetricInfoTip from '../../MetricInfoTip'
import {
  COMPARISON_LABELS,
  DIGITAL_INFO,
  DIGITAL_LABELS,
  KEY_EXPENDITURE_ROWS,
  METRIC_INFO,
} from './benchmarkLabels'
import {
  buildBenchmarkSummary,
  buildRadarData,
  comparisonBadgeClass,
  comparisonLabel,
  describeRank,
  formatRatio,
  formatSharePct,
  insufficientPeersFromResult,
  presentMetricEntries,
  shareToPct,
} from './resultsModel'

function scrollToId(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function BenchmarkMetricTip({ metricKey, source = METRIC_INFO }) {
  const info = source[metricKey]
  if (!info) return null
  return (
    <MetricInfoTip
      title={info.title}
      blurb={info.blurb}
      numerator={info.numerator}
      denominator={info.denominator}
      ariaLabel={`Công thức ${info.title}`}
    />
  )
}

/** Peer band P25–P75 with median + firm marker (percentile axis 0–100). */
function QuartileBand({ quartiles, firmValue, formatValue }) {
  if (!quartiles || firmValue == null) return null
  const { p25, p50, p75 } = quartiles
  if (p25 == null || p50 == null || p75 == null) return null

  const lo = Math.min(p25, firmValue)
  const hi = Math.max(p75, firmValue)
  const span = hi - lo || 1
  const pct = (v) => 8 + ((v - lo) / span) * 84
  const bandLeft = pct(p25)
  const bandWidth = Math.max(pct(p75) - bandLeft, 2)
  const medLeft = pct(p50)
  const firmLeft = pct(firmValue)
  const pinLeft = Math.min(Math.max(firmLeft, 16), 84)

  return (
    <div className="quartile-band">
      <div className="quartile-pin-row">
        <span className="quartile-pin" style={{ left: `${pinLeft}%` }}>
          Bạn: {formatValue(firmValue)}
        </span>
        <span className="quartile-pin-caret" style={{ left: `${firmLeft}%` }} />
      </div>
      <div className="quartile-track">
        <div
          className="quartile-range"
          style={{ left: `${bandLeft}%`, width: `${bandWidth}%` }}
        />
        <div className="quartile-median" style={{ left: `${medLeft}%` }} />
        <div className="quartile-firm" style={{ left: `${firmLeft}%` }} />
      </div>
      <div className="quartile-labels">
        <span>Thấp {formatValue(p25)}</span>
        <span>Giữa ngành {formatValue(p50)}</span>
        <span>Cao {formatValue(p75)}</span>
      </div>
    </div>
  )
}

function QuartileLegend() {
  return (
    <div className="quartile-legend">
      <span className="quartile-legend-item">
        <i className="quartile-legend-swatch swatch-range" />
        Khoảng phổ biến — một nửa số doanh nghiệp cùng ngành nằm trong vùng này
      </span>
      <span className="quartile-legend-item">
        <i className="quartile-legend-swatch swatch-median" />
        Mức giữa ngành
      </span>
      <span className="quartile-legend-item">
        <i className="quartile-legend-swatch swatch-firm" />
        Doanh nghiệp của bạn
      </span>
    </div>
  )
}

function describePeerScope(result) {
  if (!result) return null
  const scope = result.peer_scope || ''
  const count = result.peer_count ?? 0
  const divisionMatch = /^vsic_division:(\d+)$/i.exec(scope)
  const division = divisionMatch?.[1]
  const vsicHint = division ? (
    <>
      phân ngành VSIC <strong className="scope-highlight">{division}</strong>
    </>
  ) : (
    scope || 'cùng phân ngành VSIC'
  )

  if (count === 0) {
    return (
      <>
        Chưa có doanh nghiệp niêm yết cùng {vsicHint} có báo cáo tài chính trong dữ liệu
        để làm đối chiếu.
      </>
    )
  }
  return (
    <>
      Đang so sánh với <strong className="scope-highlight">{count}</strong>{' '}
      doanh nghiệp niêm yết cùng {vsicHint} (có báo cáo tài chính trong dữ liệu).
    </>
  )
}

function DigitalSection({ digital }) {
  if (!digital) return null

  if (digital.status !== 'ok') {
    const message = {
      no_stock_code:
        'Nhập tay chưa gắn với doanh nghiệp niêm yết nào, nên chưa so sánh được mức độ số hóa. '
        + 'Hãy bấm nạp một doanh nghiệp ở phía trên.',
      no_company:
        'Doanh nghiệp đã nạp không thuộc phân ngành đang chọn, nên chưa so sánh được mức độ số hóa.',
      no_metrics:
        'Chưa thu thập được dữ liệu kênh số của doanh nghiệp này, nên chưa có gì để so sánh.',
    }[digital.status]
    if (!message) return null
    return (
      <div className="chart-container mb-md">
        <h3>So sánh mức độ số hóa</h3>
        <div className="empty-state">{message}</div>
      </div>
    )
  }

  const entries = Object.entries(DIGITAL_LABELS).filter(
    ([key]) => digital.metrics?.[key] != null,
  )
  if (!entries.length) return null

  return (
    <div
      id="digital-benchmark"
      className="chart-container digital-benchmark mb-md"
    >
      <h3>So sánh mức độ số hóa</h3>
      <p className="chart-note mt-0">
        Dữ liệu kênh số của <strong className="scope-highlight">{digital.stock_code}</strong>
        {digital.period ? ` (kỳ ${String(digital.period).slice(0, 7)})` : ''} so với{' '}
        <strong className="scope-highlight">{digital.peer_count}</strong> doanh nghiệp cùng
        phân ngành đã có dữ liệu số hóa.
      </p>
      {entries.some(([key]) => digital.industry_quartiles?.[key]) && <QuartileLegend />}
      <div className="cards digital-benchmark-cards">
        {entries.map(([key, label]) => {
          const value = digital.metrics[key]
          const pct = digital.percentiles?.[key]
          const avg = digital.industry_averages?.[key]
          const comp = digital.comparison?.[key]
          const quartiles = digital.industry_quartiles?.[key]
          const asPct = (v) => (v == null ? '—' : `${(v * 100).toFixed(2)}%`)
          return (
            <div className="card" key={key}>
              <div className="label">{label}</div>
              <div className="value metric-value-row metric-card-value">
                <span>{asPct(value)}</span>
                <BenchmarkMetricTip metricKey={key} source={DIGITAL_INFO} />
              </div>
              {pct != null ? (
                <>
                  <div className="sub">Xếp hạng: {describeRank(key, pct)}</div>
                  <div className="percentile-bar">
                    <div className="percentile-fill" style={{ width: `${pct}%` }} />
                  </div>
                </>
              ) : (
                <div className="sub">
                  Chưa xếp hạng được — không đủ doanh nghiệp cùng ngành có dữ liệu số hóa
                </div>
              )}
              {quartiles && (
                <QuartileBand quartiles={quartiles} firmValue={value} formatValue={asPct} />
              )}
              <div className="metric-card-avg">
                Trung bình ngành: {asPct(avg)}
              </div>
              <div className="metric-card-badge">
                <span className={`badge ${comparisonBadgeClass(key, comp)}`}>
                  {comparisonLabel(key, comp)}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ShareDonut({ label, value, tone }) {
  const pct = shareToPct(value)
  const r = 36
  const c = 2 * Math.PI * r
  const stroke = tone === 'firm' ? 'var(--singstat-firm)' : 'var(--singstat-industry)'

  if (pct == null) {
    return (
      <div className="singstat-donut">
        <div className="singstat-donut-ring singstat-donut-ring--empty" aria-hidden="true">
          <span className="singstat-donut-na">Không có</span>
        </div>
        <div className="singstat-donut-caption">{label}</div>
      </div>
    )
  }

  const dash = (pct / 100) * c
  return (
    <div className="singstat-donut">
      <svg className="singstat-donut-svg" viewBox="0 0 96 96" aria-hidden="true">
        <circle className="singstat-donut-track" cx="48" cy="48" r={r} />
        <circle
          className="singstat-donut-arc"
          cx="48"
          cy="48"
          r={r}
          stroke={stroke}
          strokeDasharray={`${dash} ${c - dash}`}
          transform="rotate(-90 48 48)"
        />
      </svg>
      <div className="singstat-donut-center">
        <span className="singstat-donut-pct">{pct.toFixed(2)}%</span>
      </div>
      <div className="singstat-donut-caption">{label}</div>
    </div>
  )
}

function KeyExpenditureRow({ label, industry, firm }) {
  const indPct = shareToPct(industry)
  const firmPct = shareToPct(firm)
  const maxPct = Math.max(indPct ?? 0, firmPct ?? 0, 1)

  return (
    <div className="singstat-key-row">
      <div className="singstat-key-row-label">{label}</div>
      <div className="singstat-key-bars">
        <div className="singstat-key-bar-line">
          <span className="singstat-key-bar-tag singstat-key-bar-tag--industry">Ngành</span>
          {indPct == null ? (
            <span className="singstat-na">Không có</span>
          ) : (
            <>
              <div className="singstat-key-bar-track">
                <div
                  className="singstat-key-bar-fill singstat-key-bar-fill--industry"
                  style={{ width: `${(indPct / maxPct) * 100}%` }}
                />
              </div>
              <span className="singstat-key-bar-pct">{indPct.toFixed(2)}%</span>
            </>
          )}
        </div>
        <div className="singstat-key-bar-line">
          <span className="singstat-key-bar-tag singstat-key-bar-tag--firm">DN của bạn</span>
          {firmPct == null ? (
            <span className="singstat-na">Không có</span>
          ) : (
            <>
              <div className="singstat-key-bar-track">
                <div
                  className="singstat-key-bar-fill singstat-key-bar-fill--firm"
                  style={{ width: `${(firmPct / maxPct) * 100}%` }}
                />
              </div>
              <span className="singstat-key-bar-pct">{firmPct.toFixed(2)}%</span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function NarrativePanel({ narrative, narrativeLoading, narrativeError }) {
  return (
    <div
      id="benchmark-narrative"
      className="chart-container story-panel mb-md"
      role="region"
      aria-label="Giải thích kết quả benchmark"
    >
      <h3>Giải thích ROA / ROE / phân vị</h3>
      <p className="chart-note mt-0">
        Chỉ trích dẫn số từ kết quả so sánh vừa nhận — thiếu chỉ số thì bỏ qua, không bịa.
      </p>
      {narrativeLoading && (
        <p className="chart-note">Đang soạn giải thích…</p>
      )}
      {narrativeError && (
        <div className="banner banner-warn" role="alert">
          {narrativeError}
        </div>
      )}
      {!narrativeLoading && narrative?.narrative && (
        <>
          <div className="narrative-list">
            {(narrative.paragraphs?.length
              ? narrative.paragraphs
              : narrative.narrative.split(/\n\n+/)).map((para, idx) => (
              <p key={`narr-${idx}`} className={`chart-note${idx === 0 ? ' mt-0' : ''}`}>
                {para}
              </p>
            ))}
          </div>
          {narrative.omitted?.length > 0 && (
            <p className="chart-note muted-text">
              Bỏ qua (thiếu trong kết quả): {narrative.omitted.join(', ')}
            </p>
          )}
          <p className="chart-note muted-text narrative-source">
            Nguồn: {narrative.method === 'llm' ? 'LLM (đã kiểm tra số)' : 'mẫu rules-first'}
          </p>
        </>
      )}
      {!narrativeLoading && !narrativeError && !narrative?.narrative && (
        <div className="empty-state">Chưa có giải thích cho kết quả này.</div>
      )}
    </div>
  )
}

export default function BenchmarkResults({ result, narrative, narrativeLoading, narrativeError }) {
  const insufficientPeers = insufficientPeersFromResult(result)
  const metricEntries = presentMetricEntries(result)
  const avg = result?.industry_averages || {}
  const summary = buildBenchmarkSummary(result, metricEntries)
  const radarData = buildRadarData(metricEntries, result)

  return (
    <div>
      <div className="chart-container mb-md">
        <p className="chart-note mt-0 peer-scope-note">
          {describePeerScope(result)}
          {insufficientPeers && (
            <>
              {' '}
              <span className="badge badge-warning">chưa đủ dữ liệu so sánh</span>
            </>
          )}
        </p>
        <div className="singstat-jump">
          <button
            type="button"
            className="singstat-jump-btn"
            onClick={() => scrollToId('singstat-expenditure')}
          >
            So sánh tỷ lệ liên quan chi phí
          </button>
          <button
            type="button"
            className="singstat-jump-btn"
            onClick={() => scrollToId('singstat-kpi')}
          >
            So sánh hiệu quả theo phân vị
          </button>
        </div>
      </div>

      <NarrativePanel
        narrative={narrative}
        narrativeLoading={narrativeLoading}
        narrativeError={narrativeError}
      />

      <div id="singstat-kpi">
        {metricEntries.length === 0 ? (
          <div className="empty-state">
            Không tính được chỉ số từ dữ liệu hiện tại — bổ sung BCTC (tài sản/vốn CSH/…) hoặc nạp RAL.
          </div>
        ) : (
          <>
            {radarData.length >= 3 && (
              <div className="chart-container mb-md">
                <h3>Vị trí của doanh nghiệp so với các doanh nghiệp cùng ngành</h3>
                <p className="chart-note mt-0">
                  Mỗi trục là một chỉ số, thang 0–100: càng ra ngoài càng tốt hơn so với các
                  doanh nghiệp cùng ngành. Đường nét đứt là mức giữa của ngành. Riêng nợ trên
                  vốn chủ sở hữu đã được đảo chiều, nên ra ngoài nghĩa là vay nợ ít hơn.
                </p>
                <ResponsiveContainer width="100%" height={320}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="var(--accent-soft)" />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: 'var(--ink)' }} />
                    <PolarRadiusAxis
                      angle={30}
                      domain={[0, 100]}
                      tick={{ fontSize: 10 }}
                    />
                    <Radar
                      name="Doanh nghiệp của bạn"
                      dataKey="firm"
                      stroke="var(--accent)"
                      fill="var(--accent)"
                      fillOpacity={0.35}
                    />
                    <Radar
                      name="Mức giữa của ngành"
                      dataKey="peerMedian"
                      stroke="var(--ink)"
                      fill="transparent"
                      strokeDasharray="4 4"
                    />
                    <Legend />
                    <Tooltip formatter={(value) => formatIndex(value)} />
                  </RadarChart>
                </ResponsiveContainer>

                {summary && (
                  <div className="benchmark-summary" role="status">
                    {summary.empty ? (
                      <p className="benchmark-summary-empty">{summary.empty}</p>
                    ) : (
                      <>
                        <div className="benchmark-summary-head">
                          <span className="benchmark-summary-score">
                            {summary.aboveMedian}
                            <span className="benchmark-summary-total">
                              /{summary.total}
                            </span>
                          </span>
                          <span className="benchmark-summary-caption">
                            chỉ số đạt từ mức giữa của ngành trở lên
                          </span>
                        </div>
                        <ul className="benchmark-summary-list">
                          <li>
                            <span className="benchmark-summary-tag is-strong">
                              Điểm mạnh
                            </span>
                            <span>
                              <strong>{summary.strongest.label}</strong> —{' '}
                              {describeRank(summary.strongest.key, summary.strongest.pct)}.
                            </span>
                          </li>
                          <li>
                            <span className="benchmark-summary-tag is-weak">
                              {summary.weakestIsLeverage ? 'Cần chú ý' : 'Điểm yếu'}
                            </span>
                            <span>
                              <strong>{summary.weakest.label}</strong> —{' '}
                              {describeRank(summary.weakest.key, summary.weakest.pct)}.
                            </span>
                          </li>
                        </ul>
                      </>
                    )}
                  </div>
                )}
              </div>
            )}

            {metricEntries.some(([key]) => result.industry_quartiles?.[key]) && (
              <QuartileLegend />
            )}
            <div className="cards">
              {metricEntries.map(([key, label]) => {
                const value = result[key]
                const pct = result.percentiles?.[key]
                const comp = result.comparison?.[key]
                const indAvg = result.industry_averages?.[key]
                const quartiles = result.industry_quartiles?.[key]
                return (
                  <div className="card" key={key}>
                    <div className="label">{label}</div>
                    <div className="value metric-value-row metric-card-value">
                      <span>{formatRatio(value, key)}</span>
                      <BenchmarkMetricTip metricKey={key} />
                    </div>
                    {pct != null ? (
                      <>
                        <div className="sub">
                          Xếp hạng: {describeRank(key, pct)}
                        </div>
                        <div className="percentile-bar">
                          <div className="percentile-fill" style={{ width: `${pct}%` }} />
                        </div>
                      </>
                    ) : (
                      <div className="sub">
                        Chưa xếp hạng được — không đủ doanh nghiệp cùng ngành để so sánh
                      </div>
                    )}
                    {quartiles ? (
                      <QuartileBand
                        quartiles={quartiles}
                        firmValue={value}
                        formatValue={(v) => formatRatio(v, key)}
                      />
                    ) : (
                      pct != null && (
                        <div className="sub muted quartile-hint">
                          Cần ít nhất 4 doanh nghiệp cùng ngành để hiện khoảng phổ biến
                        </div>
                      )
                    )}
                    <div className="metric-card-avg">
                      Trung bình ngành: {indAvg != null ? formatRatio(indAvg, key) : 'Không có'}
                    </div>
                    <div className="metric-card-badge">
                      <span className={`badge ${comparisonBadgeClass(key, comp)}`}>
                        {comparisonLabel(key, comp)}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>

            <DigitalSection digital={result.digital} />
          </>
        )}
      </div>

      <section id="singstat-expenditure" className="singstat-section">
        <header className="singstat-section-head">
          <h3 className="singstat-section-title">Tỷ lệ liên quan chi phí</h3>
        </header>

        <div className="singstat-donut-row">
          <ShareDonut
            label="Ngành"
            value={avg.expenditure_related_ratio}
            tone="industry"
          />
          <ShareDonut
            label="DN của bạn"
            value={result.expenditure_related_ratio}
            tone="firm"
          />
        </div>

        <div className="singstat-legend">
          <span className="singstat-legend-item">
            <i className="singstat-swatch singstat-swatch--industry" /> Ngành
          </span>
          <span className="singstat-legend-item">
            <i className="singstat-swatch singstat-swatch--firm" /> DN của bạn
          </span>
        </div>

        <header className="singstat-section-head singstat-section-head--follow">
          <h3 className="singstat-section-title">Cơ cấu chi phí chính</h3>
        </header>

        <div className="singstat-key-list">
          {KEY_EXPENDITURE_ROWS.map(({ key, label }) => (
            <KeyExpenditureRow
              key={key}
              label={label}
              industry={avg[key]}
              firm={result[key]}
            />
          ))}
        </div>

        {(result.comparison?.expenditure_related_ratio
          || result.comparison?.purchase_goods_share) && (
          <p className="singstat-comp-note">
            So sánh chi phí:{' '}
            {COMPARISON_LABELS[result.comparison?.expenditure_related_ratio]
              || result.comparison?.expenditure_related_ratio
              || '—'}
            {formatSharePct(result.expenditure_related_ratio) != null && (
              <> · Tỷ lệ chi phí DN {formatSharePct(result.expenditure_related_ratio)}</>
            )}
          </p>
        )}
      </section>
    </div>
  )
}
