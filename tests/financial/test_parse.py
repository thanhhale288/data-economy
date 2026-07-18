"""Parser tests for structured BCTC JSON / HTML — no live network."""

from __future__ import annotations

import json
from datetime import date

import pytest

from crawlers.financial.bctc_crawler import parse_bctc_html, parse_bctc_json
from tests.financial.conftest import FIXTURES, load_fixture_text


def test_parse_structured_json_extracts_period_and_fields():
    payload = json.loads(load_fixture_text("bctc_ral_structured.json"))
    report = parse_bctc_json(payload)

    assert report["stock_code"] == "RAL"
    assert report["period"] == date(2024, 12, 31)
    assert report["report_type"] == "annual"
    assert report["revenue"] == 5200000000000
    assert report["net_profit"] == 350000000000
    assert report["employees"] == 3200
    assert report["gross_margin"] == pytest.approx(0.38)
    assert report["source_url"] == "https://example.test/bctc/RAL/2024.json"


def test_parse_structured_json_keeps_null_fields():
    payload = json.loads(load_fixture_text("bctc_partial_nulls.json"))
    report = parse_bctc_json(payload)

    assert report["revenue"] == 162000000000000
    assert report["profit_before_tax"] is None
    assert report["current_assets"] is None
    assert report["operating_expenses"] is None
    assert report["rental_cost"] is None
    assert report["remuneration"] is None
    assert report["employees"] == 32000


def test_parse_html_table_extracts_data_field_attributes():
    html = load_fixture_text("bctc_ral_table.html")
    report = parse_bctc_html(html, stock_code="RAL")

    assert report["stock_code"] == "RAL"
    assert report["period"] == date(2024, 12, 31)
    assert report["report_type"] == "annual"
    assert report["revenue"] == 5200000000000.0
    assert report["employees"] == 3200
    assert report["gross_margin"] == pytest.approx(0.38)
    assert report["source_url"] is None
