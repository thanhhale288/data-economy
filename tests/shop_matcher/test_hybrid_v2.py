"""Task #60 — hybrid matcher regression + QA gate vs fuzzy baseline."""

from __future__ import annotations

import json

import pytest

from ml.shop_matcher import (
    BACKEND_ENV,
    DEFAULT_EMBEDDER_BACKEND,
    DEFAULT_THRESHOLD,
    FuzzyShopMatcher,
    HybridShopMatcher,
    ShopMatcher,
    resolve_embedder_backend,
)
from ml.shop_matcher.evaluate import (
    build_default_qa_rows,
    ensure_qa_sample_file,
    evaluate_matchers,
)
from ml.shop_matcher.hybrid import fuse_scores, short_prefix_boost


def test_default_shop_matcher_is_hybrid():
    assert ShopMatcher is HybridShopMatcher
    m = ShopMatcher(embedder_backend="tfidf")
    assert isinstance(m, HybridShopMatcher)
    assert m._embedder_backend_pref == "tfidf"


def test_sentence_transformers_importable():
    from sentence_transformers import SentenceTransformer

    assert SentenceTransformer is not None


def test_short_prefix_boost_rescues_rd_dq():
    assert short_prefix_boost(
        "Công ty Cổ phần Bóng đèn Rạng Đông", "rd_lighting_bulb_store"
    ) >= 0.70
    assert short_prefix_boost(
        "Công ty Cổ phần Điện Quang", "dq_lighting_vn"
    ) >= 0.70
    # Must not fire for wrong company
    assert (
        short_prefix_boost("Tập đoàn FPT", "rd_lighting_bulb_store") == 0.0
    )
    # Must not fire on "radio..." false prefix
    assert (
        short_prefix_boost(
            "Công ty Cổ phần Bóng đèn Rạng Đông", "radio_shop_vn"
        )
        == 0.0
    )


def test_fuse_scores_midband_and_prefix():
    assert fuse_scores(0.95, 0.1, 0.0) == 0.95
    assert fuse_scores(0.39, 0.2, 0.72) >= 0.70
    assert fuse_scores(0.20, 0.1, 0.0) < DEFAULT_THRESHOLD


@pytest.fixture
def hybrid_tfidf() -> HybridShopMatcher:
    m = HybridShopMatcher(embedder_backend="tfidf")
    rows = build_default_qa_rows()
    from ml.shop_matcher.embeddings import company_embedding_text, shop_embedding_text

    corpus = [
        *[company_embedding_text(r["company"]) for r in rows],
        *[shop_embedding_text(r["shop"]) for r in rows],
    ]
    m._embedder.fit(corpus)
    return m


def test_hybrid_rescues_hard_prefix_positives(hybrid_tfidf: HybridShopMatcher):
    fuzzy = FuzzyShopMatcher()
    hard = [
        ("Công ty Cổ phần Bóng đèn Rạng Đông", "rd_lighting_bulb_store"),
        ("Công ty Cổ phần Điện Quang", "dq_lighting_vn"),
        ("Tập đoàn Hòa Phát", "hpg_steel_official"),
    ]
    for company, shop in hard:
        assert fuzzy.match_score(company, shop) < DEFAULT_THRESHOLD
        assert hybrid_tfidf.is_match(company, shop) is True


def test_hybrid_keeps_seed_precision(hybrid_tfidf: HybridShopMatcher):
    """Seed shops must not false-match other DN (FP=0 on classic negatives)."""
    negatives = [
        ("Tập đoàn Hòa Phát", "rangdong_official"),
        ("Tập đoàn FPT", "vinamilk_official"),
        ("Công ty Cổ phần Sữa Việt Nam", "rangdong_official"),
        ("Công ty Cổ phần Bóng đèn Rạng Đông", "vinamilk_official"),
    ]
    for company, shop in negatives:
        assert hybrid_tfidf.is_match(company, shop) is False


