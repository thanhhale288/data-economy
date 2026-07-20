#!/usr/bin/env bash
# Demo smoke — API contracts for Task #19 (no business-logic changes).
# Prerequisites: stack up + seed/bootstrap (see .scratch/demo-smoke-checklist.md).
#
# Usage:
#   API_BASE=http://localhost:8000 bash scripts/smoke_demo.sh
#
# Exit non-zero when /health is down or hard API contracts break.
# Soft/empty states (no IIP, untrained ML) are reported as NOTES, not failures.

set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
API_BASE="${API_BASE%/}"

PASS=0
FAIL=0
NOTES=()

red() { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
info() { printf '  %s\n' "$*"; }

ok() {
  PASS=$((PASS + 1))
  green "PASS  $*"
}

fail() {
  FAIL=$((FAIL + 1))
  red "FAIL  $*"
}

note() {
  NOTES+=("$*")
  yellow "NOTE  $*"
}

# GET/POST helpers: write body to $BODY_FILE, echo HTTP status on stdout.
BODY_FILE="$(mktemp)"
trap 'rm -f "$BODY_FILE"' EXIT

http_get() {
  local url="$1"
  local code
  local max_t="${2:-15}"
  # curl -w still prints 000 on transport errors; do not append a second 000 via ||.
  code="$(curl -sS -o "$BODY_FILE" -w '%{http_code}' --connect-timeout 3 --max-time "$max_t" "$url" 2>/dev/null || true)"
  if [[ -z "$code" ]]; then
    echo "000"
  else
    echo "$code"
  fi
}

http_post_json() {
  local url="$1"
  local json="$2"
  local code
  local max_t="${3:-45}"
  code="$(curl -sS -o "$BODY_FILE" -w '%{http_code}' --connect-timeout 3 --max-time "$max_t" \
    -H 'Content-Type: application/json' \
    -X POST -d "$json" "$url" 2>/dev/null || true)"
  if [[ -z "$code" ]]; then
    echo "000"
  else
    echo "$code"
  fi
}

py() {
  # Usage: py BODY_FILE 'python expression using data'
  # For statements, use py_exec instead.
  python3 - "$1" "$2" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
expr = sys.argv[2]
data = json.loads(path.read_text(encoding="utf-8"))
print(eval(expr, {"data": data, "json": json}))
PY
}

py_exec() {
  # Usage: py_exec BODY_FILE <<'EOF' ... set out=... EOF
  # Reads Python statements from stdin; prints ns["out"].
  local path="$1"
  local code
  code="$(cat)"
  CODE="$code" python3 - "$path" <<'PY'
import json, os, sys
from pathlib import Path

path = Path(sys.argv[1])
code = os.environ["CODE"]
data = json.loads(path.read_text(encoding="utf-8"))
ns = {"data": data, "json": json, "out": ""}
exec(code, ns)
print(ns.get("out", ""))
PY
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    red "Missing required command: $1"
    exit 1
  }
}

need_cmd curl
need_cmd python3

echo "=== Demo smoke against ${API_BASE} ==="
echo

# ---------------------------------------------------------------------------
# 1. GET /health — hard fail if dead
# ---------------------------------------------------------------------------
echo "[1/7] Health"
code="$(http_get "${API_BASE}/health" 8)"
if [[ "$code" != "200" ]]; then
  fail "GET /health → HTTP ${code} (API down or unreachable)"
  echo
  red "Aborting: health check failed. Start API (uvicorn) then re-run."
  exit 1
fi
if ! status="$(py "$BODY_FILE" 'data.get("status")' 2>/dev/null)"; then
  fail "GET /health → 200 but body is not JSON"
  exit 1
fi
if [[ "$status" != "ok" ]]; then
  fail "GET /health status='${status}' (expected ok)"
  exit 1
fi
ok "GET /health → status=ok"

