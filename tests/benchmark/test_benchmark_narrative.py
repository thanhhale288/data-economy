"""Task #61 — Benchmark narrative cites only BenchmarkResult numbers."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.main import app
from backend.app.services.benchmark_narrative import (
    extract_number_tokens,
    generate_benchmark_narrative,
    narrative_numbers_are_honest,
)


def _full_result(**overrides):
    base = {
        "roa": 0.0617,
        "roe": 0.1312,
        "current_ratio": None,
        "equity_ratio": None,
        "revenue_per_worker": None,
        "profit_per_worker": None,
        "profit_margin": None,
        "asset_turnover": None,
        "debt_to_equity": None,
        "percentiles": {"roa": 72.0, "roe": 55.0},
        "industry_averages": {"roa": 0.048, "roe": 0.11},
        "industry_quartiles": {},
        "comparison": {"roa": "above_average", "roe": "average"},
        "peer_count": 2,
        "peer_scope": "vsic_division:27",
        "warnings": ["prototype_listed_sample"],
        "digital": None,
    }
    base.update(overrides)
    return base


def test_narrative_only_contains_input_numbers():
    payload = _full_result()
    out = generate_benchmark_narrative(payload)
    assert out["method"] == "rules"
    assert out["narrative"]
    assert narrative_numbers_are_honest(out["narrative"], payload)
    # Known citations appear in Vietnamese form.
    assert "6.17" in out["narrative"]  # ROA %
    assert "13.12" in out["narrative"]  # ROE %
    assert "72" in out["narrative"] or "72.0" in out["narrative"]
    assert "2" in out["narrative"]  # peer_count
    # Fabricated number must not appear.
    tokens = extract_number_tokens(out["narrative"])
    assert "99.99" not in tokens
    assert "50.00" not in tokens  # no invented median


def test_narrative_missing_roe_does_not_invent():
    payload = _full_result(roe=None, percentiles={"roa": 72.0}, industry_averages={"roa": 0.048})
    # Clear roe-related peer stats so they aren't citeable.
    payload["percentiles"].pop("roe", None)
    payload["industry_averages"].pop("roe", None)
    payload["comparison"].pop("roe", None)

    out = generate_benchmark_narrative(payload)
    assert "roe" in out["omitted"]
    assert "Thiếu ROE" in out["narrative"]
    assert narrative_numbers_are_honest(out["narrative"], payload)
    # Must not invent a ROE percent like 13.12 when roe is null.
    assert "13.12" not in out["narrative"]


def test_narrative_insufficient_peers_no_fake_percentile():
    payload = _full_result(
        percentiles={"roa": None, "roe": None},
        industry_averages={},
        comparison={"roa": "insufficient_peers", "roe": "insufficient_peers"},
        peer_count=0,
        peer_scope="vsic_division:11",
        warnings=["insufficient_peers"],
    )
    out = generate_benchmark_narrative(payload)
    assert "insufficient_peers" in out["narrative"]
    assert "không suy diễn" in out["narrative"].lower() or "không bịa" in out["narrative"].lower()
    assert narrative_numbers_are_honest(out["narrative"], payload)
    # No invented peer median percentile token.
    for token in extract_number_tokens(out["narrative"]):
        assert token != "50"
        assert token != "50.0"


def test_narrative_endpoint_openapi_and_honesty(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        openapi = client.get("/openapi.json")
        assert openapi.status_code == 200
        assert "/api/benchmark/narrative" in openapi.json()["paths"]

        payload = _full_result()
        res = client.post("/api/benchmark/narrative", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["narrative"]
        assert body["method"] == "rules"
        assert narrative_numbers_are_honest(body["narrative"], payload)
        assert any(c["field"] == "roa" for c in body["citations"])
    finally:
        app.dependency_overrides.clear()


def test_llm_missing_key_uses_rules(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BENCHMARK_NARRATIVE_LLM_KEY", raising=False)
    out = generate_benchmark_narrative(_full_result())
    assert out["method"] == "rules"


def _honest_benchmark_llm_text() -> str:
    """Numbers already citeable from _full_result() — honesty gate must still pass."""
    return "ROA của doanh nghiệp là 6.17%. ROE là 13.12%. Phân vị 72. Peer 2."


def _patch_httpx_post(monkeypatch, captured: dict):
    import httpx

    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": [{"message": {"content": captured.get("content", _honest_benchmark_llm_text())}}]}

    def fake_post(url, *args, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        return _Resp()

    monkeypatch.setattr(httpx, "post", fake_post)


def test_llm_posts_default_openai_url(monkeypatch):
    monkeypatch.setenv("BENCHMARK_NARRATIVE_LLM_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BENCHMARK_NARRATIVE_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("NARRATIVE_LLM_BASE_URL", raising=False)
    captured: dict = {}
    _patch_httpx_post(monkeypatch, captured)
    out = generate_benchmark_narrative(_full_result())
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["json"]["model"] == "gpt-4o-mini"
    assert out["method"] == "llm"


def test_llm_posts_gemini_openai_compatible_url(monkeypatch):
    monkeypatch.setenv("BENCHMARK_NARRATIVE_LLM_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv(
        "BENCHMARK_NARRATIVE_LLM_BASE_URL",
        "https://generativelanguage.googleapis.com/v1beta/openai",
    )
    monkeypatch.setenv("NARRATIVE_LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("BENCHMARK_NARRATIVE_LLM_MODEL", "gemini-2.0-flash")
    captured: dict = {}
    _patch_httpx_post(monkeypatch, captured)
    out = generate_benchmark_narrative(_full_result())
    assert captured["url"] == (
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    )
    assert captured["json"]["model"] == "gemini-2.0-flash"
    assert out["method"] == "llm"


def test_llm_full_endpoint_kept_as_is(monkeypatch):
    monkeypatch.setenv("BENCHMARK_NARRATIVE_LLM_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv(
        "BENCHMARK_NARRATIVE_LLM_BASE_URL",
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions/",
    )
    monkeypatch.delenv("NARRATIVE_LLM_BASE_URL", raising=False)
    captured: dict = {}
    _patch_httpx_post(monkeypatch, captured)
    generate_benchmark_narrative(_full_result())
    assert captured["url"] == (
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    )


def test_llm_shared_base_url_fallback(monkeypatch):
    monkeypatch.setenv("BENCHMARK_NARRATIVE_LLM_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BENCHMARK_NARRATIVE_LLM_BASE_URL", raising=False)
    monkeypatch.setenv("NARRATIVE_LLM_BASE_URL", "https://api.openai.com/v1")
    captured: dict = {}
    _patch_httpx_post(monkeypatch, captured)
    generate_benchmark_narrative(_full_result())
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"


def test_llm_invented_number_falls_back_to_rules(monkeypatch):
    monkeypatch.setenv("BENCHMARK_NARRATIVE_LLM_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BENCHMARK_NARRATIVE_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("NARRATIVE_LLM_BASE_URL", raising=False)
    captured: dict = {"content": "ROA nhảy lên 99.99% so với peer."}
    _patch_httpx_post(monkeypatch, captured)
    out = generate_benchmark_narrative(_full_result())
    assert out["method"] == "rules"
    assert "99.99" not in out["narrative"]
    assert "llm_fallback_rules" in out["warnings"]
