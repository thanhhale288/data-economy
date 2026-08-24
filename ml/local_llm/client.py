"""Ollama chat client: pinned model, JSON schema, retry, then abstain."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import httpx

from ml.local_llm.schema import (
    ExtractionResult,
    abstain_result,
    extraction_json_schema,
    parse_extraction,
)

PACKAGE_DIR = Path(__file__).resolve().parent
PIN_PATH = PACKAGE_DIR / "pin.json"
PROMPT_PATH = PACKAGE_DIR / "prompts" / "extract_vi.txt"
DEFAULT_TIMEOUT = 180.0
MAX_ATTEMPTS = 3  # 1 initial + 2 repairs
REPAIR_USER = (
    "Output valid JSON only matching the schema. No markdown, no extra keys."
)
Decision = Literal["ok", "retry_ok", "abstain"]


class PinMismatchError(RuntimeError):
    """Runtime model digest does not match the pinned research digest."""


@dataclass(frozen=True)
class LocalLlmSettings:
    base_url: str
    model: str
    digest: str
    temperature: float
    seed: int
    think: bool
    ollama_version_min: str

    @classmethod
    def from_pin_and_env(cls, pin: dict[str, Any] | None = None) -> LocalLlmSettings:
        pin = pin if pin is not None else load_pin()
        return cls(
            base_url=_env("LOCAL_LLM_BASE_URL", str(pin["default_base_url"])).rstrip("/"),
            model=_env("LOCAL_LLM_MODEL", str(pin["model"])),
            digest=_env("LOCAL_LLM_MODEL_DIGEST", str(pin["digest"])),
            temperature=float(pin.get("temperature", 0)),
            seed=int(pin.get("seed", 42)),
            think=bool(pin.get("think", False)),
            ollama_version_min=str(pin.get("ollama_version_min", "")),
        )


@dataclass
class ExtractOutcome:
    decision: Decision
    result: ExtractionResult
    model: str
    digest: str | None
    attempts: int
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    eval_duration_ns: int | None = None
    total_duration_ns: int | None = None
    load_duration_ns: int | None = None
    raw_content: str | None = None
    error: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "result": self.result.model_dump(mode="json"),
            "model": self.model,
            "digest": self.digest,
            "attempts": self.attempts,
            "prompt_eval_count": self.prompt_eval_count,
            "eval_count": self.eval_count,
            "eval_duration_ns": self.eval_duration_ns,
            "total_duration_ns": self.total_duration_ns,
            "load_duration_ns": self.load_duration_ns,
            "error": self.error,
        }


def load_pin(path: Path | None = None) -> dict[str, Any]:
    target = path or PIN_PATH
    return json.loads(target.read_text(encoding="utf-8"))


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def prompt_sha256() -> str:
    import hashlib

    return hashlib.sha256(PROMPT_PATH.read_bytes()).hexdigest()


def schema_sha256() -> str:
    import hashlib

    blob = json.dumps(extraction_json_schema(), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def verify_pin(
    http: httpx.Client,
    settings: LocalLlmSettings,
) -> dict[str, Any]:
    """Confirm the lab is serving the pinned digest. Fail loud on mismatch."""
    tags = http.get("/api/tags")
    tags.raise_for_status()
    models = (tags.json() or {}).get("models") or []
    match = next((row for row in models if str(row.get("name") or "") == settings.model), None)
    if match is None:
        names = [str(r.get("name")) for r in models]
        raise PinMismatchError(
            f"Pinned model {settings.model!r} not on server. Available: {names}"
        )
    runtime = _normalize_digest(str(match.get("digest") or ""))
    expected = _normalize_digest(settings.digest)
    if runtime != expected:
        raise PinMismatchError(
            f"Digest mismatch for {settings.model}: runtime={runtime} pinned={expected}"
        )
    version = None
    try:
        ver = http.get("/api/version")
        if ver.is_success:
            version = (ver.json() or {}).get("version")
    except httpx.HTTPError:
        version = None
    return {
        "model": settings.model,
        "digest": runtime,
        "ollama_version": version,
        "quantization": (match.get("details") or {}).get("quantization_level"),
        "parameter_size": (match.get("details") or {}).get("parameter_size"),
    }



def list_running(http: httpx.Client) -> list[dict[str, Any]]:
    try:
        resp = http.get("/api/ps")
        resp.raise_for_status()
        return list((resp.json() or {}).get("models") or [])
    except httpx.HTTPError:
        return []


def extract_page(
    page_text: str,
    *,
    url: str | None = None,
    http: httpx.Client | None = None,
    settings: LocalLlmSettings | None = None,
    verify: bool = False,
) -> ExtractOutcome:
    """Classify one page. Invalid JSON is retried, then the whole record abstains."""
    cfg = settings or LocalLlmSettings.from_pin_and_env()
    owns = http is None
    client = http or httpx.Client(base_url=cfg.base_url, timeout=DEFAULT_TIMEOUT)
    try:
        runtime_digest = None
        if verify:
            info = verify_pin(client, cfg)
            runtime_digest = str(info["digest"])
        last_raw = None
        last_err = "empty_response"
        last_stats: dict[str, Any] = {}
        for attempt in range(1, MAX_ATTEMPTS + 1):
            raw, stats = _chat(client, cfg, page_text, url=url, repair=attempt > 1)
            last_raw = raw
            last_stats = stats
            parsed = _try_parse(raw)
            if parsed is not None:
                decision: Decision = "ok" if attempt == 1 else "retry_ok"
                return _outcome(
                    decision=decision,
                    result=parsed,
                    cfg=cfg,
                    digest=runtime_digest,
                    attempts=attempt,
                    stats=stats,
                    raw=raw,
                )
            last_err = "invalid_json_or_schema"
        return _outcome(
            decision="abstain",
            result=abstain_result("schema_invalid_after_retry"),
            cfg=cfg,
            digest=runtime_digest,
            attempts=MAX_ATTEMPTS,
            stats=last_stats,
            raw=last_raw,
            error=last_err,
        )
    finally:
        if owns:
            client.close()


def _chat(
    http: httpx.Client,
    cfg: LocalLlmSettings,
    page_text: str,
    *,
    url: str | None,
    repair: bool,
) -> tuple[str, dict[str, Any]]:
    user_parts = []
    if url:
        user_parts.append(f"URL: {url}")
    body = (page_text or "").strip() or "(empty page)"
    user_parts.append("PAGE TEXT:")
    user_parts.append(body)
    if repair:
        user_parts.append(REPAIR_USER)
    schema = extraction_json_schema()
    payload = {
        "model": cfg.model,
        "stream": False,
        "think": cfg.think,
        "format": schema,
        "options": {
            "temperature": cfg.temperature,
            "seed": cfg.seed,
        },
        "messages": [
            {"role": "system", "content": load_prompt()},
            {"role": "user", "content": "\n".join(user_parts)},
        ],
    }
    resp = http.post("/api/chat", json=payload)
    resp.raise_for_status()
    data = resp.json()
    content = ((data.get("message") or {}).get("content")) or ""
    stats = {
        "prompt_eval_count": data.get("prompt_eval_count"),
        "eval_count": data.get("eval_count"),
        "eval_duration_ns": data.get("eval_duration"),
        "total_duration_ns": data.get("total_duration"),
        "load_duration_ns": data.get("load_duration"),
    }
    return str(content), stats


def _try_parse(raw: str) -> ExtractionResult | None:
    text = (raw or "").strip()
    if not text:
        return None
    if text.startswith("```"):
        text = _strip_fence(text)
    try:
        return parse_extraction(text)
    except Exception:
        pass
    try:
        obj = json.loads(text)
        return ExtractionResult.model_validate(obj)
    except Exception:
        return None


def _strip_fence(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _outcome(
    *,
    decision: Decision,
    result: ExtractionResult,
    cfg: LocalLlmSettings,
    digest: str | None,
    attempts: int,
    stats: dict[str, Any],
    raw: str | None,
    error: str | None = None,
) -> ExtractOutcome:
    return ExtractOutcome(
        decision=decision,
        result=result,
        model=cfg.model,
        digest=digest,
        attempts=attempts,
        prompt_eval_count=_as_int(stats.get("prompt_eval_count")),
        eval_count=_as_int(stats.get("eval_count")),
        eval_duration_ns=_as_int(stats.get("eval_duration_ns")),
        total_duration_ns=_as_int(stats.get("total_duration_ns")),
        load_duration_ns=_as_int(stats.get("load_duration_ns")),
        raw_content=raw,
        error=error,
    )


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_digest(value: str) -> str:
    text = value.strip().lower()
    if text.startswith("sha256:"):
        return text.split(":", 1)[1]
    return text


def _env(name: str, default: str) -> str:
    raw = (os.environ.get(name) or "").strip()
    return raw if raw else default
