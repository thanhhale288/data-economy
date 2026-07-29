# Handoff — Manufacturing Data Economy (Phase 3)

**Next session focus:** Phase 3 — Clean, Features & ML (roadmap tasks 10–12): cleaning pipeline/DAGs, feature engineering, train+evaluate ARIMA / XGBoost|LightGBM / LSTM, model registry + API. Prefer demo-ready IIP forecasts; do not rewrite Phase 1 macro or Phase 2 enterprise crawlers unless fixing a proven bug.

**Date:** 2026-07-19  
**Repo:** `/Users/hale/Code/AI in Data Economy`  
**Remote:** `https://github.com/thanhhale288/data-economy`

---

## Where things stand

### Phase 1 — DONE on `main`
- Merged via PR #1 → `410f373`.
- GSO/NSO IIP + PX-Web shipment/inventory; OECD INDIGO@VNM + MEI_IP@EA20 peer; ADR-0001.

### Phase 2 — DONE (demo) on branch `cursor/phase2-enterprise-digital`
- Tip commit: `eeb7fba` (pushed to `origin/cursor/phase2-enterprise-digital`).
- PR into `main` may not be opened yet — confirm merge status before branching Phase 3.
- Details / caveats: `docs/plan.md` § Tiến độ thực tế + Giai đoạn 2; `.scratch/phase2/STATUS.md`, `.scratch/phase2/checklist.md`, `.scratch/phase2/phase2-final-acceptance.md`.

### Phase 2 accepted scope (do not reopen unless asked)
- Tickers: RAL, HPG, VNM, FPT, GVR, DGC, MSN, PNJ, REE, **BMP** (Nhựa Bình Minh; **not** BWE/Biwase).
- BCTC live = **CafeF quarterly** HTML (`crawlers/financial/cafef.py`). HOSE/PDF annual → later.
- Marketplace live Shopee/TikTok → **deferred** (scaffold + seed/fallback only).
- Digital metrics: Digital VA formula locked in CONTEXT; no listing → online_revenue **0** (no invented ×0.15); industry-ratio sourced → later.
- Shop-matcher: fuzzy ≥ 0.65 in `ml/shop_matcher/` (not full TF-IDF classifier).

### Working tree notes
- `diagram/drawio-ai-kit/` intentionally gitignored (nested git clone).
- `*.db.bak` gitignored.
- Local `.scratch/` has Phase 2 wave reports (committed).

---

## Read first (do not reinvent)

| Doc | Why |
|-----|-----|
| `AGENTS.md` | Stack, 10 tickers, no invent GSO/OECD, Digital VA lock |
| `CONTEXT.md` | Domain language; ARIMA/XGBoost/LSTM; Digital VA |
| `docs/plan.md` | Phase 3 bullets; features list; ML eval |
| `docs/adr/0001-oecd-vietnam-macro-policy.md` | No fake VNM MEI; INDIGO step-hold; EA20 peer |
| `.cursor/skills/project-roadmap/SKILL.md` | Tasks **10–12** sequential backlog |
| `pipeline/features/engineering.py` | Existing feature join (IIP + INDIGO + MEI_IP@EA20) |
| `pipeline/dags/scheduler.py` | Job wiring scaffold |
| `ml/` | Model folders — train not production-ready yet |

---

## Phase 3 scope (do this)

Per roadmap + plan:

1. **Task 10 — Cleaning pipeline** — missing values, outliers (IQR/Z-score), entity resolution, VSIC mapping; DAGs (Prefect/Airflow or extend existing scheduler). *Blocked by:* Phase 2 metrics + OECD (done).
2. **Task 11 — Feature engineering** — lag/rolling IIP + OECD + digital/financial features; no fake MEI_BCI. *Blocked by:* 10.
3. **Task 12 — ML models** — train & evaluate ARIMA/SARIMAX, XGBoost/LightGBM, LSTM; MAE/RMSE/MAPE, walk-forward; model registry + API. *Blocked by:* 11.

Target: forecast **GSO IIP Section C** (primary), using real macro + available micro features.

---

## Constraints / do not

- Do not invent GSO/OECD/CafeF/marketplace numbers.
- Do not change Digital VA formula without CONTEXT + ADR.
- Do not expand beyond 10 tickers (BMP not BWE).
- Do not reopen Phase 2 marketplace live / HOSE PDF unless user asks.
- Prefer not to rewrite Phase 1 GSO/OECD crawlers.
- No commit/push/reset unless user asks.

---

## Suggested git start for Phase 3

```bash
cd "/Users/hale/Code/AI in Data Economy"
git fetch origin
# If Phase 2 PR merged into main:
git checkout main && git pull
git checkout -b cursor/phase3-clean-features-ml
# If Phase 2 not merged yet, base on phase2 branch instead:
# git checkout cursor/phase2-enterprise-digital && git pull
# git checkout -b cursor/phase3-clean-features-ml
```

---

## Suggested skills

- `.agents/skills/implement/SKILL.md` — structured implementation
- `.agents/skills/tdd/SKILL.md` — cleaning/feature/model tests first
- `.agents/skills/codebase-design/SKILL.md` — seams for clean → features → train
- `.cursor/skills/project-roadmap/SKILL.md` — confirm task 10 as current
- `.agents/skills/diagnosing-bugs/SKILL.md` — if training/pipeline fails
- Domain: `docs/agents/domain.md` before inventing metric names

---

## Open risks for Phase 3

- Sparse digital features (many firms online_revenue=0) — models must tolerate missing/zero digital inputs; do not invent.
- CafeF BCTC is quarterly → align feature frequency with monthly IIP carefully.
- LSTM/data length may be short for deep models — document limits; keep ARIMA/XGBoost solid.
- Scheduler already scaffolds crawls — cleaning/train jobs need clear provenance + pipeline_jobs rows.

---

## Paste prompt for the new chat (plain text)

Copy the block below into a new Cursor agent chat:

---
Bạn tiếp tục dự án Manufacturing Data Economy tại /Users/hale/Code/AI in Data Economy.

Đọc handoff: [đường dẫn file handoff bên dưới / hoặc .scratch/handoff-phase3.md nếu đã copy vào repo].
Đọc thêm: AGENTS.md, CONTEXT.md, docs/plan.md (Giai đoạn 3), docs/adr/0001-oecd-vietnam-macro-policy.md, .cursor/skills/project-roadmap/SKILL.md (task 10–12).

Phase 1 + Phase 2 (demo) đã xong — không viết lại GSO/OECD / enterprise crawl trừ bug có chứng cứ.
Phase 2 caveat: BCTC = CafeF quý; marketplace live hoãn; ticker BMP (không BWE); Digital VA không đổi.

Nhiệm vụ phiên này: Phase 3 — cleaning pipeline, feature engineering, train/evaluate ARIMA + XGBoost/LightGBM + LSTM cho IIP Section C, model registry + API. Không bịa số liệu.

Bắt đầu bằng: xác nhận main đã có Phase 2 (hoặc base đúng branch), tạo branch cursor/phase3-..., rồi đề xuất thứ tự milestone ngắn (task 10→11→12) trước khi code.
---

