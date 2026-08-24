"""One-firm and batch cascade: fetch → tier1 rules → tier2 LLM → compare."""

from __future__ import annotations

from typing import Any

import httpx

from crawlers.extraction_cascade.compare import compare_tiers
from crawlers.extraction_cascade.fetch import fetch_page
from crawlers.extraction_cascade.schema import (
    CohortSource,
    FirmCascadeResult,
    RenderedPage,
    Tier1Indicators,
)
from crawlers.extraction_cascade.tier1_rules import analyze_page_rules
from crawlers.extraction_cascade.tier2_llm import run_tier2
from ml.local_llm import LocalLlmSettings
from ml.local_llm.client import prompt_sha256


def run_on_page(
    *,
    firm_id: str,
    source_cohort: CohortSource,
    website_url: str,
    page: RenderedPage,
    locale: str = "vi",
    llm_enabled: bool = True,
    http_llm: httpx.Client | None = None,
    llm_settings: LocalLlmSettings | None = None,
    verify_pin: bool = False,
) -> FirmCascadeResult:
    if not page.ok:
        return FirmCascadeResult(
            firm_id=firm_id,
            source_cohort=source_cohort,
            website_url=website_url,
            fetch_ok=False,
            fetch_detail=page.detail,
            tier1=None,
            tier2=None,
            tier2_decision=None,
            conflicts=compare_tiers(firm_id, None, None, fetch_ok=False),
        )

    tier1: Tier1Indicators = analyze_page_rules(
        page.html,
        base_url=page.final_url or website_url,
        locale=locale,
    )
    tier2_dict, decision, model_id = run_tier2(
        page.text,
        url=page.final_url or website_url,
        enabled=llm_enabled,
        http=http_llm,
        settings=llm_settings,
        verify_pin=verify_pin,
    )
    conflicts = compare_tiers(firm_id, tier1, tier2_dict, fetch_ok=True)
    prompt_ver = None
    if llm_enabled and decision != "disabled":
        try:
            prompt_ver = prompt_sha256()[:12]
        except OSError:
            prompt_ver = None
    return FirmCascadeResult(
        firm_id=firm_id,
        source_cohort=source_cohort,
        website_url=website_url,
        fetch_ok=True,
        fetch_detail=page.detail,
        tier1=tier1,
        tier2=tier2_dict,
        tier2_decision=decision,
        conflicts=conflicts,
        model_id=model_id,
        prompt_version=prompt_ver,
    )


def run_firm(
    *,
    firm_id: str,
    source_cohort: CohortSource,
    website_url: str,
    locale: str = "vi",
    llm_enabled: bool = True,
    http_fetch: httpx.Client | None = None,
    http_llm: httpx.Client | None = None,
    llm_settings: LocalLlmSettings | None = None,
    verify_pin: bool = False,
    page: RenderedPage | None = None,
) -> FirmCascadeResult:
    rendered = page or fetch_page(website_url, client=http_fetch)
    return run_on_page(
        firm_id=firm_id,
        source_cohort=source_cohort,
        website_url=website_url,
        page=rendered,
        locale=locale,
        llm_enabled=llm_enabled,
        http_llm=http_llm,
        llm_settings=llm_settings,
        verify_pin=verify_pin,
    )


def flatten_indicator_rows(result: FirmCascadeResult) -> list[dict[str, Any]]:
    """One row per tier for CSV/JSONL exports."""
    rows: list[dict[str, Any]] = []
    base = {
        "firm_id": result.firm_id,
        "source_cohort": result.source_cohort,
        "website_url": result.website_url,
        "fetch_ok": result.fetch_ok,
        "fetch_detail": result.fetch_detail,
    }
    if result.tier1 is not None:
        t1 = result.tier1.to_dict()
        rows.append(
            {
                **base,
                "tier": 1,
                "has_product_catalog": t1["has_product_catalog"],
                "has_order_cart": t1["has_order_cart"],
                "payment_methods": ",".join(t1["payment_methods"]),
                "social_link_count": len(t1["social_links"]),
                "marketplace_link_count": len(t1["marketplace_links"]),
                "website_language": t1["website_language"],
                "confidence": 1.0,
                "abstain": False,
                "decision": "rules",
                "model_id": None,
                "evidence": t1["evidence"],
            }
        )
    if result.tier2 is not None:
        t2 = result.tier2
        rows.append(
            {
                **base,
                "tier": 2,
                "has_product_catalog": _field_value(t2, "has_product_catalog"),
                "has_order_cart": _field_value(t2, "has_order_cart"),
                "payment_methods": _join_tokens(_field_value(t2, "payment_methods")),
                "social_link_count": _list_len(_field_value(t2, "social_links")),
                "marketplace_link_count": _list_len(_field_value(t2, "marketplace_links")),
                "website_language": _field_value(t2, "website_language"),
                "confidence": _mean_confidence(t2),
                "abstain": _all_abstain(t2),
                "decision": result.tier2_decision,
                "model_id": result.model_id,
                "evidence": None,
            }
        )
    if not rows:
        rows.append(
            {
                **base,
                "tier": None,
                "has_product_catalog": None,
                "has_order_cart": None,
                "payment_methods": "",
                "social_link_count": None,
                "marketplace_link_count": None,
                "website_language": None,
                "confidence": 0.0,
                "abstain": True,
                "decision": "skip",
                "model_id": None,
                "evidence": None,
            }
        )
    return rows


def _field_value(tier2: dict[str, Any], name: str) -> Any:
    raw = tier2.get(name)
    if isinstance(raw, dict):
        return raw.get("value")
    return None


def _join_tokens(value: Any) -> str:
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(str(item.get("platform") or item.get("url") or ""))
            else:
                parts.append(str(item))
        return ",".join(p for p in parts if p)
    return "" if value is None else str(value)


def _list_len(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _mean_confidence(tier2: dict[str, Any]) -> float:
    vals: list[float] = []
    for raw in tier2.values():
        if isinstance(raw, dict) and "confidence" in raw:
            try:
                vals.append(float(raw["confidence"]))
            except (TypeError, ValueError):
                continue
    if not vals:
        return 0.0
    return round(sum(vals) / len(vals), 4)


def _all_abstain(tier2: dict[str, Any]) -> bool:
    flags = [
        bool(raw.get("abstain"))
        for raw in tier2.values()
        if isinstance(raw, dict) and "abstain" in raw
    ]
    return bool(flags) and all(flags)
