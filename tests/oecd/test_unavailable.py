"""Fallback / unavailable: missing VN series must not invent numbers."""

from unittest.mock import MagicMock

from crawlers.oecd.sdmx_client import (
    FALLBACK_SOURCE,
    INDICATOR_SPECS,
    fetch_indicator,
    load_fixture_payload,
    parse_sdmx_json,
    harmonize_to_monthly,
)


def test_missing_vn_series_unavailable_not_fabricated():
    client = MagicMock()
    response = MagicMock()
    response.status_code = 404
    response.text = "NoResultsFound"
    client.get.return_value = response

    for code in ("MEI_IP", "MEI_BCI", "ICT_INVEST"):
        spec = next(s for s in INDICATOR_SPECS if s.indicator_code == code)
        records, status = fetch_indicator(
            spec, country="VNM", client=client, allow_fixture_fallback=True
        )
        assert records == [], code
        assert status.status == "unavailable", code


def test_indigo_fixture_is_traceable_when_used_offline():
    payload = load_fixture_payload("oecd_indigo_vnm.json")
    records = parse_sdmx_json(
        payload,
        indicator_code="INDIGO",
        indicator_name="Digital Trade Openness Index",
        country_filter="VNM",
        source=FALLBACK_SOURCE,
    )
    assert records
    assert all(r["source"] == FALLBACK_SOURCE for r in records)
    assert all(isinstance(r["value"], float) for r in records)
    monthly = harmonize_to_monthly(records)
    assert all(r["frequency"] == "monthly" for r in monthly)
    # 15 annual years → 15 * 12 months
    assert len(monthly) == len(records) * 12
