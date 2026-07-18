"""Tests for NSO PX-Web shipment/inventory client — no live network."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from crawlers.gso.pxweb_client import (
    FALLBACK_SOURCE,
    LIVE_SOURCE,
    PxwebHttpError,
    PxwebNetworkError,
    expand_annual_to_monthly_step,
    fetch_pxweb_section_c,
    fetch_pxweb_table,
    load_pxweb_fallback,
    parse_pxweb_table,
    _parse_year_label,
)

FIXTURES = Path(__file__).parent / "fixtures"
SHIPMENT_FIXTURE = FIXTURES / "pxweb_shipment_sample.json"


@pytest.fixture(scope="module")
def shipment_sample():
    return json.loads(SHIPMENT_FIXTURE.read_text(encoding="utf-8"))


def test_parse_year_label():
    assert _parse_year_label("2023") == 2023
    assert _parse_year_label("Prel. 2024") == 2024
    assert _parse_year_label("bad") is None


def test_parse_pxweb_shipment_whole_manufacturing(shipment_sample):
    meta = {"variables": shipment_sample["meta"]["variables"]}
    records = parse_pxweb_table(
        meta,
        shipment_sample["data"],
        indicator_code="SHIPMENT_C",
        indicator_name="shipment",
        unit="index_prev_year=100",
        source=LIVE_SOURCE,
        step_hold_monthly=False,
    )
    assert len(records) == 3
    assert all(r["vsic_code"] == "C" for r in records)
    assert all(r["indicator_code"] == "SHIPMENT_C" for r in records)
    by_year = {r["period"].year: r["value"] for r in records}
    assert by_year[2022] == pytest.approx(106.82)
    assert by_year[2023] == pytest.approx(101.46)
    assert by_year[2024] == pytest.approx(111.38)


def test_annual_step_hold():
    annual = [
        {
            "vsic_code": "C",
            "indicator_code": "SHIPMENT_C",
            "indicator_name": "x",
            "period": date(2023, 1, 1),
            "value": 100.0,
            "unit": "index",
            "source": LIVE_SOURCE,
        }
    ]
    monthly = expand_annual_to_monthly_step(annual)
    assert len(monthly) == 12
    assert monthly[0]["period"] == date(2023, 1, 1)
    assert monthly[11]["period"] == date(2023, 12, 1)
    assert all(r["value"] == 100.0 for r in monthly)


def test_network_failure_uses_fallback(monkeypatch):
    def boom(self, url, **kwargs):
        raise httpx.ConnectTimeout("timed out", request=MagicMock())

    monkeypatch.setattr(httpx.Client, "get", boom)
    monkeypatch.setattr(httpx.Client, "post", boom)

    result = fetch_pxweb_table("E07.03.px", use_fallback=True)
    assert result.status == "fallback"
    assert result.records
    assert all(r["source"] == FALLBACK_SOURCE for r in result.records)
    assert all(r["indicator_code"] == "SHIPMENT_C" for r in result.records)
    # step-hold: 13 years * 12 months in committed fallback
    assert len(result.records) == 13 * 12


def test_http_error_without_fallback(monkeypatch):
    def bad(self, url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(503, request=request, text="down")

    monkeypatch.setattr(httpx.Client, "get", bad)
    monkeypatch.setattr(httpx.Client, "post", bad)

    result = fetch_pxweb_table("E07.03.px", use_fallback=False)
    assert result.status == "error"
    assert result.records == []


def test_load_committed_fallbacks():
    ship = load_pxweb_fallback("E07.03.px")
    inv = load_pxweb_fallback("E07.04.px")
    assert ship and inv
    assert {r["indicator_code"] for r in ship} == {"SHIPMENT_C"}
    assert {r["indicator_code"] for r in inv} == {"INVENTORY_C"}


def test_fetch_section_c_combines_both_from_fallback(monkeypatch):
    def boom(self, url, **kwargs):
        raise httpx.ConnectError("refused", request=MagicMock())

    monkeypatch.setattr(httpx.Client, "get", boom)
    monkeypatch.setattr(httpx.Client, "post", boom)

    result = fetch_pxweb_section_c(use_fallback=True)
    codes = {r["indicator_code"] for r in result.records}
    assert codes == {"SHIPMENT_C", "INVENTORY_C"}
    assert result.status == "fallback"
