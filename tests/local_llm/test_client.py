"""Local LLM client: schema ok, retry, abstain, pin mismatch — no live lab calls."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from ml.local_llm.client import (
    LocalLlmSettings,
    PinMismatchError,
    extract_page,
    load_pin,
    verify_pin,
)
from ml.local_llm.schema import ExtractionResult

FIXTURE = Path(__file__).parent / "fixtures" / "page_shop.txt"
PINNED = load_pin()


def _valid_payload() -> dict:
    return {
        "has_product_catalog": {
            "value": True,
            "confidence": 0.9,
            "abstain": False,
            "reason": "catalog",
        },
        "has_order_cart": {
            "value": True,
            "confidence": 0.85,
            "abstain": False,
            "reason": "cart",
        },
        "payment_methods": {
            "value": ["vnpay", "momo", "cod"],
            "confidence": 0.8,
            "abstain": False,
            "reason": "pay",
        },
        "social_links": {
            "value": [{"platform": "facebook", "url": "https://facebook.com/abc"}],
            "confidence": 0.7,
            "abstain": False,
            "reason": "fb",
        },
        "marketplace_links": {
            "value": [{"platform": "shopee", "url": "https://shopee.vn/abc"}],
            "confidence": 0.75,
            "abstain": False,
            "reason": "shopee",
        },
        "website_language": {
            "value": "vi",
            "confidence": 0.9,
            "abstain": False,
            "reason": "vi",
        },
    }


def _chat_response(content: str) -> dict:
    return {
        "model": PINNED["model"],
        "message": {"role": "assistant", "content": content},
        "done": True,
        "prompt_eval_count": 100,
        "eval_count": 50,
        "eval_duration": 1_000_000_000,
        "total_duration": 1_200_000_000,
        "load_duration": 100_000_000,
    }


def _tags_ok() -> dict:
    return {
        "models": [
            {
                "name": PINNED["model"],
                "digest": PINNED["digest"],
                "details": {
                    "quantization_level": PINNED["quantization"],
                    "parameter_size": PINNED["parameter_size"],
                },
            }
        ]
    }


def _settings() -> LocalLlmSettings:
    return LocalLlmSettings.from_pin_and_env(PINNED)


def _client(handler) -> httpx.Client:
    return httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://ollama.test",
    )


def test_extract_ok_first_attempt():
    calls = {"chat": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/chat":
            calls["chat"] += 1
            body = json.loads(request.content.decode())
            assert body["stream"] is False
            assert body["think"] is False
            assert body["options"]["temperature"] == 0
            assert body["options"]["seed"] == 42
            assert isinstance(body["format"], dict)
            assert "has_product_catalog" in body["format"]["properties"]
            return httpx.Response(200, json=_chat_response(json.dumps(_valid_payload())))
        return httpx.Response(404, json={"error": "unexpected"})

    with _client(handler) as http:
        out = extract_page(FIXTURE.read_text(encoding="utf-8"), http=http, settings=_settings())
    assert out.decision == "ok"
    assert out.attempts == 1
    assert out.result.has_order_cart.value is True
    assert calls["chat"] == 1


def test_extract_retry_then_ok():
    calls = {"chat": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path != "/api/chat":
            return httpx.Response(404)
        calls["chat"] += 1
        if calls["chat"] == 1:
            return httpx.Response(200, json=_chat_response("not-json{{{"))
        return httpx.Response(200, json=_chat_response(json.dumps(_valid_payload())))

    with _client(handler) as http:
        out = extract_page("gio hang VNPay", http=http, settings=_settings())
    assert out.decision == "retry_ok"
    assert out.attempts == 2
    assert out.result.payment_methods.value


def test_extract_abstains_after_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path != "/api/chat":
            return httpx.Response(404)
        return httpx.Response(200, json=_chat_response('{"broken": true}'))

    with _client(handler) as http:
        out = extract_page("text", http=http, settings=_settings())
    assert out.decision == "abstain"
    assert out.attempts == 3
    assert out.result.all_fields_abstain()
    assert out.result.has_product_catalog.value is None


def test_verify_pin_ok():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json=_tags_ok())
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.17.4"})
        return httpx.Response(404)

    with _client(handler) as http:
        info = verify_pin(http, _settings())
    assert info["digest"] == PINNED["digest"]
    assert info["ollama_version"] == "0.17.4"


def test_verify_pin_digest_mismatch():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            bad = _tags_ok()
            bad["models"][0]["digest"] = "deadbeef" * 8
            return httpx.Response(200, json=bad)
        return httpx.Response(404)

    with _client(handler) as http:
        with pytest.raises(PinMismatchError, match="Digest mismatch"):
            verify_pin(http, _settings())


def test_extract_with_verify_records_digest():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json=_tags_ok())
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.17.4"})
        if request.url.path == "/api/chat":
            return httpx.Response(200, json=_chat_response(json.dumps(_valid_payload())))
        return httpx.Response(404)

    with _client(handler) as http:
        out = extract_page("x", http=http, settings=_settings(), verify=True)
    assert out.digest == PINNED["digest"]
    assert out.decision == "ok"


def test_pin_file_matches_expected_model():
    assert PINNED["model"] == "qwen3:8b"
    assert PINNED["think"] is False
    assert len(PINNED["digest"]) == 64
