"""Fetch a company homepage for indicator extraction (not marketplace listing crawl)."""

from __future__ import annotations

import logging

import httpx

from crawlers.extraction_cascade.schema import RenderedPage
from ml.local_llm.text import html_to_text

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 20.0
USER_AGENT = "Mozilla/5.0 (compatible; MfgDataEconomy/1.0; +research)"
MIN_TEXT_CHARS = 40


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
