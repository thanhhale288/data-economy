# Handoff — Task #81 Benchmark Wave A

**Status:** DONE  
**Branch:** `cursor/epic5-phase5-task81-benchmark-wave-a`  
**Date:** 2026-08-19  
**Phase:** Epic 5 Phase 5.5 (FE leftover)  
**Base:** `origin/main` @ `f17bf4c`  
**PR:** (filled after `gh pr create`)

---

## Delivered

| Piece | Path |
|-------|------|
| Copy / builders | `frontend/src/benchmarkIndustryContext.js` |
| node:test | `frontend/src/benchmarkIndustryContext.test.js` |
| Page chrome | `frontend/src/pages/Benchmark.jsx` — header, breadcrumb, industry context **above** the form |
| Tokens | `frontend/src/index.css` — `.page-breadcrumb`, `.industry-context` (existing `--ink` / `--muted` / `--accent`) |

**Không đổi:** `backend/app/services/benchmark_service.py` math, Digital VA / VDEI, Wave B component split, Playwright (#68).

---

## What the UI shows

1. **Header** — title «So sánh hiệu quả doanh nghiệp» + subtitle: peers niêm yết trong mẫu, **không** census GSO / chuẩn ngành quốc gia; thiếu số → N/A.
2. **Breadcrumb** — `Benchmark` alone when VSIC empty (không bịa mã); `Benchmark → VSIC 27` after form/prefill/URL (2 ký tự đầu, cùng quy tắc `vsic_division_prefix`). Không cây category bán lẻ giả.
3. **Industry context (trên form)** — `peer_scope` (`vsic_division:{2-digit}` từ form, hoặc từ API sau compare); phân ngành VSIC 2 số; reminder peer = BCTC listed seed (~28); **không** bảng tỷ lệ ngành GSO; link tới demo VSIC 1100 (`#insufficient-peers-demo`) cho `insufficient_peers`.

Thiếu VSIC → các ô hiện **N/A**. Không invent số GSO/OECD/CafeF.

---

## Honesty limits

- Peer = listed BCTC đã seed, **không** tổng điều tra GSO.
- `~28` lấy từ copy mẫu sẵn có (`WARNING_LABELS` / SampleHonestyBanner) — không bịa census mới.
- Demo `1100` giữ nguyên nút cũ; Wave A chỉ thêm path cue + context.
- Hallmark: in-place, token khóa; không catalog theme mới, không hex inline, không glow pill, không italic heading.

---

## Verify

```bash
cd frontend && node --test src/benchmarkIndustryContext.test.js
# 7 passed

cd frontend && npm run build
# vite build OK (agent)
```

---

## Giải thích dễ hiểu

### Đã làm
- User thấy **đang so sánh với ai** (phân ngành VSIC 2 số, mẫu niêm yết) **trước khi** điền form.
- VSIC trống → N/A / ẩn division trên breadcrumb — không bịa mã ngành.

### Hạn chế / chưa làm
- Wave B (tách `components/benchmark/*`) — Task #92 gated.
- Không có tên ngành GSO / bảng tỷ lệ quốc gia (không có nguồn số trên trang này).
- Không đổi percentile / peer math.
