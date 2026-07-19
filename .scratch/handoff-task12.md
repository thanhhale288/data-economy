# Handoff — Manufacturing Data Economy (Task #12)

**Next session focus:** Phase 3 **Task #12 — ML models** only. Do not reopen #10/#11 unless fixing a proven bug. Do not start Phase 4 dashboards unless user asks after #12 acceptance.

**Date:** 2026-07-19  
**Repo:** `/Users/hale/Code/AI in Data Economy`  
**Remote:** `https://github.com/thanhhale288/data-economy`  
**Branch:** `cursor/phase3-clean-features-ml` (Tasks #10 + #11)

---

## Where things stand

### Done
- **Phase 1 + 2** on `main` (PR #1, PR #2).
- **Task #10 cleaning** — `cleaned_macro.parquet`, `cleaned_marketplace.parquet`, `cleaning_report.json`; job `data_cleaning`.
- **Task #11 features** — `pipeline/features/*` (digital/financial/macro_helpers/validation + glue `engineering.py`); `data/processed/features.parquet` + `features_manifest.json`; `tests/features` (16 passed). Seed migrates legacy **BWE → BMP**.
- Persistence: Phase 3 = **parquet** under `data/processed/`; staging Postgres → Module 3–4 only.

### Do not rewrite
- Cleaning (#10), feature modules (#11), GSO/OECD crawlers, Digital VA formula — unless proven bug.

### Local caveats
- `mei_ip` may still be missing if OECD peer EA20 not in DB/clean (`series_missing`). Do **not** invent; refresh OECD crawl with `include_peers=True` if needed.
- Digital/financial on the monthly frame may be `broadcast_latest` / `step_hold_*` — see manifest notes; not fake monthly observations.
- Tickers: **BMP** not BWE. Leave `.scratch/_local_backup/` untracked.

---

## Read first

`AGENTS.md`, `CONTEXT.md`, `docs/plan.md` (§4.2–4.3 + GĐ3), `docs/adr/0001-oecd-vietnam-macro-policy.md`, `.cursor/skills/project-roadmap/SKILL.md` (task 12), `.cursor/skills/github-workflow/SKILL.md` (commit/PR), `docs/guides/task-12-ml-models.md`, `ml/models/trainer.py`, `ml/evaluation/`, `pipeline/features/engineering.py`, `data/processed/features_manifest.json`.

---

## Task #12 scope

Train & evaluate **ARIMA/SARIMAX**, **XGBoost/LightGBM**, **LSTM** on GSO **IIP_C** target; metrics **MAE/RMSE/MAPE**; prefer **walk-forward** over a single naive split; persist artifacts under `data/models/` (gitignored binaries OK); **model registry** + API endpoints for ML Lab later. Read features from `build_features` / `features.parquet` — do not invent feature columns.

Current `ml/models/trainer.py` is a scaffold (EMA stand-in for ARIMA, simple holdout, short LSTM). Replace with real training + honest eval; no fabricated metrics.

---

## Suggested skills

`project-roadmap`, `tdd`, `codebase-design`, `github-workflow` (when committing), domain docs.

---

## Paste prompt for new chat

```
Bạn tiếp tục dự án Manufacturing Data Economy tại /Users/hale/Code/AI in Data Economy.

Đọc handoff: .scratch/handoff-task12.md
Đọc thêm: AGENTS.md, CONTEXT.md, docs/plan.md (§4.2–4.3 + Giai đoạn 3), docs/adr/0001-oecd-vietnam-macro-policy.md, .cursor/skills/project-roadmap/SKILL.md (task 12), docs/guides/task-12-ml-models.md, ml/models/trainer.py, pipeline/features/engineering.py, data/processed/features_manifest.json.

Phase 1–2 DONE. Task #10 cleaning + Task #11 features DONE trên branch cursor/phase3-clean-features-ml. Không viết lại clean/features trừ bug có chứng cứ.

Persistence: features từ data/processed/features.parquet (hoặc build_features). Không overwrite raw GSO/OECD. Không bịa số / không bịa metrics. Digital VA không đổi. Ticker BMP (không BWE). Không MEI_BCI giả; MEI_IP chỉ peer EA20 nếu có trong features.

Nhiệm vụ phiên này: Task #12 — ML models (ARIMA/SARIMAX, XGBoost/LightGBM, LSTM; MAE/RMSE/MAPE; walk-forward; registry + API). Không làm Phase 4 dashboard trừ khi user yêu cầu sau #12.

Bắt đầu bằng: checkout/pull cursor/phase3-clean-features-ml, xác nhận features.parquet / trainer hiện trạng, đề xuất milestone ngắn rồi hỏi guide vs implement.
```
