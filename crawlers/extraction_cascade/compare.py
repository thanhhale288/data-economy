"""Compare tier-1 rules vs tier-2 LLM fields without inventing values."""

from __future__ import annotations

from typing import Any

from crawlers.extraction_cascade.schema import ConflictRow, Tier1Indicators

BOOL_FIELDS = ("has_product_catalog", "has_order_cart")
LIST_PRESENCE_FIELDS = ("payment_methods", "social_links", "marketplace_links")
LANG_FIELD = "website_language"


def _tier2_field(tier2: dict[str, Any] | None, name: str) -> dict[str, Any]:
    if not isinstance(tier2, dict):
        return {"value": None, "abstain": True, "confidence": 0.0, "reason": "missing_tier2"}
    raw = tier2.get(name)
    if not isinstance(raw, dict):
        return {"value": None, "abstain": True, "confidence": 0.0, "reason": "missing_field"}
    return raw


def _boolish(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return bool(value)


def _presence_from_list(value: Any) -> bool:
    if isinstance(value, list):
        return len(value) > 0
    return bool(value)


def compare_tiers(
    firm_id: str,
    tier1: Tier1Indicators | None,
    tier2: dict[str, Any] | None,
    *,
    fetch_ok: bool,
) -> list[ConflictRow]:
    """Return per-field agree / conflict / abstain / skip rows."""
    if not fetch_ok or tier1 is None:
        return [
            ConflictRow(
                firm_id=firm_id,
                field="*",
                kind="skip",
                tier1_value=None,
                tier2_value=None,
                tier2_abstain=True,
                note="fetch_failed_or_no_tier1",
            )
        ]

    rows: list[ConflictRow] = []

    for name in BOOL_FIELDS:
        t1 = bool(getattr(tier1, name))
        f2 = _tier2_field(tier2, name)
        rows.append(_compare_bool(firm_id, name, t1, f2))

    for name in LIST_PRESENCE_FIELDS:
        t1_list = getattr(tier1, name) or []
        t1_present = len(t1_list) > 0
        f2 = _tier2_field(tier2, name)
        rows.append(_compare_presence(firm_id, name, t1_present, t1_list, f2))

    t1_lang = tier1.website_language
    f2 = _tier2_field(tier2, LANG_FIELD)
    rows.append(_compare_lang(firm_id, t1_lang, f2))
    return rows


def _compare_bool(
    firm_id: str,
    field: str,
    t1: bool,
    f2: dict[str, Any],
) -> ConflictRow:
    if f2.get("abstain"):
        return ConflictRow(
            firm_id=firm_id,
            field=field,
            kind="abstain",
            tier1_value=t1,
            tier2_value=f2.get("value"),
            tier2_abstain=True,
            note=str(f2.get("reason") or "tier2_abstain"),
        )
    t2 = _boolish(f2.get("value"))
    if t2 is None:
        return ConflictRow(
            firm_id=firm_id,
            field=field,
            kind="abstain",
            tier1_value=t1,
            tier2_value=None,
            tier2_abstain=True,
            note="tier2_null_value",
        )
    kind = "agree" if t1 == t2 else "conflict"
    return ConflictRow(
        firm_id=firm_id,
        field=field,
        kind=kind,
        tier1_value=t1,
        tier2_value=t2,
        tier2_abstain=False,
        note="" if kind == "agree" else "bool_mismatch",
    )


def _compare_presence(
    firm_id: str,
    field: str,
    t1_present: bool,
    t1_list: list[Any],
    f2: dict[str, Any],
) -> ConflictRow:
    if f2.get("abstain"):
        return ConflictRow(
            firm_id=firm_id,
            field=field,
            kind="abstain",
            tier1_value=t1_list,
            tier2_value=f2.get("value"),
            tier2_abstain=True,
            note=str(f2.get("reason") or "tier2_abstain"),
        )
    t2_present = _presence_from_list(f2.get("value"))
    kind = "agree" if t1_present == t2_present else "conflict"
    return ConflictRow(
        firm_id=firm_id,
        field=field,
        kind=kind,
        tier1_value=t1_list,
        tier2_value=f2.get("value"),
        tier2_abstain=False,
        note="" if kind == "agree" else "presence_mismatch",
    )


def _compare_lang(
    firm_id: str,
    t1_lang: str | None,
    f2: dict[str, Any],
) -> ConflictRow:
    if f2.get("abstain"):
        return ConflictRow(
            firm_id=firm_id,
            field=LANG_FIELD,
            kind="abstain",
            tier1_value=t1_lang,
            tier2_value=f2.get("value"),
            tier2_abstain=True,
            note=str(f2.get("reason") or "tier2_abstain"),
        )
    t2 = f2.get("value")
    if t1_lang is None and t2 is None:
        kind: str = "agree"
    elif t1_lang == t2:
        kind = "agree"
    elif t1_lang in {None, "unknown"} or t2 in {None, "unknown"}:
        kind = "agree"
        note = "unknown_compatible"
        return ConflictRow(
            firm_id=firm_id,
            field=LANG_FIELD,
            kind="agree",
            tier1_value=t1_lang,
            tier2_value=t2,
            tier2_abstain=False,
            note=note,
        )
    else:
        return ConflictRow(
            firm_id=firm_id,
            field=LANG_FIELD,
            kind="conflict",
            tier1_value=t1_lang,
            tier2_value=t2,
            tier2_abstain=False,
            note="language_mismatch",
        )
    return ConflictRow(
        firm_id=firm_id,
        field=LANG_FIELD,
        kind="agree",
        tier1_value=t1_lang,
        tier2_value=t2,
        tier2_abstain=False,
        note="",
    )
