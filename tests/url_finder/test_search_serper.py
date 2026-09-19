"""Serper search backend — mocked HTTP only; never call google.serper.dev."""

from __future__ import annotations

import json

import httpx

from crawlers.url_finder.config_loader import resolve_search_backend
from crawlers.url_finder.search import SearchClient, cache_key

SERPER_URL = "https://google.serper.dev/search"


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_default_backend_is_duckduckgo_html(monkeypatch):
    monkeypatch.delenv("URL_FINDER_SEARCH_BACKEND", raising=False)
    assert resolve_search_backend({"search_backend": "duckduckgo_html"}) == "duckduckgo_html"
    assert resolve_search_backend({}) == "duckduckgo_html"


def test_env_search_backend_wins_over_locale(monkeypatch):
    monkeypatch.setenv("URL_FINDER_SEARCH_BACKEND", "serper")
    assert resolve_search_backend({"search_backend": "duckduckgo_html"}) == "serper"


def test_serper_parses_two_organic_hits(tmp_path, monkeypatch):
    monkeypatch.setenv("URL_FINDER_SEARCH_BACKEND", "serper")
    monkeypatch.setenv("SERPER_API_KEY", "test-key")
    captured: dict = {}
    payload = {
        "organic": [
            {
                "title": "Rang Dong",
                "link": "https://rangdong.com.vn/",
                "snippet": "official site",
            },
            {
                "title": "CafeF RAL",
                "link": "https://cafef.vn/ral",
                "snippet": "ticker page",
            },
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["key"] = request.headers.get("X-API-KEY")
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=payload, request=request)

    query = "Rang Dong MST"
    with SearchClient(
        cache_dir=tmp_path,
        client=_client(handler),
        delay_seconds=0,
    ) as searcher:
        assert searcher.backend == "serper"
        hits = searcher.search(query)

    assert [h.url for h in hits] == [
        "https://rangdong.com.vn/",
        "https://cafef.vn/ral",
    ]
    assert [h.title for h in hits] == ["Rang Dong", "CafeF RAL"]
    assert [h.snippet for h in hits] == ["official site", "ticker page"]
    assert all(h.source == "search" for h in hits)
    assert captured["url"] == SERPER_URL
    assert captured["method"] == "POST"
    assert captured["key"] == "test-key"
    assert captured["body"] == {"q": query, "num": 10}
    assert cache_key(query, "serper") != cache_key(query, "duckduckgo_html")
    cache_path = tmp_path / f"{cache_key(query, 'serper')}.json"
    assert cache_path.exists()
    cached = json.loads(cache_path.read_text(encoding="utf-8"))
    assert cached["backend"] == "serper"
    assert len(cached["hits"]) == 2


def test_serper_missing_key_marks_blocked_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("URL_FINDER_SEARCH_BACKEND", "serper")
    monkeypatch.delenv("SERPER_API_KEY", raising=False)

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"must not network when SERPER_API_KEY is missing: {request.url}")

    with SearchClient(
        cache_dir=tmp_path,
        client=_client(handler),
        delay_seconds=0,
    ) as searcher:
        hits = searcher.search("anything")
        assert hits == []
        assert searcher.blocked is True
        assert searcher.block_detail == "missing_SERPER_API_KEY"


def test_serper_http_401_marks_blocked(tmp_path, monkeypatch):
    monkeypatch.setenv("URL_FINDER_SEARCH_BACKEND", "serper")
    monkeypatch.setenv("SERPER_API_KEY", "bad-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Unauthorized"}, request=request)

    with SearchClient(
        cache_dir=tmp_path,
        client=_client(handler),
        delay_seconds=0,
    ) as searcher:
        hits = searcher.search("Rang Dong")
        assert hits == []
        assert searcher.blocked is True
        assert searcher.block_detail == "HTTP 401 serper"
        assert list(tmp_path.glob("*.json")) == []
