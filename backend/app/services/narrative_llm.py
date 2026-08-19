"""OpenAI-compatible chat-completions URL for optional narrative LLM polish.

Gemini and other OpenAI-compatible hosts work at config level via BASE_URL env
vars — no live network is required to resolve the endpoint.
"""

from __future__ import annotations

import os

DEFAULT_NARRATIVE_LLM_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
_SHARED_BASE_URL_ENV = "NARRATIVE_LLM_BASE_URL"
_COMPLETIONS_PATH = "/chat/completions"


def resolve_narrative_llm_completions_url(service_env: str) -> str:
    """Resolve the chat-completions URL for a narrative service.

    Precedence: non-empty ``service_env`` → ``NARRATIVE_LLM_BASE_URL`` → OpenAI default.

    A value that already ends with ``/chat/completions`` (or is clearly that full
    endpoint, including a query string) is used as-is after stripping a trailing
    slash. A host/base such as ``https://api.openai.com/v1`` or
    ``https://generativelanguage.googleapis.com/v1beta/openai`` is joined with
    ``/chat/completions``.
    """
    raw = (os.environ.get(service_env) or "").strip()
    if not raw:
        raw = (os.environ.get(_SHARED_BASE_URL_ENV) or "").strip()
    if not raw:
        return DEFAULT_NARRATIVE_LLM_COMPLETIONS_URL
    return _normalize_completions_url(raw)


def _normalize_completions_url(raw: str) -> str:
    path_part, sep, query = raw.partition("?")
    path_stripped = path_part.rstrip("/")
    lower_path = path_stripped.lower()
    if lower_path.endswith(_COMPLETIONS_PATH) or _COMPLETIONS_PATH in lower_path:
        # Full endpoint: keep path (and query); drop only a trailing slash on the path.
        return f"{path_stripped}{sep}{query}" if sep else path_stripped
    return f"{path_stripped}{_COMPLETIONS_PATH}{sep}{query}" if sep else f"{path_stripped}{_COMPLETIONS_PATH}"