# ---------------------------------------------------------------------------
# 2. Dashboard: IIP + forecast after bootstrap OR honest empty/untrained
# ---------------------------------------------------------------------------
echo
echo "[2/7] Dashboard (IIP + forecast contract)"
code="$(http_get "${API_BASE}/api/dashboard/summary")"
if [[ "$code" != "200" ]]; then
  fail "GET /api/dashboard/summary → HTTP ${code}"
else
  ok "GET /api/dashboard/summary → 200"
fi

iip_latest="$(py "$BODY_FILE" 'data.get("iip_latest")')"
pref_model="$(py "$BODY_FILE" 'data.get("preferred_forecast_model")')"
n_metrics="$(py "$BODY_FILE" 'len(data.get("model_metrics") or {})')"
metric_names="$(py "$BODY_FILE" '",".join((data.get("model_metrics") or {}).keys())')"

code="$(http_get "${API_BASE}/api/dashboard/iip?vsic_code=C")"
if [[ "$code" != "200" ]]; then
  fail "GET /api/dashboard/iip → HTTP ${code}"
else
  iip_n="$(py "$BODY_FILE" 'len(data) if isinstance(data, list) else -1')"
  if [[ "$iip_n" -lt 0 ]]; then
    fail "GET /api/dashboard/iip body is not a list"
  elif [[ "$iip_n" -eq 0 ]]; then
    note "IIP series empty — UI should show empty-state (không bịa). Seed/crawl GSO if demo needs chart."
    ok "GET /api/dashboard/iip → 200 (empty OK)"
  else
    ok "GET /api/dashboard/iip → 200 (${iip_n} points)"
  fi
fi

# Forecast probe: use preferred_forecast_model; if preferred is xgboost and arima
# is registered, smoke calls arima (macOS XGB OpenMP can crash the worker —
# same caution as tests/e2e). Dashboard UI still uses preferred.
model="${pref_model:-xgboost}"
if [[ "$model" == "None" || -z "$model" ]]; then
  model="xgboost"
fi
if [[ "$model" == "xgboost" && ",${metric_names}," == *",arima,"* ]]; then
  note "Smoke forecast uses arima (preferred=${model}; avoids XGB OpenMP crash risk)."
  model="arima"
fi
code="$(http_post_json "${API_BASE}/api/ml/forecast" "{\"model_name\":\"${model}\",\"horizon_months\":6}")"
if [[ "$code" == "200" ]]; then
  n_fc="$(py "$BODY_FILE" 'len(data.get("forecasts") or [])')"
  if [[ "$n_fc" -ge 1 ]]; then
    ok "POST /api/ml/forecast (${model}) → ${n_fc} points"
  else
    fail "POST /api/ml/forecast 200 but forecasts empty"
  fi
elif [[ "$code" == "404" ]]; then
  note "Forecast artifact missing for «${model}» — Dashboard banner empty/untrained (honest)."
  ok "POST /api/ml/forecast → 404 untrained (contract OK)"
elif [[ "$code" == "400" ]]; then
  note "Forecast 400: $(py "$BODY_FILE" 'str(data.get("detail", data))[:200]')"
  ok "POST /api/ml/forecast → 400 (no invented series)"
elif [[ "$code" == "000" ]]; then
  fail "POST /api/ml/forecast → transport error (server down/crash?). Re-check /health."
else
  fail "POST /api/ml/forecast → HTTP ${code}"
fi

if [[ "$iip_latest" != "None" && -n "$iip_latest" && "$n_metrics" != "0" ]]; then
  info "summary: iip_latest=${iip_latest}, model_metrics=${n_metrics}, preferred=${pref_model}"
fi

# ---------------------------------------------------------------------------
# 3. Company RAL detail
# ---------------------------------------------------------------------------
echo
echo "[3/7] Company RAL"
code="$(http_get "${API_BASE}/api/companies/RAL")"
if [[ "$code" != "200" ]]; then
  fail "GET /api/companies/RAL → HTTP ${code}"
