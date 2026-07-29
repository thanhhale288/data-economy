# Handoff — Epic 3 Phase 1 (Data honesty & plumbing)

**Branch:** `cursor/epic3-data-first` (local `main` đã ff-merge Epic 2 trước đó)  
**Status:** Phase 1 DONE locally (chưa bắt buộc đã push/PR)  
**Date:** 2026-07-25  
**Plan gốc Phase 1:** Tasks #25–#31 (parity / provenance / gate)  
**Phase 2:** xem mục “Next” + [`docs/plan.md`](../docs/plan.md) § Epic 3 Phase 2 + plan `.cursor/plans` / `.scratch/epic3-phase2-*.md`

---

## Mục tiêu Phase 1 (đã chọn)

Sau Epic 2 (product-first: mẫu ~28 + UX/ops), Phase 1 **không** cố chứng minh GMV/BCTC “thị trường thật” trên mọi DN. Mục tiêu là:

1. Làm **trung thực** đường dữ liệu (seed/fallback đủ 28, provenance, không invent).  
2. Mở **hook** live (CafeF path, Playwright follow-up, `source` trên listing).  
3. **Gate** industry-ratio / GRDP khi chưa có nguồn — ghi biên bản thay vì silent fill.

Số trong seed annual **vẫn là demo** nếu CafeF/live không chạy thành công — Phase 2 mới ưu tiên số thật.

---

## Delivered (#25–#31) — làm được gì

| Task | Làm được | Ý nghĩa cho bạn |
|------|----------|-----------------|
| **#25** | `companies_bctc_fallback.json` = **28** ticker sync từ seed; BMP null giữ; PROVENANCE + tests | Offline/CI không chết; **không** đồng nghĩa CafeF đã smoke thành công |
| **#26** | MSN bỏ tiktok ảo; DQC thêm Shopee URL; test flag ⇒ phải có DP URL; ops checklist | Seed consistency; **chưa** batch HTTP detector cả 28 |
| **#27** | Cột `marketplace_listings.source` + alembic; fallback 28; `source_health` marketplace | Biết listing từ live/seed/fallback; listing GMV vẫn ~5 brand |
| **#28** | Playwright sau httpx HTML; test **mock**; block→seed | Code sẵn; **chưa** chứng minh ≥1 ticker `source=live` ngoài đời |
| **#29** | Alias DQC + tests; noise `dien` chống FP REE↔DQC | Matcher cho DN **có shop**; không discovery toàn sàn |
| **#30** | Research: không có ratio CBCT đáng tin → `SOURCED_INDUSTRY_ECOMMERCE_RATIO=None` | Online = Σ listing hoặc 0; không ×0.15 |
| **#31** | GRDP spike = deferred; plan/economy-knowledge/handoff | M1 vẫn IIP + shipment/inventory |

### Chỗ xem nhanh (self-check)

```bash
# BCTC fallback đủ 28
python3 -c "import json; print(len(json.load(open('data/raw/companies_bctc_fallback.json'))))"

# Mọi URL marketplace trong seed
python3 - <<'PY'
import json
from pathlib import Path
for c in json.loads(Path("data/seeds/companies.json").read_text()):
    for d in c.get("digital_presence", []):
        if d.get("channel_type") in ("shopee", "tiktok", "lazada"):
            print(c["stock_code"], d["channel_type"], d["url"])
PY

PYTHONPATH=. pytest -q \
  tests/financial/test_epic3_bctc_parity.py \
  tests/companies/test_epic3_digital_honesty.py \
  tests/marketplace/ \
  tests/shop_matcher/ \
  tests/digital_metrics/
```

**Marketplace DP hiện có:** RAL, VNM, FPT, MSN, PNJ, DQC (DQC chưa có listing GMV).  
**22 ticker còn lại:** không có shop seed — đúng cho nhiều DN B2B, không phải “quên nửa mẫu 10”.

---

## Chưa làm / cố ý để Phase 2 (từ thắc mắc của bạn)

