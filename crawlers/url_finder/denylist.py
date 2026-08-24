"""Drop directory / media / marketplace hosts from URL-finder candidates."""

from __future__ import annotations

from crawlers.url_finder.config_loader import load_config
from crawlers.url_finder.domain import registrable_domain, strip_www


def aggregator_suffixes(locale: str = "vi") -> tuple[str, ...]:
    cfg = load_config(locale)
    raw = cfg.get("aggregator_suffixes") or []
    return tuple(str(item).lower().rstrip(".") for item in raw if str(item).strip())


def is_aggregator_host(url_or_host: str | None, locale: str = "vi") -> bool:
    host = strip_www(registrable_domain(url_or_host) or "")
    if not host:
        return False
    for suffix in aggregator_suffixes(locale):
        if host == suffix or host.endswith(f".{suffix}"):
            return True
    return False
