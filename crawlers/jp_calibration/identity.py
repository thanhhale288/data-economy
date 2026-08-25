"""Japan identity IO — 13-digit 法人番号, no URL fields, no VN 10-digit MST rule."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from crawlers.jp_calibration.paths import IDENTITY_FILE, LABELS_FILE
from crawlers.url_finder.domain import registrable_domain
from crawlers.url_finder.identity import assert_no_url_fields


def load_jp_identity(path: Path | None = None) -> list[dict[str, Any]]:
    import json

    target = path or IDENTITY_FILE
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{target}: identity must be a JSON list")
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(f"{target}: rows must be objects")
        assert_no_url_fields(item, context=str(target))
        number = str(item.get("ticker") or item.get("corporate_number") or "").strip()
        if len(number) != 13 or not number.isdigit():
            raise ValueError(f"{target}: ticker/corporate_number must be 13 digits")
        if number in seen:
            raise ValueError(f"{target}: duplicate {number}")
        seen.add(number)
        out.append(
            {
                **item,
                "ticker": number,
                "corporate_number": number,
                "legal_name": str(item.get("legal_name") or "").strip(),
                "tax_id": str(item.get("tax_id") or number).strip(),
                "address": str(item.get("address") or "").strip(),
                "province": str(item.get("province") or item.get("prefecture") or "").strip(),
                "aliases": [
                    str(a).strip()
                    for a in (item.get("aliases") or [])
                    if str(a).strip()
                ],
            }
        )
    return out


def load_jp_labels(path: Path | None = None) -> dict[str, dict[str, Any]]:
    import json

    target = path or LABELS_FILE
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{target}: labels must be a JSON list")
    out: dict[str, dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        ticker = str(item.get("ticker") or "").strip()
        gold = str(item.get("gold_url") or "").strip()
        if not ticker or not gold:
            raise ValueError(f"{target}: each label needs ticker + gold_url")
        out[ticker] = {
            "ticker": ticker,
            "gold_url": gold,
            "gold_domain": registrable_domain(gold),
            "note": str(item.get("note") or "gBizINFO company_url (silver)"),
            "employee_stratum": str(item.get("employee_stratum") or ""),
            "prefecture": str(item.get("prefecture") or ""),
        }
    return out