| Chủ đề | Phase 1 dừng ở đâu | Vì sao | Phase 2 sẽ làm gì |
|--------|-------------------|--------|-------------------|
| **Số BCTC thật** | Seed/fallback demo; CafeF có trong code nhưng **chưa smoke live cả 28** | AC Phase 1 = parity + không invent; live phụ thuộc mạng/HTML | #32 enrich CafeF (rồi annual/XBRL nếu cần) → DB `source_url` thật; seed chỉ còn lưới demo |
| **Batch website / QA URL** | Chỉ sửa lệch seed đã biết; test consistency | Không HTTP thật trong chat | #33 batch detector + báo cáo URL/checkout; audit provenance tay |
| **Listing ít (~5 brand)** | Không bịa price/units cho peer | 10 DN mẫu ≠ 10 DN có TMĐT | #34 chỉ thêm listing khi live OK hoặc curation có nguồn |
| **Live Shopee/TikTok** | Playwright + contract fallback | Anti-bot/captcha | #35 chiến lược: allowlist+cache / session / API — không dựa scrape làm sự thật ngành |
| **Matcher “cả 28”** | Chỉ brand có shop | Alias DN không shop → FP | #36 không bắt buộc discovery; mở rộng khi có URL mới |
| **Industry-ratio** | `None` + research note | Không có tỷ trọng TMĐT/doanh thu CBCT | #37 wire **chỉ** khi có citation trong `data/mappings/` |
| **GRDP/VA** | Deferred | Chưa table NSO xác nhận | #38 crawl chỉ khi có table ID |
| **Scale trăm / toàn Section C** | Ngoài Phase 1 | Mẫu niêm yết ≠ vũ trụ ngành | #39 kiến trúc vũ trụ DN (đăng ký/thống kê) + micro nông vs mẫu sâu |

Biên bản Phase 1:

- `.scratch/epic3-task30-industry-ratio-research.md`  
- `.scratch/epic3-task31-grdp-spike.md`

---

## Nguyên tắc giữ sang Phase 2

- Không invent GSO/OECD/CafeF/GMV/GRDP.  
- Không đổi Digital VA/VDEI (cần ADR).  
- Seed demo ≠ số hiển thị “đã crawl thật” — UI/health phải phân biệt `cafef|seed|fallback|live`.  
- Một chat = một task (lazy-to-complete).

---

## Git / verify Phase 1

```bash
git checkout cursor/epic3-data-first
git status -sb
# Commit/PR khi user yêu cầu — đừng commit docx lạ / secrets
```

---

## Next — Epic 3 Phase 2 (paste prompt)

```text
Đang chạy skill lazy-to-complete-workflow — Epic 3 Phase 2, Task #32 only.

Đọc:
- .scratch/handoff-epic3-phase1-data.md  (Phase 1 đóng)
- docs/plan.md § Epic 3 Phase 2
- CONTEXT.md, AGENTS.md

Base: merge/PR tip Phase 1 (`cursor/epic3-data-first`) vào main nếu chưa; branch `cursor/epic3-phase2-task32-cafef-live-bctc`.

Task #32 — CafeF live enrich → số BCTC thật trên allowlist ~28:
- Smoke CafeF ngoài sandbox (mạng thật) cho full allowlist; ghi status ok|fallback từng ticker.
- Persist financial_reports với source_url CafeF khi parse OK; field thiếu (employees…) = null, không lấp seed.
- Script/ops: một lệnh enrich batch + bảng báo cáo (ticker, status, period, source).
- Không invent; không đổi Digital VA.
- Tests: mock CafeF ok + network fail → fallback; optional live skip nếu block.

## Waves / Subagents
- W1 Explore: cafef.py / bctc_crawler / enrich path / seed vs DB
- W2 Implement: batch enrich + report + docs ops
- W3 Verify: pytest financial + smoke 3–5 ticker live (ghi kết quả)
- W4 Ship: commit/PR + handoff-task32 + prompt Task #33

STOP sau Task #32.
```
