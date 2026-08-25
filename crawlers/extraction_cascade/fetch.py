"""Fetch a company homepage for indicator extraction (not marketplace listing crawl)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path

import httpx

from crawlers.extraction_cascade.paths import PAGES_CACHE_DIR
from crawlers.extraction_cascade.schema import RenderedPage
from ml.local_llm.text import html_to_text

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 20.0
USER_AGENT = "Mozilla/5.0 (compatible; MfgDataEconomy/1.0; +research)"
MIN_TEXT_CHARS = 40

_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")


def cache_key(firm_id: str, url: str) -> str:
    digest = hashlib.sha256(f"{firm_id}|{url}".encode()).hexdigest()[:16]
    safe = _SAFE_ID.sub("_", firm_id)[:40] or "firm"
    return f"{safe}_{digest}"


def _cache_paths(firm_id: str, url: str, cache_dir: Path) -> tuple[Path, Path]:
    key = cache_key(firm_id, url)
    return cache_dir / f"{key}.html", cache_dir / f"{key}.meta.json"


def load_cached_page(
    firm_id: str,
    url: str,
    *,
    cache_dir: Path | None = None,
    max_chars: int = 8000,
) -> RenderedPage | None:
    """Return a prior fetch from disk, or None if missing."""
    root = cache_dir or PAGES_CACHE_DIR
    html_path, meta_path = _cache_paths(firm_id, url, root)
    if not html_path.exists() or not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    html = html_path.read_text(encoding="utf-8", errors="replace")
    ok = bool(meta.get("ok"))
    text = html_to_text(html, max_chars=max_chars) if ok and html.strip() else ""
    return RenderedPage(
        url=str(meta.get("url") or url),
        final_url=str(meta.get("final_url") or url),
        ok=ok,
        detail=str(meta.get("detail") or "cache"),
        html=html if ok else "",
        text=text,
        status_code=meta.get("status_code"),
    )


def save_cached_page(
    firm_id: str,
    page: RenderedPage,
    *,
    cache_dir: Path | None = None,
) -> None:
    """Persist HTML + meta for reuse (regenerable; gitignored)."""
    root = cache_dir or PAGES_CACHE_DIR
    root.mkdir(parents=True, exist_ok=True)
    html_path, meta_path = _cache_paths(firm_id, page.url, root)
    html_path.write_text(page.html if page.ok else "", encoding="utf-8")
    meta = {
        "firm_id": firm_id,
        "url": page.url,
        "final_url": page.final_url,
        "ok": page.ok,
        "detail": page.detail,
        "status_code": page.status_code,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_page(
    url: str,
    *,
    client: httpx.Client | None = None,
    max_chars: int = 8000,
) -> RenderedPage:
    """HTTP GET company site. On fail: ok=False and empty html/text — never invent."""
    if not url or not str(url).strip():
        return RenderedPage(
            url=url or "",
            final_url=url or "",
            ok=False,
            detail="missing_url",
        )

    owns = client is None
    http = client or httpx.Client(
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )
    try:
        response = http.get(url)
        final = str(response.url)
        if response.status_code != 200:
            detail = f"http_fail status={response.status_code}"
            logger.warning("Cascade fetch fail %s: %s", url, detail)
            return RenderedPage(
                url=url,
                final_url=final,
                ok=False,
                detail=detail,
                status_code=response.status_code,
            )
        html = response.text or ""
        text = html_to_text(html, max_chars=max_chars)
        detail = "ok"
        if len(text) < MIN_TEXT_CHARS:
            detail = "ok_sparse_text"
        return RenderedPage(
            url=url,
            final_url=final,
            ok=True,
            detail=detail,
            html=html,
            text=text,
            status_code=response.status_code,
        )
    except Exception as exc:  # noqa: BLE001 — network/parse; do not invent indicators
        detail = f"error:{type(exc).__name__}:{exc}"
        logger.warning("Cascade fetch fail %s: %s", url, detail)
        return RenderedPage(url=url, final_url=url, ok=False, detail=detail)
    finally:
        if owns:
            http.close()