else
  stock="$(py "$BODY_FILE" 'data.get("stock_code")')"
  if [[ "$stock" != "RAL" ]]; then
    fail "RAL detail stock_code='${stock}'"
  else
    name="$(py "$BODY_FILE" 'data.get("name") or ""')"
    ok "GET /api/companies/RAL → 200 (${name})"
  fi
fi

# ---------------------------------------------------------------------------
# 4. Pipeline trigger + status
# ---------------------------------------------------------------------------
echo
echo "[4/7] Pipeline trigger + status"
# Lightweight trigger id accepted by API (background task; we only need job row + status).
code="$(http_post_json "${API_BASE}/api/pipeline/trigger" '{"crawler":"metrics"}')"
job_id=""
if [[ "$code" != "200" ]]; then
  fail "POST /api/pipeline/trigger → HTTP ${code}"
else
  job_id="$(py "$BODY_FILE" 'data.get("id")')"
  job_name="$(py "$BODY_FILE" 'data.get("job_name")')"
  job_status="$(py "$BODY_FILE" 'data.get("status")')"
  if [[ -z "$job_id" || "$job_id" == "None" ]]; then
    fail "trigger response missing job id"
  else
    ok "POST /api/pipeline/trigger → job id=${job_id} name=${job_name} status=${job_status}"
  fi
fi

code="$(http_get "${API_BASE}/api/pipeline/status")"
if [[ "$code" != "200" ]]; then
  fail "GET /api/pipeline/status → HTTP ${code}"
else
  listed="$(py "$BODY_FILE" 'data.get("jobs_listed")')"
  ok "GET /api/pipeline/status → 200 (jobs_listed=${listed})"
fi

code="$(http_get "${API_BASE}/api/pipeline/jobs")"
if [[ "$code" != "200" ]]; then
  fail "GET /api/pipeline/jobs → HTTP ${code}"
else
  n_jobs="$(py "$BODY_FILE" 'len(data) if isinstance(data, list) else -1')"
  if [[ "$n_jobs" -lt 1 ]]; then
    fail "pipeline/jobs empty after trigger"
  else
    ok "GET /api/pipeline/jobs → 200 (${n_jobs} jobs)"
  fi
fi

# ---------------------------------------------------------------------------
# 5. ML Lab: MAE / RMSE / MAPE from registry
# ---------------------------------------------------------------------------
echo
echo "[5/7] ML Lab registry metrics"
code="$(http_get "${API_BASE}/api/ml/models")"
if [[ "$code" != "200" ]]; then
  fail "GET /api/ml/models → HTTP ${code}"
else
  n_models="$(py "$BODY_FILE" 'len(data) if isinstance(data, list) else -1')"
  if [[ "$n_models" -eq 0 ]]; then
    note "Model registry empty — train via Pipeline/ML Lab before demo metrics slide."
    ok "GET /api/ml/models → 200 (empty registry OK)"
  else
    # Every registered model must expose metrics object with mae/rmse/mape keys
    # (values may be null if training recorded failure — never invent numbers).
    bad="$(py_exec "$BODY_FILE" <<'EOF'
bad = []
for m in data:
    name = m.get("model_name", "?")
    metrics = m.get("metrics")
    if metrics is None or not isinstance(metrics, dict):
        bad.append(f"{name}:metrics_missing")
        continue
    for k in ("mae", "rmse", "mape"):
        if k not in metrics:
            bad.append(f"{name}:missing_{k}")
out = "|".join(bad)
EOF
)"
    if [[ -n "$bad" ]]; then
      fail "registry metrics contract broken: ${bad}"
    else
      names="$(py "$BODY_FILE" '",".join(m.get("model_name","?") for m in data)')"
      ok "GET /api/ml/models → ${n_models} model(s) with mae/rmse/mape keys (${names})"
    fi
  fi
fi

