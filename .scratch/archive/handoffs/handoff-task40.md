# Handoff — Task #40 Website domain fix + honesty guard

**Status:** DONE (PR open)  
**Branch:** `cursor/epic3-phase2-task40-website-domain-fix`  
**Date:** 2026-07-27  
**Phase:** Epic 3 Phase 2  
**Commit / PR:** `5f48c26` · PR https://github.com/thanhhale288/data-economy/pull/29  
**Base:** `origin/main` @ `12281cf` (includes Task #39 via PR #26; main later gained #51)

---

## Delivered

- **8/9** failing tickers from audit #33 now `website_ok=true` with verified fetch (SSL verify ON)
- Seed `data/seeds/companies.json`: synced `website_url` + `digital_presence.website.url`; checkout only from live detector
- **GEE** still fail (SSL issuer) — best-known URL `https://gelex-electric.com` + biên bản; audit `has_checkout=unknown`
- Biên bản: `.scratch/epic3-task40-website-domain-fix.md`
- Audit refresh: `.scratch/epic3-task33-website-url-audit.{md,csv}` → **`website_ok=27/28`**
- Plans: `docs/plan.md` + `.scratch/epic3-phase2-plan.md` mark #40 DONE

### URL map (seed after)

| Ticker | New URL | Outcome |
|--------|---------|---------|
| IDI | `https://idiseafood.com` | OK |
| SBT | `https://ttcagris.com.vn` | OK |
| NKG | `https://tonnamkim.com` | OK |
| POM | `http://www.pomina-steel.com` | OK (HTTPS weak key) |
| TLH | `https://www.tienlengroup.vn` | OK (`has_checkout=true`) |
| GEE | `https://gelex-electric.com` | FAIL SSL — unknown checkout |
| DPR | `https://doruco.com.vn` | OK |
| CSV | `https://sochemvn.com` | OK (`has_checkout=true`) |
| DCM | `https://www.pvcfc.com.vn` | OK |

### Not done (out of scope)

- Tasks #41–#50 / #45
- Disable SSL verify / invent checkout/GMV
- Digital VA formula changes
- FE chip “URL chưa verify” (P1 backlog — only GEE left)

---

## Task review — #40 Website domain fix + honesty guard

### Tiến độ
- Ước lượng hoàn thành AC: **100%**
- Status: **DONE**
- Phase · Branch · Tip · PR: Epic 3 Phase 2 · `cursor/epic3-phase2-task40-website-domain-fix` · `5f48c26` · PR #29

### Đã làm được gì (đối chiếu AC)

| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| Mỗi ticker có kết luận URL mới OK **hoặc** biên bản fail | done | 8 OK + GEE biên bản |
| Không suy checkout khi chưa fetch | done | GEE audit `unknown`; TLH/CSV checkout chỉ sau HTTP 200 |
| Không tắt SSL verify | done | POM dùng HTTP official; GEE giữ fail |
| Re-audit so trước/sau | done | 19→**27**/28 `website_ok` |

Deliverable chính:
- Seed domain corrections + Task #40 biên bản + refreshed audit report

### Làm thế nào
- Waves: W1 explore (seed/audit + public domain research) → W2 seed update → W3 live audit + pytest → W4 handoff (no commit)
- Subagents: [Explore seed/audit](1efd0904-8fd6-46a7-b2a7-a2378b8c4e1f), [Explore alt URLs in repo](cfe523d3-7031-465c-a538-df65e655be38)
- File chính: `data/seeds/companies.json`, `.scratch/epic3-task40-website-domain-fix.md`, audit refresh, `docs/plan.md`
- Trade-off: POM **HTTP** (Vietstock-listed) thay vì tắt SSL trên HTTPS weak-key; GEE không bịa “ok”

### Còn lại / rủi ro
- GEE SSL vẫn không verify được — FE chip “URL chưa verify” chỉ còn 1 ticker
- Next priority chain: **#45** (VA Dashboard) → #41 → #46 …

---

## Testing results — Task #40

### Tóm tắt
- Overall: **PASS**
- Ý nghĩa: domain fixes verify live; honesty giữ unknown trên GEE; regression tests xanh

### Lệnh đã chạy

| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | Live httpx probe (9 tickers × candidates, `verify=True`) | domain research | **8 OK / GEE fail** | outside sandbox |
| 2 | `PYTHONPATH=. python3 scripts/audit_website_marketplace.py --no-db` | allowlist 28 | **website_ok=27**, fail=1 (GEE), checkout_unknown=1 | flag_url_mismatch=0 |
| 3 | `PYTHONPATH=. …/pytest -q tests/ -k "website or company or seed" --maxfail=20` | website/company/seed | **61 passed**, 257 deselected | parent `.venv` |

### Failures
- None in pytest
- Expected live: GEE SSL issuer fail (documented)

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| Commit/PR | Done — PR #29 | Merge when green |
| `--fix-db` | No DB sync this chat | Ops / seed re-run |
| FE “URL chưa verify” chip | Backlog P1 | Optional after #40 |

---

## Do not reopen
- Không làm #41–#50 / #45 trong chat Task #40
- Không `verify=False` toàn cục để “cứu” GEE
- Không invent checkout/GMV / đổi Digital VA

## Next
**Task #45 — Dashboard/API M1 hiện VA** (nợ từ #38; chuỗi cân bằng micro↔macro)

Base: tip Task #40 branch (hoặc merge #40 → main trước nếu user ship).

---

## Paste prompt (chat sau)

```text
# Task
Tiếp tục **Epic 3 Phase 2**. Chat này chỉ làm **Task #45 — Dashboard/API M1 hiện VA (nợ từ #38)**. STOP sau #45.

Không làm #41–#44 / #46–#50 trong chat này.
Đang chạy lazy-to-complete: Explore → Implement → Verify → Ship (commit/PR chỉ khi user Explicit yêu cầu).

## Context
Repo: `/Users/hale/Code/AI in Data Economy`

Đọc bắt buộc trước khi code:
- `.scratch/handoff-task40.md` (Task #40 DONE — website_ok 27/28; GEE SSL còn fail)
- `.scratch/handoff-task38.md` (VA_C / VA_C_NOMINAL wired vào gso_macro)
- `.scratch/epic3-task31-grdp-spike.md` § Task #38 (mapping SDMX)
- `docs/plan.md` § Task #45 + Module 1 Dashboard
- `backend/app/services/dashboard_service.py`, Dashboard FE page
- `CONTEXT.md`, `AGENTS.md`

**Ý nghĩa:** #38 đã có series thật `VA_C` (+ optional `VA_C_NOMINAL`) trong `gso_macro`. #45 = **surface** lên Dashboard/API Module 1 — KPI/timeseries; copy tách rõ **VA ngành (macro)** vs **Digital VA mẫu DN** (ADR-0003 / prototype_listed_sample). Không invent số.

**Chuỗi ưu tiên:** `#40` DONE → **`#45`** → `#41` → `#46` → … (đan xen micro ↔ macro).

## Git / branch
1. Base: tip Task #40 `cursor/epic3-phase2-task40-website-domain-fix` (merge/PR #40 nếu user đã ship) hoặc `main` đã có #40.
2. Branch mới: `cursor/epic3-phase2-task45-dashboard-va` (không commit trên `main`).
3. Không commit/push trừ khi user Explicit yêu cầu.
4. Không stage secrets / artifact nặng / file ngoài scope.

## Task #45 — Requirements

### Functional
1. API Dashboard expose `VA_C` timeseries (và optional `VA_C_NOMINAL` nếu đã có trong DB/service) với `source` / thiếu rõ — không silent fill từ IIP.
2. FE Module 1: KPI và/hoặc chart VA; copy/label tách Digital VA (mẫu ~28) vs VA chế biến chế tạo quốc gia.
3. Honesty: thiếu series → empty/missing state; không bịa; không đổi Digital VA formulas.

### AC
- Dashboard/API hiện được `VA_C` khi data có trong `gso_macro`.
- Copy không nhầm VA macro với Digital VA DN.
- Tests dashboard (và FE build nếu đụng UI) pass.

## Constraints
- Một chat = Task #45 only.
- Không GMV (#41), không website (#40), không pipeline features VA (#46), không GRDP tỉnh (#47).

## Waves / Subagents

### W1 — Explore (1–2 subagent song song)
- **A:** dashboard_service / API schema — chỗ IIP vs macro series; gaps cho VA_C.
- **B:** FE Dashboard.jsx — KPI/chart slots; chỗ Digital VA copy.

Deliverable: map file + minimal surface plan (KPI vs chart).

### W2 — Implement
- Wire VA_C (+ optional nominal) API + FE; honesty copy.

### W3 — Verify
```bash
PYTHONPATH=. pytest -q tests/ -k "dashboard or va or gso" --maxfail=20
cd frontend && npm run build
```

### W4 — Ship
Handoff `.scratch/handoff-task45.md` + Task review + Testing results + prompt #41 (có Waves) → STOP.
Không commit trừ khi user bảo.
```
