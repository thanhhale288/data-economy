/** Vietnamese labels for Benchmark UI. Keep in sync with backend metric keys. */

export const METRIC_LABELS = {
  roa: 'Tỷ suất sinh lời trên tài sản (ROA)',
  roe: 'Tỷ suất sinh lời trên vốn CSH (ROE)',
  current_ratio: 'Hệ số thanh toán hiện hành',
  equity_ratio: 'Tỷ trọng vốn chủ sở hữu',
  revenue_per_worker: 'Doanh thu trên lao động',
  profit_per_worker: 'Lợi nhuận trên lao động',
  profit_margin: 'Biên lợi nhuận trước thuế',
  asset_turnover: 'Vòng quay tài sản',
  debt_to_equity: 'Nợ trên vốn chủ sở hữu',
}

/** Short labels for radar axes. */
export const METRIC_SHORT = {
  roa: 'ROA',
  roe: 'ROE',
  current_ratio: 'Thanh khoản',
  equity_ratio: 'Tỷ trọng VCSH',
  revenue_per_worker: 'DT/LĐ',
  profit_per_worker: 'LN/LĐ',
  profit_margin: 'Biên LN',
  asset_turnover: 'Vòng quay TS',
  debt_to_equity: 'Nợ/VCSH',
}

/** Higher value = more leverage risk (not “better”). */
export const HIGHER_IS_WORSE = new Set(['debt_to_equity'])

/** Công thức khớp `compute_benchmark_ratios`. */
export const METRIC_INFO = {
  roa: {
    title: 'Tỷ suất sinh lời trên tài sản (ROA)',
    numerator: 'Lợi nhuận trước thuế',
    denominator: 'Tổng tài sản',
    blurb: 'Đo hiệu quả sử dụng tài sản để tạo lợi nhuận.',
  },
  roe: {
    title: 'Tỷ suất sinh lời trên vốn CSH (ROE)',
    numerator: 'Lợi nhuận trước thuế',
    denominator: 'Vốn chủ sở hữu',
    blurb: 'Đo mức sinh lời cho chủ sở hữu so với vốn CSH trên sổ sách.',
  },
  current_ratio: {
    title: 'Hệ số thanh toán hiện hành',
    numerator: 'Tài sản ngắn hạn',
    denominator: 'Nợ ngắn hạn',
    blurb: 'Khả năng thanh khoản: đáp ứng nghĩa vụ ngắn hạn bằng tài sản ngắn hạn.',
  },
  equity_ratio: {
    title: 'Tỷ trọng vốn chủ sở hữu',
    numerator: 'Vốn chủ sở hữu',
    denominator: 'Tổng tài sản',
    blurb: 'Tỷ lệ tài sản được tài trợ bằng vốn chủ sở hữu thay vì nợ.',
  },
  revenue_per_worker: {
    title: 'Doanh thu trên lao động',
    numerator: 'Doanh thu hoạt động',
    denominator: 'Số lao động',
    blurb: 'Chỉ số gần đúng năng suất lao động theo doanh thu hoạt động trên mỗi người.',
  },
  profit_per_worker: {
    title: 'Lợi nhuận trên lao động',
    numerator: 'Lợi nhuận trước thuế',
    denominator: 'Số lao động',
    blurb: 'Chỉ số gần đúng năng suất theo lợi nhuận trước thuế trên mỗi người.',
  },
  profit_margin: {
    title: 'Biên lợi nhuận trước thuế',
    numerator: 'Lợi nhuận trước thuế',
    denominator: 'Doanh thu hoạt động',
    blurb: 'Mỗi đồng doanh thu tạo ra bao nhiêu lợi nhuận trước thuế.',
  },
  asset_turnover: {
    title: 'Vòng quay tài sản',
    numerator: 'Doanh thu hoạt động',
    denominator: 'Tổng tài sản',
    blurb: 'Mức doanh thu tạo ra trên mỗi đồng tài sản. Cùng ROA: ROA ≈ biên LN × vòng quay tài sản.',
  },
  debt_to_equity: {
    title: 'Nợ trên vốn chủ sở hữu',
    numerator: 'Tổng tài sản − Vốn CSH',
    denominator: 'Vốn chủ sở hữu',
    blurb:
      'Ước lượng đòn bẩy: nợ tương đối so với vốn chủ. Số cao hơn thường nghĩa rủi ro đòn bẩy cao hơn — không phải chỉ số “càng cao càng tốt”.',
  },
}

export const COMPARISON_LABELS = {
  above_average: 'Trên trung bình ngành',
  below_average: 'Dưới trung bình ngành',
  average: 'Bằng trung bình ngành',
  insufficient_peers: 'Chưa đủ doanh nghiệp cùng ngành',
  neutral: '—',
}

export const DEBT_COMPARISON_LABELS = {
  above_average: 'Đòn bẩy cao hơn ngành',
  below_average: 'Đòn bẩy thấp hơn ngành',
  average: 'Đòn bẩy gần trung bình ngành',
  insufficient_peers: 'Chưa đủ doanh nghiệp cùng ngành',
  neutral: '—',
}

/** API BenchmarkResult.warnings → Vietnamese honesty copy (show all, not only insufficient_peers). */
export const WARNING_LABELS = {
  prototype_listed_sample:
    'So sánh trên mẫu DN niêm yết trong nền tảng (~28 DN) — chưa phải chuẩn ngành quốc gia (VSIC Section C).',
  small_peer_sample:
    'Ít hơn 3 DN cùng ngành có BCTC — phân vị chỉ mang tính tham khảo.',
  insufficient_peers:
    'Chưa đủ doanh nghiệp cùng ngành trong dữ liệu để so sánh phân vị.',
}

export const KEY_EXPENDITURE_ROWS = [
  { key: 'purchase_goods_share', label: 'Chi phí hàng hóa & nguyên vật liệu' },
  { key: 'remuneration_share', label: 'Chi phí nhân công (thuyết minh)' },
]

export const DIGITAL_LABELS = {
  digital_adoption_score: 'Mức độ số hóa kênh bán',
  online_revenue_ratio: 'Tỷ trọng doanh thu online (ước lượng)',
}

export const DIGITAL_INFO = {
  digital_adoption_score: {
    title: 'Mức độ số hóa kênh bán',
    blurb:
      'Điểm tổng hợp 0–100% từ các kênh đã ghi nhận: website, gian hàng sàn thương mại điện tử và tín hiệu bán hàng. Điểm cao nghĩa là doanh nghiệp hiện diện trên nhiều kênh số hơn.',
  },
  online_revenue_ratio: {
    title: 'Tỷ trọng doanh thu online (ước lượng)',
    numerator: 'Doanh thu online ước lượng',
    denominator: 'Doanh thu hoạt động',
    blurb:
      'Phần doanh thu đến từ kênh online so với tổng doanh thu. Doanh thu online là ước lượng từ các sản phẩm thu thập được trên sàn, không phải số doanh nghiệp công bố.',
  },
}

export const EXTRACT_LOW_CONFIDENCE = 0.75
