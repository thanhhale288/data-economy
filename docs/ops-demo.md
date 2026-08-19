# Ops — Demo runbook

Short operator notes for local demo. Formulas and series honesty: `CONTEXT.md`. Full Quick Start: [README](../README.md).

## Onboarding a new listed company (Epic 2)

```bash
PYTHONPATH=. python scripts/onboard_company.py \
  --code XYZ --name "Công ty ..." --vsic 2410 \
  --website https://example.com --enrich
```

**QA checklist:** `GET /api/companies/XYZ`; VSIC peers on detail; website detect không invent checkout; optional Pipeline companies batch + metrics.

Allowlist = stock codes in `data/seeds/companies.json`.

## Digital presence honesty (Epic 3)

- `digital_channels.shopee|tiktok|lazada=true` **chỉ** khi có URL trong `digital_presence`.
- Marketplace crawl: live → seed → fallback; `marketplace_listings.source` ∈ `live|seed|fallback`.
- Industry-ratio online revenue: **không** bật silent ratio (Tasks #30/#37 still `None`) — xem `.scratch/epic3-task30-industry-ratio-research.md`.

## CafeF BCTC enrich (Epic 3 Task #32)

Smoke + upsert `financial_reports` from CafeF quarterly HTML for the seed allowlist (~28). Missing fields (e.g. employees) stay `null` — not backfilled from seed demo.

```bash
# Full allowlist (needs DB seeded + network). Writes .scratch/epic3-task32-cafef-bctc-report.{md,csv}
PYTHONPATH=. python scripts/enrich_bctc_cafef.py

# Subset / dry-run (no DB write)
PYTHONPATH=. python scripts/enrich_bctc_cafef.py --tickers RAL,BMP,HPG --dry-run
```

Report columns: `ticker | status (cafef_ok|fallback|error) | detail | period | source_url`. Company detail API exposes `financial_reports[].source_url` (`cafef` URL vs `seed:companies.json`).

## Website + marketplace URL audit (Epic 3 Task #33)

Batch `detect_website` over the seed allowlist (~28) and list Shopee/TikTok/Lazada URLs from seed/`digital_presence`. HTTP 403/timeout → `website_ok=false`, `has_checkout=unknown` — never invent checkout.

**Chỗ xem URL:** `data/seeds/companies.json` (`digital_presence[].url`) · report `.scratch/epic3-task33-website-url-audit.{md,csv}` · Company detail (chip Website + bảng Kênh bán số).

```bash
# Full allowlist + live detect (needs network). Writes .scratch/epic3-task33-website-url-audit.{md,csv}
PYTHONPATH=. python scripts/audit_website_marketplace.py

# Offline seed/DB consistency only
PYTHONPATH=. python scripts/audit_website_marketplace.py --no-detect

# Sync DB digital_presence URLs to seed when drifted (e.g. missing Shopee row)
PYTHONPATH=. python scripts/audit_website_marketplace.py --fix-db --no-detect
```

Report columns: `stock_code | website_ok | has_checkout | shopee_url | tiktok_url | flag_vs_url_mismatch`. Exit code 3 if any marketplace flag lacks a URL.

## Listing depth (Epic 3 Task #34)

**Mẫu niêm yết (~28)** ≠ **mẫu có shop TMĐT** ≠ **mẫu có listing GMV**.

| Sample | Meaning |
|--------|---------|
| Niêm yết | Seed allowlist |
| Có shop TMĐT | Shopee/TikTok/Lazada URL trong seed/`digital_presence` |
| Có listing | ≥1 `marketplace_listings` (kể cả website catalog, units null) |
| Có GMV | Listing có cả `price` và `units_sold_est` → đóng góp online revenue |

Chỉ thêm listing khi live scrape `source=live` **hoặc** curation có PROVENANCE
(`data/raw/marketplace_listings_fallback.PROVENANCE.md`). Peer B2B không shop → `[]`.

```bash
# Seed coverage + live smoke (needs network). Writes .scratch/epic3-task34-listing-depth.{md,csv}
PYTHONPATH=. python scripts/enrich_marketplace_listings.py

# Offline seed coverage only
PYTHONPATH=. python scripts/enrich_marketplace_listings.py --no-live

# Persist via crawl upsert (live→seed→fallback); never invents units on block
PYTHONPATH=. python scripts/enrich_marketplace_listings.py --persist-db
```

DQC (sau #34): curated **website** catalog rows từ `dienquang.com` — `units_sold_est=null`
→ online revenue vẫn 0 cho đến khi live Shopee OK.

## Marketplace live strategy (Epic 3 Task #35)

**ADR:** [`docs/adr/0002-marketplace-live-strategy.md`](adr/0002-marketplace-live-strategy.md)

| Option | Role |
|--------|------|
| Allowlist + cache + badge `live\|seed\|fallback` | **Default** — `data/raw/marketplace_live_cache/` (RAL×shopee, VNM×tiktok) |
| Session cookie (`SHOPEE_SESSION_COOKIE` / `TIKTOK_SESSION_COOKIE`) | **Optional ops** — manual login; never commit secrets |
| Partner API | Spike only — no full implement without contract |
| Anti-bot SaaS | **Rejected** as đồ án default |

Crawl when live attempted: HTTP → on 403/block, allowlisted cache (`source=live`,
provenance `live:cache:…`) → seed → fallback. Never invent units/GMV.

```bash
# Demo-stable: prefer cache before HTTP (no invent)
PYTHONPATH=. python scripts/enrich_marketplace_listings.py --prefer-cache --tickers RAL,VNM

# Live HTTP then cache-on-fail (default when not --no-cache)
PYTHONPATH=. python scripts/enrich_marketplace_listings.py --tickers RAL,VNM,FPT
```

### Session cookie ops smoke (Epic 3 Task #42)

Set cookies in local `.env` only (names in `.env.example`). Never commit or paste values into `.scratch/`.

```bash
# Presence check (prints yes/no only — do not echo cookie strings)
PYTHONPATH=. python -c "import os; from dotenv import load_dotenv; load_dotenv();
print('SHOPEE', 'yes' if os.getenv('SHOPEE_SESSION_COOKIE','').strip() else 'no');
print('TIKTOK', 'yes' if os.getenv('TIKTOK_SESSION_COOKIE','').strip() else 'no')"

# True live HTTP (no cache mask) — expect block/403 if anti-bot still active
PYTHONPATH=. python scripts/enrich_marketplace_listings.py --tickers RAL,VNM --no-cache

# Ops default: HTTP then allowlisted cache
PYTHONPATH=. python scripts/enrich_marketplace_listings.py --tickers RAL,VNM
```

**2026-07-27 smoke:** cookies `present=yes` for both; live HTTP still anti-bot/403 (`live_ok=0` with `--no-cache`); cache-on-fail `live_ok=2`. Biên bản: `.scratch/epic3-task42-cookie-ops-smoke.md`. Partner API spike (no implement): `.scratch/epic3-task42-partner-api-spike.md`.

Company detail listing table shows badge **Nguồn** = `live` | `seed` | `fallback`.

## Matcher discovery gate (Epic 3 Task #36 / #43)

Marketplace **shop discovery** (non-seed search) is **OFF by default**. Crawl only links seed known URLs that pass ShopMatcher ≥ **0.65**.

To enable controlled discovery (ops/QA only):

```bash
export MARKETPLACE_DISCOVERY_ENABLED=1
# optional override; default 0.65
export MARKETPLACE_DISCOVERY_THRESHOLD=0.65
# Edit data/mappings/discovery_allowlist.json — add {ticker, channel_type, url}
# Empty entries[] ⇒ no discovered shops even when enabled
```

Ticker không có shop trong seed vẫn **unlinked** trừ khi có entry QA allowlist + score ≥ 0.65. Không invent shop/GMV.

**Task #43 — search path + fuzzy hygiene:**

- Code: `search_marketplace_shop_candidates(query, channel=…)` → parse-only candidates; `candidates_to_qa_allowlist_entries` formats rows for **manual** QA promote. Never auto-links; still requires flag + allowlist via `discover_shops_for_company`.
- **Live search (2026-07-27):** Shopee/TikTok search HTTP **blocked** (anti-bot) — biên bản `.scratch/epic3-task43-discovery-crawl.md`. Same class as #42 cookie listing smoke.
- Fuzzy: token containment min length **5** + noise `dong` — DPR no longer false-matches `rangdong_official`.
- Pipeline: `resolve_shop_to_company(..., discovery_gated=True)` respects the same gate (no bypass).

Ops smoke (injected allowlist, keep committed `entries: []`):

```bash
export MARKETPLACE_DISCOVERY_ENABLED=1
PYTHONPATH=. python -c "
from backend.app.models import Company
from crawlers.marketplace.shop_finder import discover_shops_for_company
ral = Company(stock_code='RAL', name='Công ty Cổ phần Bóng đèn Rạng Đông', vsic_code='2740', exchange='HOSE')
print(discover_shops_for_company(ral, enabled=True, allowlist=[{
  'ticker':'RAL','channel_type':'shopee','url':'https://shopee.vn/rangdong_official'}])[0]['match_source'])
"
# → qa_discovery
unset MARKETPLACE_DISCOVERY_ENABLED
```

## Feedback alias harvest (Epic 5 Task #79)

JSONL field diffs → markdown/JSON **proposals** only. Does **not** patch `_LABEL_ALIASES`. See `PYTHONPATH=. python scripts/harvest_feedback_aliases.py --help`.

```bash
PYTHONPATH=. python scripts/harvest_feedback_aliases.py \
  --input tests/benchmark/fixtures/feedback_alias_harvest.jsonl \
  --markdown-out /tmp/feedback-alias-harvest.md
```

## Bootstrap (recommended)


```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Postgres URL matching docker compose
make bootstrap         # or: ./scripts/bootstrap.sh
make api               # terminal 1
make fe                # terminal 2
```

**Database path (pick one and stay consistent):**

| Path | How |
|------|-----|
| **Postgres (recommended)** | `docker compose up -d db redis` + `.env` from `.env.example` (`DATABASE_URL=postgresql://mfg_economy:…@localhost:5432/mfg_economy`) |
| **SQLite** | No `.env` (or `DATABASE_URL=sqlite:///./data/mfg_economy.db`); skip compose db |

Redis is started by compose but **not required** for seed, cleaning, features, or training. Crawl/seed need the DB you chose.

**Phase 3 order** (same as `pipeline/dags/scheduler.py` after crawls):

1. `compute_all_digital_metrics`
2. `run_data_cleaning` → `data/processed/cleaned_macro.parquet` (+ marketplace parquet / report)
3. `run_feature_engineering` → `data/processed/features.parquet` + `features_manifest.json`
4. `train_all_models` → `data/models/*`

`scripts/bootstrap.sh` sets `OMP_NUM_THREADS=1` by default (XGBoost OpenMP can segfault on some macOS setups otherwise).

Do **not** skip cleaning/features before train. Do **not** invent GSO/OECD/CafeF numbers when crawl fails — use explicit fallback and surface status in the UI.

## LightGBM train + monitoring (Epic 5 Task #71)

`train_all_models` already fits LightGBM on the same IIP feature frame as XGBoost (target stays `iip`; never switched to VA). `GET /api/ml/monitoring` always lists **lightgbm** with arima / xgboost / lstm. Untrained → metrics `null` + `registry_missing` / `artifact_missing` — no invented MAPE.

Soft-fail if the `lightgbm` package is missing (`status=unavailable`); do not install darts.

**Train on local DB** (API up, or script; after seed + clean + features):

```bash
# HTTP — same trainer as the Pipeline job `ml_training`
curl -sS -X POST http://localhost:8000/api/ml/train

# CLI wrapper
./run.sh train

# Direct trainer (writes data/models/lightgbm_model.joblib + lightgbm_importance.json)
PYTHONPATH=. python -c "
from backend.app.database import SessionLocal
from ml.models.trainer import train_all_models
db = SessionLocal()
print(train_all_models(db))
db.close()
"
```

Nightly worker (`PYTHONPATH=. python -m pipeline.dags.scheduler`) runs `ml_training` → `train_all_models` after `feature_engineering`.

**Do not commit** `data/models/*.pt` or LightGBM/XGBoost `.joblib` binaries from a local train. Artifacts are machine-generated; gitignore covers `*.pt` and LightGBM joblib names.

## Refresh ML drift baseline (Epic 5 Task #72)

`GET /api/ml/monitoring` computes drift only when `data/models/ml_monitoring_baseline.json` exists. Missing file → `drift_flag` / `drift_score` stay **null** (no invented drift).

After a retrain that meets the quality bar, refresh the baseline from **ModelRegistry MAPE** (never type numbers by hand):

```bash
# Preview — does not write
PYTHONPATH=. python scripts/write_ml_monitoring_baseline.py --dry-run

# Write data/models/ml_monitoring_baseline.json from the latest registry row per canonical model
PYTHONPATH=. python scripts/write_ml_monitoring_baseline.py
```

The writer includes only models whose latest registry row has a real numeric `mape`. Untrained models (for example LightGBM with `registry_missing`) are omitted. If the registry is empty or unreachable, the script prints a warning, exits non-zero, and does **not** write a file — so you cannot overwrite a good baseline with zeros.

Point it at a specific DB without copying `.env` into a worktree:

```bash
PYTHONPATH=. python scripts/write_ml_monitoring_baseline.py --database-url "$DATABASE_URL"
```

JSON baseline is committable **only** when values came from the registry. Do not invent MAPE in the file or in this doc.

## PaddleOCR extra (Epic 5 Task #69)

**Decision:** default is **lazy-load** PaddleOCR on first scanned PDF/image extract. The Docker image **does not** install `requirements-ocr.txt` (`backend/Dockerfile` copies only `requirements.txt`). Do **not** bake OCR into the image unless an operator explicitly asks in a later task.

Code path: `backend/app/services/bctc_extract_ocr.py` — `paddleocr_available()` ImportError → warnings `ocr_unavailable` + `no_extractable_fields`; `_ocr_engine()` is an `lru_cache` singleton, models under `~/.paddlex`. Extract field formulas are unchanged.

### Without the extra (default demo / CI)

`POST /api/benchmark/extract` still accepts scan PDFs and images. The OCR path returns all fields `null` plus those warnings — it does **not** invent numbers.

Frontend (Task #66, `frontend/src/extractWarningCopy.js`) maps `ocr_unavailable` to:

> Máy chủ chưa có OCR. Dùng nạp CafeF (prefill) hoặc PDF chữ chọn được (selectable text) — bản scan sẽ để form trống.

**Workaround:** nạp CafeF (prefill) on the Benchmark form, or upload a selectable-text PDF. Scan-only files stay empty.

### Install extra (local operator only)

```bash
source .venv/bin/activate
pip install -r requirements-ocr.txt
```

PaddlePaddle CPU wheels use the vendor index documented in `requirements-ocr.txt`:

```bash
pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
pip install paddleocr==3.7.0
```

Not part of default CI (`pip install -r requirements.txt` only). Do not add this extra to `backend/Dockerfile`.

Smoke after install:

```bash
python -c "from paddleocr import PaddleOCR; print('ok')"
```

### Env and first init

- `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK` — `_ocr_engine()` already `os.environ.setdefault(..., "True")`. Setting it in `.env` is optional.
- First engine init is **slow** and needs network: models download to `~/.paddlex`. **Do not commit** that directory or model binaries.
- Later extracts in the same process reuse the singleton.

### pytest

OCR integration tests are marked `ocr` (`pytest.ini`) and use `pytest.importorskip("paddleocr")`. Default CI `pytest -q` skips them when the extra is missing.

```bash
# Default CI / machines without PaddleOCR
PYTHONPATH=. pytest -q
PYTHONPATH=. pytest -q -m "not ocr"

# Only after pip install -r requirements-ocr.txt (first run downloads ~/.paddlex)
PYTHONPATH=. pytest -q -m ocr
```

Do **not** change extract formulas to work around a missing extra.


## Online vs offline

| Mode | What happens |
|------|----------------|
| **Online** | Seed/crawl need HTTP: NSO/GSO, OECD SDMX, CafeF (and marketplace where configured). Failures must record status/detail — no silent fake series. |
| **Offline** | Use `data/raw/` fixtures / sourced fallbacks already in the repo. UI and Pipeline/ML surfaces must show **fallback / unavailable**, not invent values. |

**API smoke** (API must be up — **not** one-shot with bootstrap):

```bash
make api    # terminal 1 — required
make smoke  # terminal 2 — scripts/smoke_demo.sh
```

On macOS, smoke may probe **arima** for forecast while Dashboard prefers **xgboost** (OpenMP crash risk). See `.scratch/demo-smoke-checklist.md`.

**Offline E2E** (pytest fixtures, no live API): `make e2e` → `PYTHONPATH=. pytest -q tests/e2e/`.

**UI:** one manual browser pass — script does not replace visual empty-states (checklist §4).

## Nightly worker

```bash
PYTHONPATH=. python -m pipeline.dags.scheduler
```

Runs crawls then metrics → cleaning → features → train (see `pipeline/dags/scheduler.py`). Compose service `worker` uses the same entrypoint.

## Branch / merge caveat

Phase 4 (#13–#18) may be merged in the **stack** (`cursor/phase4-task18-benchmark`) but not yet on `main`. For demo:

1. `git fetch origin && git checkout cursor/phase5-task19-demo-ops` (or task18 tip), **or**
2. After stack PR merges to `main`, `git checkout main && git pull`.

Bootstrap does not pull branches. See `.scratch/demo-smoke-checklist.md`.
