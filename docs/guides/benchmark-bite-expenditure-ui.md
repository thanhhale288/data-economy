# Benchmark BITE — Expenditure UI guide

SingStat [BITE](https://www.singstat.gov.sg/data-tools-services/business-insights-tool-for-enterprises-bite/benchmark-my-performance/retail-trade/wearing-apparel-footwear)-style **expenditure** block for Module 5: form “Of which” cost inputs → four share/ratio metrics, compared to VSIC 2-digit peers from seeded BCTC.

**Do not invent numbers.** Missing inputs → null ratio. Missing peer sample → null percentile + `insufficient_peers` (never a fake 50th).

---

## Source files

| Layer | Path |
|-------|------|
| Form + results UI | `frontend/src/pages/Benchmark.jsx` |
| Shared styles (form grid, percentile bar, badges, empty-state) | `frontend/src/index.css` |
| Ratio math + peer populations | `backend/app/services/benchmark_service.py` |
| Request/response shapes | `backend/app/schemas/__init__.py` (`BenchmarkInput`, `BenchmarkResult`) |
| HTTP | `backend/app/api/benchmark.py` — `POST /api/benchmark/compare`, `GET /api/benchmark/prefill/{stock_code}` |
| FE client | `frontend/src/api.js` — `api.benchmark`, `api.benchmarkPrefill` |

---

## Four expenditure ratios

Computed in `compute_benchmark_ratios` / `_ratios_from_report` via `_safe_div` (returns `null` if numerator/denominator missing or denominator is 0).

| API metric key | Formula | BITE-ish meaning |
|----------------|---------|------------------|
| `expenditure_related_ratio` | `operating_expenses / operating_revenue` | Cost intensity vs revenue |
| `purchase_goods_share` | `cost_of_goods / operating_expenses` | COGS share of opex (“Of which” purchases) |
| `rental_cost_share` | `rental_cost / operating_expenses` | Rental share of opex |
| `remuneration_share` | `remuneration / operating_expenses` | Labour cost share of opex |

**Peers:** same formulas on each peer’s latest annual `FinancialReport` (`revenue` stands in for `operating_revenue`). Null BCTC fields stay null — no fill.

**Core ratios (unchanged):** ROA, ROE, current_ratio, equity_ratio, revenue_per_worker, profit_per_worker — still from BS / PBT / headcount; expenditure fields are not inputs to those.

---

## Form fields ↔ API

Empty optional strings are sent as JSON `null` (see submit handler in `Benchmark.jsx`). Required fields are coerced with `Number(...)`.

| UI label (VI) | Form state key | `BenchmarkInput` | Required |
|---------------|----------------|------------------|----------|
| VSIC Code | `vsic_code` | `vsic_code` | yes |
| Doanh thu (VND) | `operating_revenue` | `operating_revenue` | yes |
| Lợi nhuận trước thuế (VND) | `profit_before_tax` | `profit_before_tax` | yes |
| Số nhân viên | `employees` | `employees` | yes |
| Chi phí hoạt động (VND) | `operating_expenses` | `operating_expenses` | no — needed for expenditure ratios |
| Giá vốn hàng bán (VND) | `cost_of_goods` | `cost_of_goods` | no — `purchase_goods_share` |
| Chi phí thuê (VND) | `rental_cost` | `rental_cost` | no — `rental_cost_share` |
| Chi phí lương (VND) | `remuneration` | `remuneration` | no — `remuneration_share` |
| Tổng tài sản / Vốn CSH / TSNH / Nợ NH | `total_assets`, `total_equity`, `current_assets`, `current_liabilities` | same | no — ROA/ROE/liquidity |

**Prefill:** `GET /api/benchmark/prefill/{stock_code}` → `formFromPrefill` maps the same keys from latest BCTC (`revenue` → `operating_revenue`). 404 if revenue / PBT / employees missing — UI must not invent fill values.

**Demo thiếu peer:** button sets `vsic_code` to `1100` (`NO_PEER_VSIC`) while keeping firm inputs.

---

## N/A / `insufficient_peers` honesty rules

| Situation | API / UI behaviour |
|-----------|-------------------|
| User ratio inputs incomplete | Metric omitted from result payload (or `null`); UI shows “—” / hides card if filtered |
| Peer population empty for a metric | `percentiles[metric] = null`, `comparison[metric] = "insufficient_peers"` |
| `peer_count == 0` or all metric populations empty | Warning `insufficient_peers` on result; no fake industry average |
| Peer count &lt; 3 (but &gt; 0) | Warning `small_peer_sample` + always `prototype_listed_sample` |
| Percentile display | Show **N/A (thiếu mẫu peer)** — never invent 50th |
| Industry average | Show **N/A** when null |
| Empty form (no prefill) | Warn banner: do not use hard-coded sample numbers |

Comparison bands when a peer average exists: `above_average` if value &gt; 1.1× avg, `below_average` if &lt; 0.9× avg, else `average`.

---

## Smoke / screenshot checklist

Run API + FE locally (`uvicorn` :8000, Vite :5173). Prefer seeded Postgres/SQLite after `alembic upgrade head` + seed.

1. **Empty form** — banner “Form trống”; no invented defaults in inputs.
2. **Prefill RAL** — fields fill from BCTC; note shows `/api/benchmark/prefill/RAL`.
3. **Compare with peers (e.g. VSIC 27 / RAL)** — peer_count &gt; 0; core metrics + expenditure cards when opex/COGS/rental/remuneration present; percentiles numeric where peers have data.
4. **Expenditure null honesty** — clear `operating_expenses` (or COGS only); affected shares absent or N/A; other metrics still compute.
5. **Demo thiếu peer (VSIC 1100)** — badge/`warnings` include `insufficient_peers`; Percentile: N/A; TB ngành: N/A; firm ratios still shown if inputs complete.
6. **Prefill BMP** (or thin BCTC) — expect honest 404 / error copy, not fake employees.
7. **Screenshot set (optional):** (a) empty, (b) RAL result with expenditure shares, (c) insufficient_peers empty-state.

Scoped tests (when touching production code in other waves): `PYTHONPATH=. pytest -q tests/benchmark/`.

---

## Related

- Domain lock: `CONTEXT.md` (Benchmark / SingStat BITE)
- Roadmap for next FE waves: [`frontend-benchmark-roadmap.md`](./frontend-benchmark-roadmap.md)
- Anti-slop skill install notes: [`anti-ai-slop-skills.md`](./anti-ai-slop-skills.md)
