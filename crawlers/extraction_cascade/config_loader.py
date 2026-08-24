"""Load locale config for rule-layer extraction (country differences stay in JSON)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from crawlers.extraction_cascade.paths import CONFIG_DIR

DEFAULT_LOCALE = "vi"


def config_path(locale: str = DEFAULT_LOCALE) -> Path:
    return CONFIG_DIR / f"{locale}.json"


@lru_cache(maxsize=8)
def load_config(locale: str = DEFAULT_LOCALE) -> dict[str, Any]:
    path = config_path(locale)
    if not path.exists():
        raise FileNotFoundError(
            f"Extraction-cascade locale config missing: {path}. "
            "Add a JSON file; do not fork rule logic per country."
        )
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"config must be a JSON object: {path}")
    return payload