# ---------------------------------------------------------------------------
# 6. Benchmark: RAL prefill + insufficient_peers honesty
# ---------------------------------------------------------------------------
echo
echo "[6/7] Benchmark prefill + insufficient_peers"
code="$(http_get "${API_BASE}/api/benchmark/prefill/RAL")"
if [[ "$code" != "200" ]]; then
  fail "GET /api/benchmark/prefill/RAL → HTTP ${code} (bootstrap should seed RAL BCTC)"
else
  pcode="$(py "$BODY_FILE" 'data.get("stock_code")')"
  if [[ "$pcode" != "RAL" ]]; then
    fail "prefill stock_code='${pcode}'"
  else
    ok "GET /api/benchmark/prefill/RAL → 200"
  fi
fi

# VSIC 1100 → division 11 has no seeded peers → insufficient_peers, null percentiles (never fake 50).
# Note: 3290 is division 32 (PNJ 3211) and is NOT a zero-peer case.
code="$(http_post_json "${API_BASE}/api/benchmark/compare" '{
  "vsic_code": "1100",
  "operating_revenue": 1e12,
  "profit_before_tax": 1e11,
  "employees": 100,
  "total_assets": 2e12,
  "total_equity": 1e12,
  "current_assets": 8e11,
  "current_liabilities": 4e11
}')"
if [[ "$code" != "200" ]]; then
  fail "POST /api/benchmark/compare (vsic 1100) → HTTP ${code}"
else
  check="$(py_exec "$BODY_FILE" <<'EOF'
peer = data.get("peer_count")
warn = data.get("warnings") or []
pcts = data.get("percentiles") or {}
comp = data.get("comparison") or {}
errs = []
if peer != 0:
    errs.append(f"peer_count={peer}")
if "insufficient_peers" not in warn:
    errs.append("missing_warning")
for k, v in pcts.items():
    if v is not None:
        errs.append(f"percentile_{k}={v}")
    if v == 50:
        errs.append(f"fake_50_{k}")
for k, v in comp.items():
    if v == "insufficient_peers":
        continue
    if pcts.get(k) is None and v not in ("insufficient_peers",):
        errs.append(f"comparison_{k}={v}")
out = "|".join(errs) if errs else "ok"
EOF
)"
  if [[ "$check" != "ok" ]]; then
    fail "insufficient_peers honesty broken: ${check}"
  else
    ok "POST /api/benchmark/compare → insufficient_peers, null percentiles (no fake 50)"
  fi
fi

# ---------------------------------------------------------------------------
# 7. Online vs offline / fallback signals (observable; informational)
# ---------------------------------------------------------------------------
echo
echo "[7/7] Online vs offline / fallback notes"
code="$(http_get "${API_BASE}/api/dashboard/oecd-vs-gso")"
if [[ "$code" == "200" ]]; then
  oecd_st="$(py "$BODY_FILE" 'data.get("oecd_status")')"
  oecd_note="$(py "$BODY_FILE" '(data.get("oecd_note") or "")[:160]')"
  note "OECD peer status=${oecd_st} — ${oecd_note}"
else
  fail "GET /api/dashboard/oecd-vs-gso → HTTP ${code}"
fi

code="$(http_get "${API_BASE}/api/pipeline/quality")"
if [[ "$code" == "200" ]]; then
  avail="$(py "$BODY_FILE" 'data.get("available")')"
  msg="$(py "$BODY_FILE" '(data.get("message") or "")[:160]')"
  note "cleaning quality available=${avail}${msg:+ — $msg}"
else
  fail "GET /api/pipeline/quality → HTTP ${code}"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo
echo "=== Results: ${PASS} passed, ${FAIL} failed, ${#NOTES[@]} notes ==="
if [[ ${#NOTES[@]} -gt 0 ]]; then
  echo "Notes (manual UI / demo narration):"
  for n in "${NOTES[@]}"; do
    info "- $n"
  done
fi
echo
echo "Manual UI checks: .scratch/demo-smoke-checklist.md"

if [[ "$FAIL" -gt 0 ]]; then
  red "SMOKE FAILED"
  exit 1
fi
green "SMOKE OK"
exit 0
