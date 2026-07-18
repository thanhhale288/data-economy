# Phase 2 — Wave orchestration (canonical)

**Branch:** `cursor/phase2-enterprise-digital`  
**Checklist:** `.scratch/phase2/checklist.md`

Không chạy Task 6/7/8/9 song song với Task 5 trên shared files.

## WAVE 1 — Subagent A: Task 5 Company crawler

**Owns:** `crawlers/companies/listed_companies.py`, `crawlers/financial/**`, `tests/companies/**`, `tests/financial/**`  
**Không sửa:** marketplace, shop matcher, `digital_metrics.py`, GSO/OECD  
**Detector:** giữ nguyên / thin-wrap — không mở rộng checkout (Task 6)

## WAVE 2 — Subagent B ∥ C (sau Wave 1)

| Agent | Task | Owns |
|-------|------|------|
| B | 6 Website detector | `website_detector.py` mới + tests; thin call-site trong `listed_companies.py` |
| C | 7 Marketplace | `crawlers/marketplace/**` scrapers; không matcher đầy đủ; không đụng detector/metrics |

## WAVE 3 — Subagent D: Task 8 Shop-matcher

`ml/shop_matcher/**`, QA bảng, `shop_finder` chỉ gọi matcher

## WAVE 4 — Subagent E: Task 9 Digital metrics

`pipeline/cleaning/digital_metrics.py` — không đổi công thức Digital VA

## Shared (agent chính)

models / migrations / seed / pipeline / scheduler / requirements — đề xuất rồi tích hợp cuối wave nếu an toàn.
