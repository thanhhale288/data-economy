# Handoff — Task #73 Dashboard anomaly chip (latest IIP)

**Status:** DONE  
**Branch:** `cursor/epic5-phase2-task73-dashboard-anomaly-chip`  
**Date:** 2026-08-19  
**Phase:** Epic 5 Phase 5.2 (Forecast / anomaly productize)  
**Base:** `origin/main` @ `58d2bc2`  
**PR:** (filled after `gh pr create`)

---

## Delivered

- Dashboard gọi `api.getAnomalies()` (cùng `GET /api/ml/anomaly` như ML Lab). Lỗi request → **ẩn chip**, không bịa alert.
- Chip/`banner-warn` **chỉ hiện** khi:
  - `anomaly.available === true` **và** `anomaly.iip.available === true`
  - điểm IIP khớp **kỳ IIP mới nhất** có `is_anomaly === true`
- Kỳ mới nhất: `summary.latest_period` (kỳ của `iip_latest`); nếu thiếu thì kỳ cuối chuỗi IIP Dashboard; nếu vẫn thiếu thì điểm cuối `iip.points`.
- Copy VI trung thực: kỳ bị Isolation Forest gắn cờ, **không** phải cảnh báo khủng hoảng; link tới ML Lab (`/ml`).
- `available=false` / series ngắn / thiếu điểm / kỳ mới nhất **không** flagged → **ẩn** (không có banner “all clear”).
- Không sửa `ml/anomaly/detector.py`, formula, `docs/plan.md`, hay checklist Epic 5.

Files:

- `frontend/src/iipAnomalyChip.js` — helper hide/show
- `frontend/src/pages/Dashboard.jsx` — fetch + banner cạnh biểu đồ IIP + dự báo

---

## Giải thích dễ hiểu

Isolation Forest đã chạy trên chuỗi IIP ở ML Lab. Task này **không** phát hiện thêm gì — chỉ **nêu trên Dashboard** khi **tháng IIP mới nhất** thật sự bị gắn cờ.

- Có cờ trên kỳ mới nhất → một banner cảnh báo nhẹ (token `banner-warn` sẵn có) + link ML Lab.
- Không cờ / chưa đủ dữ liệu / API lỗi → Dashboard im lặng. Không invent “có bất thường”, cũng không invent “mọi thứ ổn”.

---

## Hide / show logic

`latestIipAnomalyPoint(anomaly, latestPeriod)` trả về điểm flagged hoặc `null`:

| Condition | Chip |
|-----------|------|
| `anomaly` null / request fail | ẩn |
| `available !== true` | ẩn |
| `iip.available !== true` (thiếu series / quá ngắn) | ẩn |
| `iip.points` rỗng | ẩn |
| có `latestPeriod` nhưng không khớp điểm nào | ẩn |
| điểm khớp (hoặc điểm cuối nếu không có period) `is_anomaly !== true` | ẩn |
| điểm khớp `is_anomaly === true` | hiện |

Không hiện chip xanh “all clear”.

---

## Testing results

```bash
cd frontend && npm run build
# vite v5.4.21 — ✓ built in ~1.7s
```

Helper cases (node ESM, không thêm test runner):

- `available=false` → ẩn
- `iip.available=false` → ẩn
- points rỗng → ẩn
- kỳ mới nhất `is_anomaly=false` (kỳ cũ flagged) → ẩn
- kỳ mới nhất flagged → hiện
- Dashboard period khác điểm cuối → khớp period Dashboard, không lấy điểm cuối mù
- payload null → ẩn

Không pytest FE (repo không có Vitest). Không chạy detector.

---

## Hallmark

Component-scope trên Dashboard có sẵn: **không** theme mới, **không** 8-state demo, **không** inline hex mới, **không** glow/pill 999px. Reuse `.banner.banner-warn` + `.badge-warning`.

---

## Do not reopen

- Không tick `docs/plan.md` / checklist `.scratch/epic5-remain-plan.md` trong PR này.
- Không đổi Isolation Forest / contamination / threshold.
- Không copy chart anomaly từ ML Lab lên Dashboard.
- Không hiện alert khi `available=false`.
