"""Tests for GSO manufacturing VA (GDPVNM) — no live network inventing."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from crawlers.gso.iip_crawler import (
    FALLBACK_SOURCE,
    VA_FALLBACK_CSV,
    fetch_gso_va,
    load_fallback_records,
    parse_sdmx_series,
)

FIXTURES = Path(__file__).parent / "fixtures"
VA_SAMPLE_XML = (FIXTURES / "gdp_va_sample.xml").read_text(encoding="utf-8")


def test_parse_va_prefers_quarterly_and_step_holds():
    result = parse_sdmx_series(VA_SAMPLE_XML)

    assert "NGDPVA_R_ISIC4_C_XDC" in result.series_found
    assert "NGDPVA_ISIC4_B_XDC" in result.series_unmapped

    codes = {r["indicator_code"] for r in result.records}
    assert codes == {"VA_C", "VA_C_NOMINAL"}
    assert all(r["source"] == "GSO" for r in result.records)
    assert all(r["vsic_code"] == "C" for r in result.records)

    # Annual 2024 must not appear when quarterly preferred (would be 1.477e6).
    va_c = [r for r in result.records if r["indicator_code"] == "VA_C"]
    assert all(r["value"] != pytest.approx(1477401.5) for r in va_c)
    assert all(r["unit"] == "billion_vnd_constant_2010" for r in va_c)

    # Q1 2024 → Jan–Mar step-hold at 350000
    q1_months = {date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)}
    q1 = [r for r in va_c if r["period"] in q1_months]
    assert len(q1) == 3
    assert all(r["value"] == pytest.approx(350000.0) for r in q1)

    # Q2 step-hold
    q2 = [r for r in va_c if r["period"] == date(2024, 4, 1)]
    assert len(q2) == 1
    assert q2[0]["value"] == pytest.approx(360000.0)

    # Invalid / NA obs skipped
    skip_text = " ".join(result.skipped)
    assert "invalid_TIME_PERIOD" in skip_text
    assert "invalid_OBS_VALUE" in skip_text


def test_parse_does_not_map_iip_file_as_va():
    iip_xml = (FIXTURES / "iip_sample.xml").read_text(encoding="utf-8")
    result = parse_sdmx_series(iip_xml)
    assert {r["indicator_code"] for r in result.records} == {"IIP_C"}
    assert not any(r["indicator_code"].startswith("VA_") for r in result.records)


def test_va_network_failure_falls_back(monkeypatch):
    def boom(self, url):
        raise httpx.ConnectTimeout("timed out", request=MagicMock())

    monkeypatch.setattr(httpx.Client, "get", boom)
    result = fetch_gso_va(urls=("https://example.test/gdp.xml",))
    assert result.status == "fallback"
    assert "network_error" in result.detail
    assert result.records
    assert {r["indicator_code"] for r in result.records} == {"VA_C", "VA_C_NOMINAL"}
    assert all(r["source"] == FALLBACK_SOURCE for r in result.records)


def test_va_fallback_is_sourced_and_not_iip():
    records = load_fallback_records(VA_FALLBACK_CSV)
    assert records
    assert all(r["source"] == FALLBACK_SOURCE for r in records)
    assert {r["indicator_code"] for r in records} == {"VA_C", "VA_C_NOMINAL"}
    assert all(r["indicator_code"] != "IIP_C" for r in records)
    # Step-held annual 2024 constant-price VA
    jan = next(
        r
        for r in records
        if r["indicator_code"] == "VA_C" and r["period"] == date(2024, 1, 1)
    )
    assert jan["value"] == pytest.approx(1477401.5384043476)
    assert jan["unit"] == "billion_vnd_constant_2010"


def test_va_http_error_without_fallback(monkeypatch):
    def bad_status(self, url):
        request = httpx.Request("GET", url)
        return httpx.Response(403, request=request, text="forbidden")

    monkeypatch.setattr(httpx.Client, "get", bad_status)
    result = fetch_gso_va(urls=("https://example.test/gdp.xml",), use_fallback=False)
    assert result.status == "error"
    assert result.records == []
    assert "http_error:403" in result.detail
