"""VSIC Section C 4-digit whitelist loader."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
VSIC_MAPPING_PATH = DATA_DIR / "mappings" / "vsic_isic_section_c.json"


@lru_cache(maxsize=1)
def section_c_vsic_4digit() -> frozenset[str]:
    """Return whitelist of VSIC 4-digit codes under Section C."""
    if not VSIC_MAPPING_PATH.exists():
        return frozenset()
    with open(VSIC_MAPPING_PATH, encoding="utf-8") as f:
        rows = json.load(f)
    return frozenset(
        str(row["vsic_code"])
        for row in rows
        if row.get("level") == 4 and len(str(row.get("vsic_code", ""))) == 4
    )


def is_allowed_vsic(code: str | None) -> bool:
    if code is None:
        return False
    return str(code) in section_c_vsic_4digit()
