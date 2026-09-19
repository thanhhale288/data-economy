"""Load locale config (language + query templates). Logic stays in Python."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from crawlers.url_finder.paths import CONFIG_DIR

DEFAULT_LOCALE = "vi"
DEFAULT_SEARCH_BACKEND = "duckduckgo_html"
SEARCH_BACKEND_ENV = "URL_FINDER_SEARCH_BACKEND"


def config_path(locale: str = DEFAULT_LOCALE) -> Path:
    return CONFIG_DIR / f"{locale}.json"


@lru_cache(maxsize=8)
def load_config(locale: str = DEFAULT_LOCALE) -> dict[str, Any]:
    path = config_path(locale)
    if not path.exists():
        raise FileNotFoundError(
            f"URL-finder locale config missing: {path}. "
            "Add a JSON file; do not fork scoring logic per country."
        )
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"config must be a JSON object: {path}")
    return payload


def resolve_search_backend(cfg: dict[str, Any] | None = None) -> str:
    """Locale JSON `search_backend`, or env `URL_FINDER_SEARCH_BACKEND` (env wins)."""
    env = (os.environ.get(SEARCH_BACKEND_ENV) or "").strip()
    if env:
        return env
    if not cfg:
        return DEFAULT_SEARCH_BACKEND
    return str(cfg.get("search_backend") or DEFAULT_SEARCH_BACKEND)
