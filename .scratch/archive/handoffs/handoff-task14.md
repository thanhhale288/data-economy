# Handoff — Task #14 Company detail (Module 2)

**Status:** DONE  
**Date:** 2026-07-20  
**Branch:** `cursor/phase4-task14-company-detail`  
**Commit:** `681e610` (feature tip; impl `decc57b`)  
**PR:** https://github.com/thanhhale288/data-economy/pull/7 (base: `cursor/phase4-task13-dashboard`)  
**Base:** tip Task #13 `0e211cc` (PR #5 / #6 still not on `main` at Task #14 start)  
**Repo:** `/Users/hale/Code/AI in Data Economy`

---

## Delivered

- BE `company_service.py`:
  - Enriched `CompanyDetail` with `crawl_timeline`, `data_quality`, optional `case_study`
  - Timeline derived from `digital_presence` + `marketplace_listings` timestamps (honest overwrite semantics)
  - Deterministic completeness/verification score (not market accuracy)
  - RAL case study from persisted website/Shopee/VSIC 2740 only — no invented TikTok/CafeF/marketplace totals
- Schemas: listing `crawled_at`; `CompanyCrawlEventOut`, `CompanyDataQualityOut`, `CompanyCaseStudyOut`
- FE `CompanyDetail.jsx`: profile strip, channel cards (website/Shopee/TikTok), online est. + Digital VA cards, listing table, quality + timeline, RAL banner
- FE `Companies.jsx`: empty/error states, RAL case-study highlight
- Tests: `tests/companies/test_company_detail.py`
- Docs: `docs/plan.md` Task #14 checked

## Verify

- `PYTHONPATH=. pytest -q tests/companies/test_company_detail.py tests/companies/test_listed_companies.py tests/digital_metrics/test_metrics.py` → 31 passed
- `cd frontend && npm run build` → ok

## Task review — #14

### Đã làm được gì
- [x] Profile DN (10 mẫu via list + detail) — done
- [x] Kênh bán số website/Shopee/TikTok + ước lượng online — done (empty state khi thiếu)
- [x] Case study Rạng Đông (RAL) — done
- [x] Timeline crawl + data quality score — done (derived; not append-only pipeline log)
- Deliverable: Module 2 company detail API + UI
- PR: https://github.com/thanhhale288/data-economy/pull/7 · Branch: `cursor/phase4-task14-company-detail` · Tip: `681e610`

### Làm thế nào
- Waves: W1 explore FE/BE → W2 implement → W3 verify → W4 ship
- Subagents: explore BE + FE
- File chính: `backend/app/services/company_service.py`, `backend/app/schemas/__init__.py`, `frontend/src/pages/CompanyDetail.jsx`, `Companies.jsx`, `tests/companies/test_company_detail.py`
- Quyết định: quality/timeline computed from existing rows (no migration / no invented provenance); RAL case study only when ticker=RAL
- Verify: pytest 31 passed; npm build ok

### Còn lại / rủi ro
- Append-only company crawl events / pipeline monitor → Task #15
- Agent Cursor không đọc được macOS keyring của `gh` (terminal user OK) — tạo PR từ terminal
- Phase 3 PR #5 + Task #13 PR #6 still not on `main` — stack PRs

## Do not reopen / do not

- Do not invent CafeF/marketplace/TikTok numbers
- Do not change Digital VA formula
- Do not start Task #15–#17 in the #14 chat
- Leave `.scratch/_local_backup/` untracked
- Ticker **BMP** not BWE

## Next

**Task #15 — Pipeline monitor (Module 3)**  
Branch gợi ý: `cursor/phase4-task15-pipeline-monitor`  
Handoff phase: `.scratch/handoff-phase4.md`

## Paste prompt for next chat

See end of Task #14 chat response.
