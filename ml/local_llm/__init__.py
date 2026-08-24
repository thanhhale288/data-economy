"""Local open-weights LLM client for research measurement (Evol-1 T04).

Numbers that go into papers must come from a pinned Ollama model, not the
optional narrative polish APIs (OpenAI/Gemini).
"""

from __future__ import annotations

from ml.local_llm.client import (
    ExtractOutcome,
    LocalLlmSettings,
    PinMismatchError,
    extract_page,
    load_pin,
    verify_pin,
)
from ml.local_llm.schema import ExtractionResult, abstain_result

__all__ = [
    "ExtractOutcome",
    "ExtractionResult",
    "LocalLlmSettings",
    "PinMismatchError",
    "abstain_result",
    "extract_page",
    "load_pin",
    "verify_pin",
]
