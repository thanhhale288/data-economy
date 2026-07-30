# Handoff — Epic 4 FE Hallmark full pass

**Status:** DONE (uncommitted — commit/PR khi user yêu cầu)  
**Branch:** `cursor/epic4-fe-hallmark-full-pass` (from `origin/main` tip incl. #54/#55/#56)  
**Date:** 2026-07-30  
**Scope:** Hallmark audit + in-place redesign toàn FE — không đổi math / API / DocAI flow

---

## Hallmark report

### Top issues trước (severity)

| Sev | Issue |
|-----|--------|
| High | Stacked radial/linear gradients trên body, cards, charts, active nav, primary buttons → “AI atmospheric” trên dashboard dữ liệu |
| High | CTA hierarchy: Pipeline 9 nút đều `btn-primary`; Benchmark primary gắn RAL thay vì upload DocAI |
| High | Secondary `.btn` thiếu nền/border rõ; thiếu `:disabled` / `:focus-visible` nhất quán |
| Med | Page titles ALL CAPS + wide tracking → templated; section `h3` cũng uppercase |
| Med | Low-confidence field highlight dùng hex inline (`#d97706`) thay vì token |
| Med | Loading chỉ text giữa trang; Dashboard nuốt lỗi load (console only) → rủi ro màn trống |
| Med | Pill chips `border-radius: 999px` + lift hover trên data cards |
| Low | Nhiều `style={{ margin* }}` rải rác; `transition: … ease` browser-default |
| Low | Thiếu `prefers-reduced-motion` |

### Thay đổi chính đã làm

1. **Tokens + surfaces** (`index.css`): spacing / ease / duration / warn-field / focus-ring; flat paper surfaces; bỏ radial bloom nền; nav active solid ink; primary CTA flat accent (không 135° gradient glow).
2. **Typography**: bỏ ALL CAPS page/section titles; tracking âm nhẹ; hierarchy data-dense hơn.
3. **States**: button hover/active/focus-visible/disabled; input focus-visible; loading spinner + reduced-motion; class `.field-low-confidence` cho guardrail #56.
4. **Benchmark**: subtitle honesty + flow #54/#55/#56; upload là primary CTA; confirm checkbox block; token-based low-confidence; giữ extract → confirm → compare.
5. **Pipeline**: chỉ «Chạy tất cả» primary; error = `banner-warn` (không nhầm empty-state).
6. **Dashboard / MLLab / Companies / CompanyDetail**: load-error rõ; subtitles honesty; spacing classes; story panel border token.

### Re-audit sau

- Không còn gradient CTA / body bloom / card lift “marketing”.
- Empty / loading / error phân biệt rõ hơn trên Dashboard, Pipeline, MLLab, Benchmark.
- DocAI flow + confidence visual còn nguyên (class thay inline hex).
- Còn deferred (không chặn merge): Wave A industry context block đầy đủ; Wave B split `components/benchmark/*`; một số width % vẫn inline (quartile/radar — cần dynamic).

### Issues còn lại + lý do defer

| Item | Lý do defer |
|------|-------------|
| Benchmark Wave A breadcrumb / industry context panel | Roadmap riêng; không bịa GSO |
| Componentize Benchmark | Wave B — ngoài scope polish |
| Chunk-split Recharts | Build warning size — không phải visual blocker |
| Soften remaining inline chart positioning | Dynamic layout; an toàn giữ inline |

---

## Files changed

### FE (core)
- `frontend/src/index.css`
- `frontend/src/pages/Benchmark.jsx`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/pages/MLLab.jsx`
- `frontend/src/pages/Pipeline.jsx`
- `frontend/src/pages/Companies.jsx`
- `frontend/src/pages/CompanyDetail.jsx`
- `frontend/src/SampleHonestyBanner.jsx`

### Docs / agent wiring
- `docs/plan.md` — note FE Hallmark pass
- `.scratch/handoff-epic4-fe-hallmark-pass.md` (this file)
- `AGENTS.md` + `.cursor/rules/frontend-hallmark.mdc` + small Hallmark skill description tweak (auto-wire FE → Hallmark)

---

## Verification

```bash
cd frontend && npm run build
# → vite build OK (2026-07-30)
```

Không có script `npm test` FE meaningful trong `package.json` — skipped.

---

## Constraints respected

- Không đổi benchmark math, Digital VA/VDEI, percentile.
- Không phá upload → extract → prefill → confirm → compare.
- Không đụng backend / #57+.
- Palette blue-report + Be Vietnam Pro / JetBrains Mono giữ nguyên (không cream/serif slop).
