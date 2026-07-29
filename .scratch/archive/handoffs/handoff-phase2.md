# Handoff — Manufacturing Data Economy (Phase 2)

**Next session focus:** Phase 2 — enterprise crawl & digital detection for the 10 seeded listed companies (metadata, website/checkout, Shopee/TikTok shop finder + listings, structured BCTC where feasible, digital metrics). Do not rewrite Phase 1 macro crawlers unless fixing a proven bug.

**Date:** 2026-07-18  
**Repo:** `/Users/hale/Code/AI in Data Economy`  
**Remote:** `https://github.com/thanhhale288/data-economy`

---

## Where things stand

- **Phase 1 (foundation + macro) is done** and pushed on branch `cursor/phase1-macro-crawlers`.
  - Commits: `62a9054` (implementation), `be9da3e` (plan.md progress update).
  - User was merging / creating PR into `main`. Confirm `main` includes Phase 1 before branching for Phase 2.
- Working tree still has **untracked** noise not part of Phase 1 PR: `.agents/`, `.cursor/`, `.scratch/`, `diagram/`, some docs (docx, needGit, generate script), `skills-lock.json`, `data/mfg_economy.db.bak`. Do not delete user files; do not commit unless asked.
- Local issue tracker pattern: `.scratch/<feature>/` — see `docs/agents/issue-tracker.md`.

## Read first (do not reinvent)

| Doc | Why |
|-----|-----|
| `AGENTS.md` | Stack, layout, boundaries (no invented OECD/GSO numbers; fixed 10 tickers; Digital VA formula lock) |
| `CONTEXT.md` | Ubiquitous language; GSO/OECD source values; peer MEI policy |
| `docs/plan.md` | Roadmap; **Tiến độ thực tế**; Phase 2 checklist; Luồng A/C corrected for NSO |
| `docs/adr/0001-oecd-vietnam-macro-policy.md` | VN-first OECD: GSO primary; INDIGO@VNM; MEI_IP@EA20 peer; annual→monthly **step-hold** |
| `docs/guides/task-02-vsic-mapping-seed.md` | Seed/mapping acceptance (already satisfied) |
| `docs/proposal-v2.md` | Method / formulas source |

## Phase 1 outcomes (verified — reference only)

- **VSIC/seed:** Section C + divisions 10–33 + 10 firms; Alembic schema; idempotent seed (no random macro seed — uses crawlers).
- **GSO/NSO:** IIP monthly SDMX `nsdp.nso.gov.vn/.../IIPVNM.xml`. Shipment `E07.03.px` + inventory `E07.04.px` via `pxweb.nso.gov.vn` API (**annual** at source → step-hold to monthly on ingest). Fallback fixtures under `data/raw/` (gitignored except allowlisted fallbacks).
- **Dead hosts:** `*.gso.gov.vn` industry/px-web often 404/timeout — use `*.nso.gov.vn`.
- **OECD:** INDIGO@VNM live; MEI/BCI/ICT@VNM unavailable (do not fabricate); MEI_IP@EA20 as `OECD_PEER`. `oecd_indicators.source` column exists.
- **Tests:** `tests/gso`, `tests/oecd` (was 33 passed at Phase 1 close).
- **Feature eng:** joins GSO IIP_C + INDIGO@VNM + MEI_IP@EA20 — do not reintroduce fake VNM MEI_BCI.

Code entry points: `crawlers/gso/iip_crawler.py` (`fetch_gso_macro`), `crawlers/gso/pxweb_client.py`, `crawlers/oecd/sdmx_client.py`, `backend/app/seed.py`.

## Phase 2 scope (do this)

Per `docs/plan.md` Giai đoạn 2:

1. Crawl/enrich 10 listed companies (seed already exists): metadata consistency, website.
2. Website detector: ecommerce / checkout signals.
3. Marketplace: Shopee/TikTok (and optionally Lazada) shop find + product scrape; shop-matcher (threshold **0.65** in CONTEXT).
4. BCTC structured fields into `financial_reports` (prefer HTML/XBRL over fragile PDF when possible).
5. Compute per-company digital metrics (online revenue estimate, adoption, etc.) — **do not change Digital VA formula** without CONTEXT + ADR.

Fixed tickers only: RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, BWE. BWE is intentional plastics sample seed (not real HOSE water utility) — see company description / plan.

## Constraints / do not

- Do not invent GSO/OECD numbers; use explicit fallback + provenance.
- Do not touch Digital VA / VDEI formulas without ADR.
- Do not expand beyond the 10 companies.
- Prefer not to rework Phase 1 macro crawlers; shared models/migrations: propose then integrate carefully.
- No commit/push/reset unless user asks.

## Suggested git start for Phase 2

```bash
cd "/Users/hale/Code/AI in Data Economy"
git fetch origin
git checkout main && git pull   # after Phase 1 merge
git checkout -b cursor/phase2-enterprise-digital
```

If Phase 1 not yet on `main`, base the new branch on `cursor/phase1-macro-crawlers` or wait for merge.

## Suggested skills (invoke when relevant)

- `.agents/skills/implement/SKILL.md` — structured implementation
- `.agents/skills/tdd/SKILL.md` — parser/matcher tests first
- `.agents/skills/diagnosing-bugs/SKILL.md` — if crawl/site blocks fail
- `.agents/skills/codebase-design/SKILL.md` — if splitting marketplace matcher seams
- Repo domain: read `docs/agents/domain.md` before inventing terms

## Open risks for Phase 2 (not Phase 1 blockers)

- Marketplace anti-bot / ToS — rate limit, clear fallbacks, no fabricated sales.
- Shop name ↔ company matching needs QA on the 10 firms.
- BCTC PDF quality varies by issuer.

## Paste prompt for the new chat (plain text)

Copy the block below into a new Cursor agent chat:

---
Bạn tiếp tục dự án Manufacturing Data Economy tại /Users/hale/Code/AI in Data Economy.

Đọc handoff: [đường dẫn file handoff bên dưới].
Đọc thêm: AGENTS.md, CONTEXT.md, docs/plan.md (Giai đoạn 2), docs/adr/0001-oecd-vietnam-macro-policy.md.

Phase 1 macro (GSO/NSO + OECD) đã xong — không viết lại trừ bug có chứng cứ.
Nhiệm vụ phiên này: Phase 2 — crawl/enrich 10 DN seed, phát hiện website/checkout, tìm shop Shopee/TikTok + listings, BCTC có cấu trúc nếu được, digital metrics. Giữ đúng 10 ticker. Không đổi công thức Digital VA. Không bịa số liệu crawl.

Bắt đầu bằng: xác nhận main đã có Phase 1, tạo branch cursor/phase2-..., rồi đề xuất thứ tự milestone ngắn trước khi code.
---

