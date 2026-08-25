"""Tier-2 LLM extraction — thin wrap of pinned local LLM (T04)."""

from __future__ import annotations

from typing import Any

import httpx

from ml.local_llm import ExtractOutcome, LocalLlmSettings, abstain_result, extract_page


def run_tier2(
    page_text: str,
    *,
    url: str | None = None,
    enabled: bool = True,
    http: httpx.Client | None = None,
    settings: LocalLlmSettings | None = None,
    verify_pin: bool = False,
) -> tuple[dict[str, Any], str, str | None]:
    """Return (ExtractionResult dict, decision, model_id).

    When ``enabled`` is False, abstain the whole record (offline / CI path).
    """
    if not enabled:
        result = abstain_result("tier2_disabled")
        return result.model_dump(mode="json"), "disabled", None

    if not (page_text or "").strip():
        result = abstain_result("empty_page_text")
        return result.model_dump(mode="json"), "abstain", None

    try:
        outcome: ExtractOutcome = extract_page(
            page_text,
            url=url,
            http=http,
            settings=settings,
            verify=verify_pin,
        )
    except Exception as exc:  # noqa: BLE001 — cascade must not invent on LLM failure
        result = abstain_result(f"tier2_error:{type(exc).__name__}")
        return result.model_dump(mode="json"), "abstain", None

    return (
        outcome.result.model_dump(mode="json"),
        outcome.decision,
        outcome.model,
    )
