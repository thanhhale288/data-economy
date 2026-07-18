"""Quarter→month interpolation tests."""

from datetime import date

from crawlers.oecd.sdmx_client import (
    interpolate_quarterly_to_monthly,
    parse_sdmx_json,
)
from tests.oecd.conftest import load_fixture


def test_monthly_series_untouched():
    monthly = [
        {
            "indicator_code": "MEI_IP",
            "indicator_name": "Industrial Production Index",
            "country": "USA",
            "isic_code": "C",
            "period": date(2024, 1, 1),
            "value": 100.0,
            "unit": "IX",
            "frequency": "monthly",
        },
        {
            "indicator_code": "MEI_IP",
            "indicator_name": "Industrial Production Index",
            "country": "USA",
            "isic_code": "C",
            "period": date(2024, 2, 1),
            "value": 101.0,
            "unit": "IX",
            "frequency": "monthly",
        },
    ]
    out = interpolate_quarterly_to_monthly(monthly)
    assert out == monthly


def test_quarterly_linear_expansion():
    quarterly = [
        {
            "indicator_code": "MEI_IP",
            "indicator_name": "Industrial Production Index",
            "country": "USA",
            "isic_code": "C",
            "period": date(2023, 1, 1),  # Q1
            "value": 10.0,
            "unit": "IX",
            "frequency": "quarterly",
        },
        {
            "indicator_code": "MEI_IP",
            "indicator_name": "Industrial Production Index",
            "country": "USA",
            "isic_code": "C",
            "period": date(2023, 4, 1),  # Q2
            "value": 40.0,
            "unit": "IX",
            "frequency": "quarterly",
        },
    ]
    out = interpolate_quarterly_to_monthly(quarterly)
    by_period = {r["period"]: r["value"] for r in out}
    # Linear between Jan=10 and Apr=40 → Feb=20, Mar=30; then flat Q2 May/Jun=40.
    assert by_period[date(2023, 1, 1)] == 10.0
    assert by_period[date(2023, 2, 1)] == 20.0
    assert by_period[date(2023, 3, 1)] == 30.0
    assert by_period[date(2023, 4, 1)] == 40.0
    assert by_period[date(2023, 5, 1)] == 40.0
    assert by_period[date(2023, 6, 1)] == 40.0
    assert all(r["frequency"] == "monthly" for r in out)
    assert len(out) == 6


def test_fixture_quarterly_then_interpolate_expands():
    payload = load_fixture("sdmx_ip_quarterly_usa.json")
    records = parse_sdmx_json(
        payload,
        indicator_code="MEI_IP",
        indicator_name="Industrial Production Index",
        isic_code="C",
        country_filter="USA",
        activity_filter="C",
    )
    assert all(r["frequency"] == "quarterly" for r in records)
    out = interpolate_quarterly_to_monthly(records)
    assert all(r["frequency"] == "monthly" for r in out)
    assert len(out) >= 6
    months = {r["period"].month for r in out}
    assert 1 in months and 2 in months and 3 in months


def test_annual_step_hold_expands_indigo_style():
    from crawlers.oecd.sdmx_client import expand_annual_to_monthly_step

    annual = [
        {
            "indicator_code": "INDIGO",
            "indicator_name": "Digital Trade Openness Index",
            "country": "VNM",
            "isic_code": None,
            "period": date(2020, 1, 1),
            "value": 0.02,
            "unit": "IX",
            "frequency": "annual",
            "source": "OECD",
        },
        {
            "indicator_code": "INDIGO",
            "indicator_name": "Digital Trade Openness Index",
            "country": "VNM",
            "isic_code": None,
            "period": date(2021, 1, 1),
            "value": 0.03,
            "unit": "IX",
            "frequency": "annual",
            "source": "OECD",
        },
    ]
    out = expand_annual_to_monthly_step(annual)
    assert len(out) == 24
    by_period = {r["period"]: r["value"] for r in out}
    assert by_period[date(2020, 1, 1)] == 0.02
    assert by_period[date(2020, 12, 1)] == 0.02
    assert by_period[date(2021, 6, 1)] == 0.03
    assert all(r["frequency"] == "monthly" for r in out)