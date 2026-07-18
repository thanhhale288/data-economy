"""Parser tests against real-shaped OECD SDMX-JSON v2 fixtures."""

from datetime import date

from crawlers.oecd.sdmx_client import parse_period, parse_sdmx_json
from tests.oecd.conftest import load_fixture


def test_parse_period_monthly_quarterly_annual():
    assert parse_period("2024-01") == date(2024, 1, 1)
    assert parse_period("2023-Q2") == date(2023, 4, 1)
    assert parse_period("2021") == date(2021, 1, 1)


def test_parse_monthly_ip_extracts_periods_indicator_frequency():
    payload = load_fixture("sdmx_ip_monthly_usa.json")
    records = parse_sdmx_json(
        payload,
        indicator_code="MEI_IP",
        indicator_name="Industrial Production Index",
        isic_code="C",
        country_filter="USA",
        activity_filter="C",
    )
    assert records
    assert all(r["indicator_code"] == "MEI_IP" for r in records)
    assert all(r["frequency"] == "monthly" for r in records)
    assert all(r["country"] == "USA" for r in records)
    assert all(r["unit"] == "IX" for r in records)
    periods = {r["period"] for r in records}
    assert periods == {date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)}
    # Values must come from the fixture, not a hardcoded date dump.
    by_period = {r["period"]: r["value"] for r in records}
    assert by_period[date(2024, 1, 1)] == 94.90908
    assert by_period[date(2024, 2, 1)] == 96.12808
    assert by_period[date(2024, 3, 1)] == 96.24496


def test_parse_quarterly_ip_extracts_quarter_starts():
    payload = load_fixture("sdmx_ip_quarterly_usa.json")
    records = parse_sdmx_json(
        payload,
        indicator_code="MEI_IP",
        indicator_name="Industrial Production Index",
        isic_code="C",
        country_filter="USA",
        activity_filter="C",
    )
    assert len(records) == 2
    assert all(r["frequency"] == "quarterly" for r in records)
    periods = sorted(r["period"] for r in records)
    assert periods == [date(2023, 1, 1), date(2023, 4, 1)]


def test_parse_indigo_vietnam_annual():
    payload = load_fixture("sdmx_indigo_vnm.json")
    records = parse_sdmx_json(
        payload,
        indicator_code="INDIGO",
        indicator_name="Digital Trade Openness Index",
        country_filter="VNM",
    )
    assert records
    assert all(r["country"] == "VNM" for r in records)
    assert all(r["indicator_code"] == "INDIGO" for r in records)
    assert all(r["frequency"] == "annual" for r in records)
    periods = {r["period"] for r in records}
    assert periods == {date(2020, 1, 1), date(2021, 1, 1), date(2022, 1, 1)}
