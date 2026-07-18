"""Fetch / fallback provenance for BCTC — network mocked."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import httpx

from crawlers.financial.bctc_crawler import (
    FALLBACK_SOURCE_PREFIX,
    SEED_SOURCE_URL,
    fetch_bctc,
)
from tests.financial.conftest import load_fixture_text


def test_live_json_success(monkeypatch):
    payload = load_fixture_text("bctc_ral_structured.json")

    def ok(self, url, **_kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(200, request=request, text=payload)

    monkeypatch.setattr(httpx.Client, "get", ok)

    result = fetch_bctc("RAL", live_urls=("https://example.test/bctc/RAL.json",))
    assert result.status == "ok"
    assert result.report is not None
    assert result.report["revenue"] == 5200000000000
    assert result.source_url == "https://example.test/bctc/RAL.json"


def test_network_failure_uses_seed_fallback(monkeypatch):
    def boom(self, url, **_kwargs):
        raise httpx.ConnectTimeout("timed out", request=MagicMock())

    monkeypatch.setattr(httpx.Client, "get", boom)

    result = fetch_bctc(
        "RAL",
        live_urls=("https://example.test/bctc/RAL.json",),
        use_fallback=True,
    )
    assert result.status == "fallback"
    assert result.report is not None
    assert result.report["period"] == date(2024, 12, 31)
    assert result.report["revenue"] == 5200000000000
    assert result.report["source_url"] in (
        SEED_SOURCE_URL,
        f"{FALLBACK_SOURCE_PREFIX}data/raw/companies_bctc_fallback.json",
    )
    assert "network" in result.detail.lower() or "timeout" in result.detail.lower()


def test_missing_ticker_returns_empty_without_inventing():
    result = fetch_bctc("ZZZZ", live_urls=(), use_fallback=True)
    assert result.status in ("empty", "fallback")
    assert result.report is None or result.report.get("revenue") is None
