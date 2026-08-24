"""Schema validation for local LLM extraction."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ml.local_llm.schema import (
    ExtractionResult,
    abstain_result,
    extraction_json_schema,
    parse_extraction,
)


def _ok_result() -> dict:
    return {
        "has_product_catalog": {
            "value": True,
            "confidence": 0.9,
            "abstain": False,
            "reason": "product list",
        },
        "has_order_cart": {
            "value": True,
            "confidence": 0.8,
            "abstain": False,
            "reason": "add to cart",
        },
        "payment_methods": {
            "value": ["vnpay", "momo", "cod"],
            "confidence": 0.85,
            "abstain": False,
            "reason": "logos",
        },
        "social_links": {
            "value": [{"platform": "facebook", "url": "https://facebook.com/abc"}],
            "confidence": 0.7,
            "abstain": False,
            "reason": "footer",
        },
        "marketplace_links": {
            "value": [{"platform": "shopee", "url": "https://shopee.vn/abc"}],
            "confidence": 0.75,
            "abstain": False,
            "reason": "link",
        },
        "website_language": {
            "value": "vi",
            "confidence": 0.95,
            "abstain": False,
            "reason": "vi copy",
        },
    }


def test_parse_happy_path():
    result = ExtractionResult.model_validate(_ok_result())
    assert result.has_order_cart.value is True
    assert "vnpay" in result.payment_methods.value


def test_parse_json_string():
    import json

    raw = json.dumps(_ok_result(), ensure_ascii=False)
    result = parse_extraction(raw)
    assert result.website_language.value == "vi"


def test_confidence_out_of_range_rejected():
    bad = _ok_result()
    bad["has_order_cart"]["confidence"] = 1.5
    with pytest.raises(ValidationError):
        ExtractionResult.model_validate(bad)


def test_unknown_payment_token_rejected():
    bad = _ok_result()
    bad["payment_methods"]["value"] = ["paypal"]
    with pytest.raises(ValidationError):
        ExtractionResult.model_validate(bad)


def test_extra_keys_rejected():
    bad = _ok_result()
    bad["has_order_cart"]["extra"] = True
    with pytest.raises(ValidationError):
        ExtractionResult.model_validate(bad)


def test_abstain_result_has_no_invented_values():
    result = abstain_result("schema_invalid_after_retry")
    assert result.all_fields_abstain()
    assert result.has_product_catalog.value is None
    assert result.payment_methods.value == []


def test_json_schema_has_required_fields():
    schema = extraction_json_schema()
    assert "has_product_catalog" in schema["properties"]
    assert "marketplace_links" in schema["properties"]
