"""Registrable-domain matching for official-website gold labels."""

from __future__ import annotations

from urllib.parse import urlparse

# Vietnam ccTLD second-level labels (not an exhaustive PSL).
_MULTI_PART_TLDS: tuple[str, ...] = (
    ".com.vn",
    ".net.vn",
    ".org.vn",
    ".edu.vn",
    ".gov.vn",
    ".ac.vn",
    ".biz.vn",
    ".info.vn",
    ".health.vn",
    ".int.vn",
    ".name.vn",
    ".pro.vn",
    ".co.jp",
    ".or.jp",
    ".ne.jp",
    ".ac.jp",
    ".go.jp",
    ".ed.jp",
    ".gr.jp",
    ".lg.jp",
    ".co.uk",
    ".com.au",
)


def host_from_url(url: str | None) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = (parsed.netloc or parsed.path.split("/")[0]).lower()
    if "@" in host:
        host = host.rsplit("@", 1)[-1]
    if ":" in host:
        host = host.split(":", 1)[0]
    return host.rstrip(".")


def strip_www(host: str) -> str:
    h = (host or "").lower().rstrip(".")
    return h[4:] if h.startswith("www.") else h


def registrable_domain(url_or_host: str | None) -> str:
    """Return eTLD+1, treating ``.com.vn`` (etc.) as a single public suffix."""
    host = strip_www(host_from_url(url_or_host) or (url_or_host or ""))
    if not host or "." not in host:
        return host
    for suffix in _MULTI_PART_TLDS:
        if host.endswith(suffix):
            rest = host[: -len(suffix)]
            if not rest:
                return host
            return f"{rest.split('.')[-1]}{suffix}"
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def domains_match(left: str | None, right: str | None) -> bool:
    a = registrable_domain(left)
    b = registrable_domain(right)
    return bool(a) and a == b
