# ADR-0004: Local open-weights LLM via lab Ollama

## Status

Accepted — 2026-08-24

## Context

Proposal-v4 requires research numbers from **open-weights** models on GPU lab:
pinned version, temperature 0, structured JSON, reproducible prompts. The optional
narrative polish path (`BENCHMARK_NARRATIVE_LLM_*` / OpenAI / Gemini) must never
feed published OBEC-style indicators.

Lab already exposes Ollama 0.17.4 at `https://research.neu.edu.vn/ollama` with
instruct models on disk (including `qwen3:8b`). Building a second serving stack
(vLLM) is unnecessary for Evol-1 T04.

## Decision

1. **Serving:** use the lab Ollama HTTP API (`/api/chat`, `/api/tags`, `/api/version`).
   Client lives in `ml/local_llm/` (httpx only). Do not add a hard dependency on
   the `ollama` Python package or on closed cloud APIs for research outputs.
2. **Pin:** default model `qwen3:8b` with digest recorded in
   `ml/local_llm/pin.json`. Runtime digest must match; mismatch fails the run.
   Override via `LOCAL_LLM_BASE_URL` / `LOCAL_LLM_MODEL` / `LOCAL_LLM_MODEL_DIGEST`.
3. **Inference contract:** `temperature=0`, fixed `seed`, `think=false` (required
   for Qwen3 structured output), JSON Schema in Ollama `format`, max 2 repair
   retries, then **whole-record abstain** (no invented fields).
4. **Scope:** T04 proves infrastructure (10-page smoke + pages/hour). Precision /
   recall is T06. Extraction cascade over the pilot frame is T05.
5. **Forbidden for paper numbers:** OpenAI, Gemini, or any unpinned closed API —
   including the narrative polish helpers.

## Consequences

- T03/T05 can call `ml.local_llm.extract_page` without reinventing transport.
- Throughput (`pages_per_hour_*` in `data/processed/local_llm/run_manifest.json`)
  is a **shared-GPU snapshot**, not a SLA.
- Serving may later switch to vLLM if the OpenAI-compatible client surface stays
  stable; the pin + schema + prompt hashes remain the reproducibility unit.

## Advisor briefing (3 sentences)

Hạ tầng AI tái lập được: model `qwen3:8b` (digest ghim trong `pin.json`) chạy trên
Ollama lab NEU, temperature 0, JSON schema + quyền abstain. Smoke 10 trang
homepage DN niêm yết ghi tốc độ trang/giờ và log tham số — chi phí ~0. Đây chưa
phải số P/R nghiên cứu; T05/T06 mới đo chất lượng chỉ tiêu.