def test_qa_gate_hybrid_beats_fuzzy(tmp_path, hybrid_tfidf: HybridShopMatcher):
    sample_path = tmp_path / "qa.json"
    rows = build_default_qa_rows()
    sample_path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    report = evaluate_matchers(rows, hybrid=hybrid_tfidf)
    assert report["n"] >= 10
    assert report["gate_pass"] is True
    assert report["hybrid"]["recall"] > report["fuzzy"]["recall"]
    assert report["hybrid"]["fp"] <= report["fuzzy"]["fp"]
    assert report["hybrid"]["precision"] >= report["fuzzy"]["precision"]
    assert report["hybrid"]["f1"] > report["fuzzy"]["f1"]


def test_ensure_qa_sample_and_cli_evaluate(tmp_path, monkeypatch):
    sample = tmp_path / "shop_matcher_qa_sample.json"
    ensure_qa_sample_file(sample)
    assert sample.exists()
    rows = json.loads(sample.read_text(encoding="utf-8"))
    assert any(r.get("bucket") == "hard_positive" for r in rows)

    from ml.shop_matcher.__main__ import main

    monkeypatch.setattr(
        "ml.shop_matcher.__main__.ensure_qa_sample_file",
        lambda path=None: sample,
    )
    monkeypatch.setattr(
        "ml.shop_matcher.__main__.load_qa_sample",
        lambda path=None: rows,
    )
    # evaluate with tfidf should exit 0 when gate passes
    rc = main(["evaluate", "--backend", "tfidf"])
    assert rc == 0


def test_hybrid_train_persists_artifact(tmp_path, monkeypatch):
    from ml.shop_matcher import hybrid as hybrid_mod

    artifact = tmp_path / "shop_matcher.joblib"
    monkeypatch.setattr(hybrid_mod, "MODEL_PATH", artifact)
    # Fuzzy train also writes MODEL_PATH — point fuzzy path too via Hybrid model_path
    m = HybridShopMatcher(embedder_backend="tfidf", model_path=artifact)
    summary = m.train()
    assert artifact.exists()
    assert summary["backend"] == "tfidf"
    assert summary["n_pairs"] >= 5

    m2 = HybridShopMatcher(embedder_backend="tfidf", model_path=artifact)
    assert m2.load() is True
    assert m2.is_match(
        "Công ty Cổ phần Bóng đèn Rạng Đông", "rangdong_official"
    )


def test_runtime_backend_env_defaults_to_tfidf(monkeypatch):
    """CI / production: unset env must stay tfidf (no Hub download)."""
    monkeypatch.delenv(BACKEND_ENV, raising=False)
    assert DEFAULT_EMBEDDER_BACKEND == "tfidf"
    assert resolve_embedder_backend() == "tfidf"
    m = ShopMatcher()
    assert m._embedder_backend_pref == "tfidf"
    assert m._embedder.backend_requested == "tfidf"


def test_runtime_backend_env_invalid_falls_back_to_tfidf(monkeypatch):
    monkeypatch.setenv(BACKEND_ENV, "not-a-backend")
    assert resolve_embedder_backend() == "tfidf"
    m = ShopMatcher()
    assert m._embedder_backend_pref == "tfidf"


def test_explicit_backend_wins_over_env(monkeypatch):
    monkeypatch.setenv(BACKEND_ENV, "sentence_transformers")
    assert resolve_embedder_backend("tfidf") == "tfidf"
    m = HybridShopMatcher(embedder_backend="tfidf")
    assert m._embedder_backend_pref == "tfidf"


def test_runtime_backend_env_reads_sentence_transformers_without_loading(monkeypatch):
    """Env is honored, but tests must not construct ST (would hit Hub)."""
    monkeypatch.setenv(BACKEND_ENV, "sentence_transformers")
    assert resolve_embedder_backend() == "sentence_transformers"
    # Skip constructing HybridShopMatcher here — CI must not download Hub.
