"""JSIC manufacturing = Division E (confirmed on gBizINFO search UI, 2026-08)."""

from __future__ import annotations

import re

# JSIC Rev.13 (2013) and the gBizINFO 業種 checkbox both label manufacturing as
# Division E (製造業). Major groups 09–32 in Rev.13. Record the raw string too.
JSIC_MANUFACTURING_DIVISION = "E"
JSIC_E_MAJOR_GROUPS = tuple(f"{i:02d}" for i in range(9, 33))

_DIV_RE = re.compile(r"\b([A-T])\b", re.IGNORECASE)
_MAJOR_RE = re.compile(r"\b(0[9]|1\d|2\d|3[0-2])\b")


def jsic_division(raw: str | None) -> str | None:
    text = (raw or "").strip()
    if not text:
        return None
    if text.upper().startswith("E") or "製造" in text:
        # "E.製造業" / "E-31" / "製造業"
        if text.upper()[:1] == "E" or "製造" in text:
            match = _DIV_RE.search(text.upper().replace("Ｅ", "E"))
            if match:
                return match.group(1).upper()
            if "製造" in text:
                return JSIC_MANUFACTURING_DIVISION
    match = _DIV_RE.search(text.upper())
    return match.group(1).upper() if match else None


def is_manufacturing(raw: str | None) -> bool:
    div = jsic_division(raw)
    if div == JSIC_MANUFACTURING_DIVISION:
        return True
    major = _MAJOR_RE.search(raw or "")
    return bool(major and major.group(1) in JSIC_E_MAJOR_GROUPS)
