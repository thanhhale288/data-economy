"""Tests for GSO IIP SDMX crawler — no live network."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import GsoMacro, VsicCode
from crawlers.gso.iip_crawler import (
    FALLBACK_SOURCE,
    FetchResult,
    GsoHttpError,
    GsoNetworkError,
    fetch_gso_iip,
    load_fallback_records,
    parse_sdmx_series,
    save_gso_records,
)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_XML = (FIXTURES / "iip_sample.xml").read_text(encoding="utf-8")


def test_parse_multi_series_valid_sample():
    result = parse_sdmx_series(SAMPLE_XML)

    assert "AIP_ISIC4_IX" in result.series_found
    assert "AIP_ISIC4_C_IX" in result.series_found
    assert "AIP_ISIC4_IX" in result.series_unmapped

    # Only manufacturing (Section C) is mapped.
    codes = {r["indicator_code"] for r in result.records}
    assert codes == {"IIP_C"}
    assert all(r["vsic_code"] == "C" for r in result.records)
    assert all(r["source"] == "GSO" for r in result.records)
    assert all(r["unit"] == "index_2015=100" for r in result.records)

    periods = {r["period"] for r in result.records}
    assert date(2017, 1, 1) in periods
    assert date(2017, 2, 1) in periods
    # May observation is valid in the fixture.
    assert date(2017, 5, 1) in periods

    jan = next(r for r in result.records if r["period"] == date(2017, 1, 1))
    assert jan["value"] == pytest.approx(97.47)


def test_parse_skips_missing_and_invalid_values():
    result = parse_sdmx_series(SAMPLE_XML)

    skip_text = " ".join(result.skipped)
    assert "missing_OBS_VALUE" in skip_text
    assert "invalid_OBS_VALUE" in skip_text
    assert "invalid_TIME_PERIOD" in skip_text

    # Bad rows must not appear as records.
    assert date(2017, 3, 1) not in {r["period"] for r in result.records}
    assert date(2017, 4, 1) not in {r["period"] for r in result.records}


def test_parse_single_series_document():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <message:StructureSpecificData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
      <message:DataSet>
        <Series INDICATOR="AIP_ISIC4_C_IX" BASE_PER="2015">
          <Obs TIME_PERIOD="2020-06" OBS_VALUE="112.5"/>
        </Series>
      </message:DataSet>
    </message:StructureSpecificData>
    """
    result = parse_sdmx_series(xml)
    assert len(result.records) == 1
    assert result.records[0]["period"] == date(2020, 6, 1)
    assert result.records[0]["value"] == 112.5


def test_network_failure_falls_back(monkeypatch):
    def boom(self, url):
        raise httpx.ConnectTimeout("timed out", request=MagicMock())

    monkeypatch.setattr(httpx.Client, "get", boom)

    result = fetch_gso_iip(urls=("https://example.test/iip.xml",))
    assert isinstance(result, FetchResult)
    assert result.status == "fallback"
    assert "network_error" in result.detail
    assert result.records
    assert all(r["source"] == FALLBACK_SOURCE for r in result.records)


def test_http_error_falls_back(monkeypatch):
    def bad_status(self, url):
        request = httpx.Request("GET", url)
        return httpx.Response(503, request=request, text="unavailable")

    monkeypatch.setattr(httpx.Client, "get", bad_status)

    result = fetch_gso_iip(urls=("https://example.test/iip.xml",), use_fallback=True)
    assert result.status == "fallback"
    assert "http_error:503" in result.detail


def test_http_error_without_fallback(monkeypatch):
    def bad_status(self, url):
        request = httpx.Request("GET", url)
        return httpx.Response(404, request=request, text="missing")

    monkeypatch.setattr(httpx.Client, "get", bad_status)

    result = fetch_gso_iip(urls=("https://example.test/iip.xml",), use_fallback=False)
    assert result.status == "error"
    assert result.records == []
    assert "http_error:404" in result.detail


def test_successful_fetch_uses_parser(monkeypatch):
    def ok(self, url):
        request = httpx.Request("GET", url)
        return httpx.Response(200, request=request, text=SAMPLE_XML)

    monkeypatch.setattr(httpx.Client, "get", ok)

    result = fetch_gso_iip(urls=("https://example.test/iip.xml",))
    assert result.status == "ok"
    assert result.source_url == "https://example.test/iip.xml"
    assert result.records
    # SDMX IIP file does not contain shipment/inventory (those come from PX-Web).
    assert "series_unavailable" in result.detail


def test_fallback_is_deterministic_and_sourced():
    a = load_fallback_records()
    b = load_fallback_records()
    assert a == b
    assert len(a) >= 12
    assert all(r["source"] == FALLBACK_SOURCE for r in a)
    assert all(r["indicator_code"] == "IIP_C" for r in a)
    assert a[0]["period"] == date(2017, 1, 1)
    assert a[0]["value"] == pytest.approx(97.47)


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'gso_test.db'}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(
        VsicCode(
            vsic_code="C",
            isic_code="C",
            level=1,
            name_vi="Công nghiệp chế biến, chế tạo",
            name_en="Manufacturing",
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_persistence_idempotent(db_session):
    records = [
        {
            "vsic_code": "C",
            "indicator_code": "IIP_C",
            "indicator_name": "Chỉ số SXCN - Chế biến chế tạo",
            "period": date(2024, 1, 1),
            "value": 180.0,
            "unit": "index_2015=100",
            "source": "GSO",
        }
    ]
    inserted_first = save_gso_records(db_session, records)
    assert inserted_first == 1
    assert db_session.query(GsoMacro).count() == 1

    records[0]["value"] = 181.5
    records[0]["source"] = FALLBACK_SOURCE
    inserted_second = save_gso_records(db_session, records)
    assert inserted_second == 0
    assert db_session.query(GsoMacro).count() == 1

    row = db_session.query(GsoMacro).one()
    assert row.value == pytest.approx(181.5)
    assert row.source == FALLBACK_SOURCE


def test_download_raises_typed_errors():
    from crawlers.gso.iip_crawler import _download_xml

    client = MagicMock()
    client.get.side_effect = httpx.ConnectError("refused", request=MagicMock())
    with pytest.raises(GsoNetworkError):
        _download_xml("https://example.test/x", client)

    request = httpx.Request("GET", "https://example.test/x")
    client.get.side_effect = None
    client.get.return_value = httpx.Response(500, request=request, text="err")
    with pytest.raises(GsoHttpError) as ei:
        _download_xml("https://example.test/x", client)
    assert ei.value.status_code == 500
