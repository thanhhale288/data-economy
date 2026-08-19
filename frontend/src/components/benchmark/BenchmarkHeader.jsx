import {
  NA_LABEL,
  buildBreadcrumbCrumbs,
  buildIndustryContext,
} from '../../benchmarkIndustryContext'

export default function BenchmarkHeader({ vsicCode, peerScopeFromResult }) {
  const industryContext = buildIndustryContext(vsicCode, { peerScopeFromResult })
  const breadcrumbCrumbs = buildBreadcrumbCrumbs(vsicCode)

  return (
    <header className="benchmark-masthead">
      <h2 className="page-title">So sánh hiệu quả doanh nghiệp</h2>
      <p className="page-subtitle">
        Upload BCTC → trích xuất → kiểm tra/chỉnh sửa → xác nhận → so sánh phân vị với peers niêm yết
        trong mẫu (không phải chuẩn ngành quốc gia / census GSO). Thiếu số liệu luôn hiện N/A — không bịa phân vị.
      </p>

      <nav className="page-breadcrumb" aria-label="Đường dẫn">
        <ol>
          {breadcrumbCrumbs.map((crumb) => (
            <li
              key={crumb.id}
              aria-current={crumb.current ? 'page' : undefined}
            >
              {crumb.label}
            </li>
          ))}
        </ol>
      </nav>

      <section className="industry-context" aria-labelledby="industry-context-heading">
        <h3 id="industry-context-heading" className="industry-context-title">
          {industryContext.title}
        </h3>
        <p>{industryContext.copy.peersReminder}</p>
        <dl className="industry-context-dl">
          <dt>
            {industryContext.peerScopeSourced === 'result'
              ? 'peer_scope'
              : 'peer_scope (dự kiến)'}
          </dt>
          <dd className={industryContext.peerScope ? undefined : 'is-na'}>
            {industryContext.peerScopeDisplay}
          </dd>
          <dt>Phân ngành VSIC (2 số)</dt>
          <dd className={industryContext.division ? undefined : 'is-na'}>
            {industryContext.divisionDisplay}
          </dd>
        </dl>
        <p>{industryContext.copy.noGsoTables}</p>
        <p>
          {industryContext.copy.insufficientDemoPrefix}{' '}
          <a href="#insufficient-peers-demo">
            {industryContext.copy.insufficientDemoLink}
          </a>
          . Phân vị hiện {NA_LABEL} khi chưa đủ DN cùng ngành — không bịa.
        </p>
      </section>
    </header>
  )
}
