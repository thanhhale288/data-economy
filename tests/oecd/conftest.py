"""Shared helpers for OECD crawler tests."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    with (FIXTURES / name).open() as fh:
        return json.load(fh)
