# Handoff — Task #77 Narrative LLM BASE_URL

**Status:** DONE  
**Branch:** `cursor/epic5-phase4-task77-narrative-llm-base-url`  
**Date:** 2026-08-19  
**Phase:** Epic 5 Phase 4  
**Base:** `origin/main` @ `3772afe`  
**PR:** not opened (commit only; no push)

---

## Đã làm được gì

- Benchmark và forecast narrative không còn POST cứng `https://api.openai.com/v1/chat/completions`.
- URL lấy từ env, thứ tự: per-service `BENCHMARK_NARRATIVE_LLM_BASE_URL` / `FORECAST_NARRATIVE_LLM_BASE_URL` → `NARRATIVE_LLM_BASE_URL` → OpenAI default.
- Host/base (ví dụ Gemini OpenAI-compatible `https://generativelanguage.googleapis.com/v1beta/openai` hoặc `https://api.openai.com/v1`) được nối `/chat/completions`. Endpoint đầy đủ (đã kết thúc `/chat/completions`, kể cả trailing slash) giữ nguyên path.
- Model env giữ như cũ (`BENCHMARK_NARRATIVE_LLM_MODEL` / `FORECAST_NARRATIVE_LLM_MODEL`, default `gpt-4o-mini`).
- Honesty gate không nới: rewrite LLM có số không có trong payload → fallback rules.
- `.env.example` ghi chú các biến (commented, không có secret). `docs/ops-demo.md` không đụng vì file đó chưa document narrative/LLM.

Files:

- `backend/app/services/narrative_llm.py` — resolve URL
- `backend/app/services/benchmark_narrative.py`
- `backend/app/services/forecast_narrative.py`
- `tests/benchmark/test_benchmark_narrative.py`
- `tests/ml/test_forecast_narrative.py`
- `.env.example`

---

## Hạn chế

- Không gọi mạng thật tới OpenAI/Gemini; chỉ cấu hình + test monkeypatch `httpx.post`.
- Live Gemini/OpenAI demo vẫn cần key + BASE_URL trong local `.env` (không copy `.env` vào worktree/commit).
- Không tick `docs/plan.md` / `.scratch/epic5-remain-plan.md`.
- Không đổi Digital VA / VDEI, không bịa số GSO/OECD/CafeF, không log API key.

---

## Testing results

```bash
source /Users/hale/Code/AI in Data Economy/.venv/bin/activate
cd /Users/hale/Code/AI in Data Economy/.worktrees/t77
PYTHONPATH=. pytest -q tests/benchmark/ -k narrative
# 10 passed, 69 deselected
PYTHONPATH=. pytest -q tests/ml/ -k narrative
# 11 passed, 51 deselected
```

Cả hai lệnh **PASS**. Không live HTTP.
