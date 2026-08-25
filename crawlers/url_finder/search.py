"""Search adapters + on-disk SERP cache (reproducible eval)."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from crawlers.companies.website_detector import HTTP_TIMEOUT
from crawlers.url_finder.config_loader import load_config
from crawlers.url_finder.paths import SERP_CACHE_DIR

logger = logging.getLogger(__name__)

DDG_HTML = "https://html.duckduckgo.com/html/"
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    snippet: str = ""
    source: str = "search"


def cache_key(query: str, backend: str) -> str:
    raw = f"{backend}\n{query.strip()}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def unwrap_ddg_href(href: str) -> str:
    raw = (href or "").strip()
    if raw.startswith("//"):
        raw = "https:" + raw
    parsed = urlparse(raw)
    qs = parse_qs(parsed.query)
    if "uddg" in qs and qs["uddg"]:
        return unquote(qs["uddg"][0])
    return raw


def parse_ddg_html(html: str) -> list[SearchHit]:
    soup = BeautifulSoup(html or "", "html.parser")
    hits: list[SearchHit] = []
    seen: set[str] = set()
    anchors = soup.select("a.result__a, a.result-link")
    if not anchors:
        anchors = [
            a
            for a in soup.find_all("a", href=True)
            if "uddg=" in (a.get("href") or "")
        ]
    for a in anchors:
        url = unwrap_ddg_href(a.get("href") or "")
        if not url.startswith("http"):
            continue
        if url in seen:
            continue
        seen.add(url)
        snippet_el = a.find_parent(class_="result")
        snippet = ""
        if snippet_el is not None:
            sn = snippet_el.select_one(".result__snippet")
            snippet = sn.get_text(" ", strip=True) if sn else ""
        hits.append(
            SearchHit(
                title=a.get_text(" ", strip=True),
                url=url,
                snippet=snippet,
            )
        )
    return hits


def _read_cache(path: Path) -> list[SearchHit] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    rows = payload.get("hits") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return None
    hits: list[SearchHit] = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("url"):
            continue
        hits.append(
            SearchHit(
                title=str(row.get("title") or ""),
                url=str(row["url"]),
                snippet=str(row.get("snippet") or ""),
                source=str(row.get("source") or "search"),
            )
        )
    return hits


def _write_cache(path: Path, query: str, backend: str, hits: list[SearchHit]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "query": query,
                "backend": backend,
                "hits": [asdict(h) for h in hits],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


class SearchClient:
    def __init__(
        self,
        *,
        locale: str = "vi",
        cache_dir: Path | None = None,
        delay_seconds: float = 1.6,
        client: httpx.Client | None = None,
        timeout: float = HTTP_TIMEOUT,
    ) -> None:
        cfg = load_config(locale)
        self.backend = str(cfg.get("search_backend") or "duckduckgo_html")
        self.cache_dir = cache_dir or SERP_CACHE_DIR
        self.delay_seconds = delay_seconds
        self._owns = client is None
        accept_language = str(
            cfg.get("accept_language") or "vi-VN,vi;q=0.9,en;q=0.8"
        )
        self.client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": BROWSER_UA,
                "Accept-Language": accept_language,
                "Accept": "text/html,application/xhtml+xml",
            },
            trust_env=False,
        )
        self._last_at = 0.0
        self.blocked = False
        self.block_detail = ""

    def close(self) -> None:
        if self._owns:
            self.client.close()

    def __enter__(self) -> SearchClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _throttle(self) -> None:
        wait = self.delay_seconds - (time.monotonic() - self._last_at)
        if wait > 0:
            time.sleep(wait)

    def search(
        self,
        query: str,
        *,
        use_cache: bool = True,
        refresh: bool = False,
    ) -> list[SearchHit]:
        q = (query or "").strip()
        if not q:
            return []
        if self.blocked:
            return []
        path = self.cache_dir / f"{cache_key(q, self.backend)}.json"
        if use_cache and not refresh:
            cached = _read_cache(path)
            if cached is not None:
                return cached
        hits = self._search_live(q)
        if hits:
            _write_cache(path, q, self.backend, hits)
        return hits

    def _mark_blocked(self, detail: str) -> None:
        self.blocked = True
        self.block_detail = detail
        logger.warning("Search blocked (%s) — skipping further live queries", detail)

    def _search_live(self, query: str) -> list[SearchHit]:
        if self.backend != "duckduckgo_html":
            raise ValueError(f"unsupported search backend: {self.backend}")
        if self.blocked:
            return []
        self._throttle()
        try:
            response = self.client.post(DDG_HTML, data={"q": query, "b": ""})
            self._last_at = time.monotonic()
        except Exception as exec_exc:  # noqa: BLE001 — network; never invent hits
            logger.warning("Search fail query=%r: %s", query, exec_exc)
            self._last_at = time.monotonic()
            return []
        if response.status_code in {202, 403, 429}:
            self._mark_blocked(f"HTTP {response.status_code} {self.backend}")
            return []
        if response.status_code != 200:
            logger.warning(
                "Search HTTP %s query=%r — not caching empty result",
                response.status_code,
                query,
            )
            return []
        hits = parse_ddg_html(response.text)
        if not hits:
            # Bot interstitial / empty page: keep live empty out of cache.
            logger.warning("Search parsed 0 hits query=%r — not caching", query)
            return []
        logger.info("Search %r → %s hits", query, len(hits))
        return hits


def render_queries(
    identity: dict[str, Any],
    *,
    locale: str = "vi",
    templates_key: str = "query_templates",
) -> list[str]:
    cfg = load_config(locale)
    templates = cfg.get(templates_key) or []
    max_q = int(cfg.get("max_queries") or len(templates))
    values = {
        "legal_name": str(identity.get("legal_name") or "").strip(),
        "tax_id": str(identity.get("tax_id") or "").strip(),
        "province": str(identity.get("province") or "").strip(),
        "address": str(identity.get("address") or "").strip(),
        "ticker": str(identity.get("ticker") or "").strip(),
    }
    out: list[str] = []
    for tmpl in templates:
        try:
            query = str(tmpl).format(**values).strip()
        except KeyError:
            continue
        if query and query not in out:
            out.append(query)
        if len(out) >= max_q:
            break
    return out
