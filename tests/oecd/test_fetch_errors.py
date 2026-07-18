"""Network / HTTP / unavailable handling — mocked client, no live network."""

from unittest.mock import MagicMock

import httpx
import pytest

from crawlers.oecd.sdmx_client import (
    INDICATOR_SPECS,
    HttpError,
    IndicatorSpec,
    NetworkError,
    SeriesUnavailableError,
    fetch_indicator,
    fetch_oecd_indicators,
    fetch_sdmx_json,
)


def _spec(code: str = "MEI_IP") -> IndicatorSpec:
    return next(s for s in INDICATOR_SPECS if s.indicator_code == code)


def test_fetch_sdmx_json_network_error():
    client = MagicMock()
    client.get.side_effect = httpx.ConnectError("connection refused")
    with pytest.raises(NetworkError):
        fetch_sdmx_json("https://sdmx.oecd.org/public/rest/data/example", client=client)


def test_fetch_sdmx_json_http_error():
    client = MagicMock()
    response = MagicMock()
    response.status_code = 500
    response.text = "Internal Server Error"
    response.reason_phrase = "Internal Server Error"
    response.json.side_effect = AssertionError("should not parse")
    client.get.return_value = response
    with pytest.raises(HttpError) as exc:
        fetch_sdmx_json("https://sdmx.oecd.org/public/rest/data/example", client=client)
    assert exc.value.status_code == 500


def test_fetch_sdmx_json_empty_series_is_unavailable():
    client = MagicMock()
    response = MagicMock()
    response.status_code = 404
    response.text = "NoRecordsFound"
    client.get.return_value = response
    with pytest.raises(SeriesUnavailableError):
        fetch_sdmx_json("https://sdmx.oecd.org/public/rest/data/example", client=client)


def test_fetch_indicator_marks_unavailable_without_fabricating():
    client = MagicMock()
    response = MagicMock()
    response.status_code = 404
    response.text = "NoRecordsFound"
    client.get.return_value = response

    records, status = fetch_indicator(
        _spec("MEI_IP"), country="VNM", client=client, allow_fixture_fallback=False
    )
    assert records == []
    assert status.status == "unavailable"
    assert status.records == 0


def test_fetch_oecd_indicators_network_failure_status():
    client = MagicMock()
    client.get.side_effect = httpx.ConnectError("dns failed")

    # Use ICT (no fixture) so network error surfaces cleanly.
    ict = _spec("ICT_INVEST")
    result = fetch_oecd_indicators(
        country="VNM",
        client=client,
        specs=(ict,),
        allow_fixture_fallback=True,
    )
    assert result.records == []
    assert result.statuses[0].status == "network_error"
