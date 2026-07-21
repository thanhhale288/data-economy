# Handoff — Benchmark BITE Expenditure UI (Phase 5)

**Status:** COMMITTED · prefill bugfix included · **chưa push/PR**  
**Date:** 2026-07-20  
**Branch:** `cursor/phase5-benchmark-bite-expenditure`  
**Commits:**
- `79aa88f` — Add SingStat-style BITE expenditure ratios to Phase 5 benchmark UI.
- `aefede0` — Fix benchmark prefill to prefer complete annual BCTC over CafeF quarterlies.

**Base:** tip `main` (có Task #18/#19a)  
**Repo:** `/Users/hale/Code/AI in Data Economy`

---

## Task review

### Tiến độ
- AC expenditure (form Of which + donut + Key Expenditure + honesty N/A + tests + docs): **DONE + committed**
- Prefill RAL 404 (CafeF quarterly thiếu employees đè annual): **FIXED + committed**
- Push/PR: **chưa** (cần user xác nhận)
- OMP hygiene (`OMP_NUM_THREADS=1` trong Makefile/`main.py`): **chưa** (Wave optional)

### Đã làm (chat commit)
1. Stage đúng “Files to commit”; không đụng economy-knowledge / .agents/skills / data/models|processed
2. Commit expenditure UI + docs + tests
3. Diagnose API log: OECD/Shopee UNAVAILABLE = fallback OK; **prefill 404** = bug chọn `max(period)` trên quý CafeF
4. Fix `_latest_annual_report` + prefill prefer complete annual; regression test; verify live `GET /api/benchmark/prefill/RAL` → 200; compare `ind_exp≈0.85`

### Chưa làm (debt → chat sau)
- Push + `gh pr create` base `main` (nếu user bảo)
- `export OMP_NUM_THREADS=1` trong `Makefile` `api` / `backend/app/main.py`
- Header / breadcrumb / Industry context (roadmap Wave A)
- Componentize `frontend/src/components/benchmark/*`

---

## Testing results

| Lệnh | Kết quả |
|------|---------|
| `PYTHONPATH=. pytest -q tests/benchmark/` | **16 passed** (thêm `test_prefill_skips_incomplete_newer_quarterly`) |
| Live `GET /api/benchmark/prefill/RAL` (sau reload) | **200** + full Of-which fields |
| Live `POST /api/benchmark/compare` (RAL payload) | firm_exp ≈ 0.865, ind_exp ≈ 0.8504, peer_count=2 |

### Ops note
API đang chạy với `OMP_NUM_THREADS=1` (session này). Log OECD 404 / Shopee anti-bot **không** làm FE crash — chỉ fallback. Prefill 404 mới là blocker Benchmark form.

```bash
export PYTHONPATH=. OMP_NUM_THREADS=1
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
# FE: http://localhost:5173/benchmark
```

---

## Next chat prompt (paste)

```markdown
# Task
Push + mở PR Benchmark BITE Expenditure (branch `cursor/phase5-benchmark-bite-expenditure` → `main`), rồi làm ops hygiene `OMP_NUM_THREADS=1` cho `make api` / startup.

## Context
Repo: `/Users/hale/Code/AI in Data Economy`  
Branch: `cursor/phase5-benchmark-bite-expenditure` (2 commits ahead origin)  
Handoff: `.scratch/handoff-benchmark-bite-expenditure.md`  
Commits: `79aa88f` expenditure UI · `aefede0` prefill annual fix  
Verdict: committed + prefill RAL 200 verified locally; **chưa push/PR**; OMP chưa ghi vào Makefile/main.

## Constraints
- Không commit economy-knowledge, .agents/skills/*, data/models|processed.
- Không invent GSO/OECD/peer numbers.
- Một task: PR + OMP hygiene only.

## Waves
### Wave 1 — Push + PR
1. `git status` / `git log origin/main..HEAD`
2. `git push -u origin HEAD`
3. `gh pr create` base `main` (summary + test plan từ handoff)

### Wave 2 — OMP hygiene
1. `export OMP_NUM_THREADS=1` trong Makefile `api` target và/hoặc early in `backend/app/main.py`.
2. Verify: Dashboard ML forecast không treo worker; `GET /api/benchmark/prefill/RAL` vẫn 200 nhanh.

## Acceptance
- [ ] PR URL
- [ ] CI xanh (hoặc note đang chạy)
- [ ] OMP set trong make api / startup
- [ ] Prefill RAL vẫn 200 sau restart qua `make api`
```
