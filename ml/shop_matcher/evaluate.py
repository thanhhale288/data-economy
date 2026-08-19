"""QA gate evaluation: fuzzy baseline vs hybrid matcher v2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from ml.shop_matcher.hybrid import HybridShopMatcher
from ml.shop_matcher.matcher import (
    DATA_DIR,
    DEFAULT_THRESHOLD,
    FuzzyShopMatcher,
    labeled_seed_pairs,
)

DEFAULT_QA_SAMPLE_PATH = DATA_DIR / "seeds" / "shop_matcher_qa_sample.json"


def load_qa_sample(path: Path | None = None) -> list[dict[str, Any]]:
    sample_path = path or DEFAULT_QA_SAMPLE_PATH
    if not sample_path.exists():
        return []
    with open(sample_path, encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        raise ValueError(f"QA sample must be a JSON list: {sample_path}")
    return rows


def build_default_qa_rows() -> list[dict[str, Any]]:
    """Labeled sample: seed positives + hard paraphrase / short-prefix cases."""
    rows: list[dict[str, Any]] = []
    for p in labeled_seed_pairs():
        rows.append(
            {
                "company": p["company"],
                "shop": p["shop"],
                "ticker": p["ticker"],
                "label": 1,
                "bucket": "seed_positive",
            }
        )

    hard_positives = [
        ("RAL", "Công ty Cổ phần Bóng đèn Rạng Đông", "rd_lighting_bulb_store"),
        ("RAL", "Công ty Cổ phần Bóng đèn Rạng Đông", "led_chieusang_congnghiep"),
        ("DQC", "Công ty Cổ phần Điện Quang", "dq_lighting_vn"),
        ("VNM", "Công ty Cổ phần Sữa Việt Nam", "sua_tuoi_official_store"),
        ("HPG", "Tập đoàn Hòa Phát", "hpg_steel_official"),
        ("PNJ", "Công ty Cổ phần Vàng bạc Đá quý Phú Nhuận", "pnj_jewelry_gold"),
    ]
    for ticker, company, shop in hard_positives:
        rows.append(
            {
                "company": company,
                "shop": shop,
                "ticker": ticker,
                "label": 1,
                "bucket": "hard_positive",
            }
        )

    hard_negatives = [
        ("HPG", "Tập đoàn Hòa Phát", "rd_lighting_bulb_store"),
        ("FPT", "Tập đoàn FPT", "rd_lighting_bulb_store"),
        ("DQC", "Công ty Cổ phần Điện Quang", "led_chieusang_congnghiep"),
        ("RAL", "Công ty Cổ phần Bóng đèn Rạng Đông", "vinamilk_official"),
        ("VNM", "Công ty Cổ phần Sữa Việt Nam", "rangdong_official"),
        ("MSN", "Tập đoàn Masan", "pnj_jewelry_gold"),
        ("BMP", "Công ty Cổ phần Nhựa Bình Minh", "dq_lighting_vn"),
        ("REE", "Công ty Cổ phần Cơ điện lạnh", "fpt_official"),
    ]
    for ticker, company, shop in hard_negatives:
        rows.append(
            {
                "company": company,
                "shop": shop,
                "ticker": ticker,
                "label": 0,
                "bucket": "hard_negative",
            }
        )

    # Task #75: extra negatives using shop handles already in seed digital_presence.
    seed_negatives = [
        ("HPG", "Tập đoàn Hòa Phát", "rangdong_official"),
        ("FPT", "Tập đoàn FPT", "vinamilk_official"),
        ("BMP", "Công ty Cổ phần Nhựa Bình Minh", "masan_consumer"),
        ("GVR", "Tập đoàn Công nghiệp Cao su Việt Nam", "pnj_official"),
        ("DQC", "Công ty Cổ phần Điện Quang", "fpt_official"),
        ("MSN", "Tập đoàn Masan", "dienquang_officialstore"),
        ("HPG", "Tập đoàn Hòa Phát", "@vinamilk"),
        ("BMP", "Công ty Cổ phần Nhựa Bình Minh", "@pnj"),
    ]
    for ticker, company, shop in seed_negatives:
        rows.append(
            {
                "company": company,
                "shop": shop,
                "ticker": ticker,
                "label": 0,
                "bucket": "seed_negative",
            }
        )
    return rows


def _prf(y_true: Iterable[int], y_pred: Iterable[int]) -> dict[str, float | int]:
    tp = fp = tn = fn = 0
    for t, p in zip(y_true, y_pred, strict=True):
        if p and t:
            tp += 1
        elif p and not t:
            fp += 1
        elif (not p) and t:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate_matchers(
    rows: list[dict[str, Any]] | None = None,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    hybrid: HybridShopMatcher | None = None,
    fuzzy: FuzzyShopMatcher | None = None,
) -> dict[str, Any]:
    """Compare fuzzy-only vs hybrid on a labeled sample; return QA gate report."""
    sample = rows if rows is not None else load_qa_sample()
    if not sample:
        sample = build_default_qa_rows()

    fuzzy_m = fuzzy or FuzzyShopMatcher(threshold=threshold)
    hybrid_m = hybrid or HybridShopMatcher(threshold=threshold, embedder_backend="tfidf")
    # Ensure hybrid embedder sees the sample lexicon
    if not hybrid_m._embedder.is_fitted:
        corpus = []
        for r in sample:
            corpus.append(r["company"])
            corpus.append(r["shop"])
        from ml.shop_matcher.embeddings import company_embedding_text, shop_embedding_text

        corpus = [
            *[company_embedding_text(r["company"]) for r in sample],
            *[shop_embedding_text(r["shop"]) for r in sample],
        ]
        hybrid_m._embedder.fit(corpus)

    y_true = [int(r["label"]) for r in sample]
    fuzzy_scores: list[float] = []
    hybrid_scores: list[float] = []
    details: list[dict[str, Any]] = []

    for r in sample:
        company, shop = r["company"], r["shop"]
        f_score = fuzzy_m.match_score(company, shop)
        h_match = hybrid_m.match(company, shop, threshold=threshold)
        h_score = float(h_match["score"])
        fuzzy_scores.append(f_score)
        hybrid_scores.append(h_score)
        details.append(
            {
                "ticker": r.get("ticker"),
                "shop": shop,
                "label": int(r["label"]),
                "bucket": r.get("bucket"),
                "fuzzy_score": round(f_score, 4),
                "hybrid_score": round(h_score, 4),
                "vector_score": round(float(h_match.get("vector_score") or 0.0), 4),
                "prefix_boost": round(float(h_match.get("prefix_boost") or 0.0), 4),
                "fuzzy_pred": int(f_score >= threshold),
                "hybrid_pred": int(h_score >= threshold),
            }
        )

    fuzzy_pred = [int(s >= threshold) for s in fuzzy_scores]
    hybrid_pred = [int(s >= threshold) for s in hybrid_scores]
    fuzzy_metrics = _prf(y_true, fuzzy_pred)
    hybrid_metrics = _prf(y_true, hybrid_pred)

    improved = (
        hybrid_metrics["f1"] > fuzzy_metrics["f1"]
        and hybrid_metrics["precision"] >= fuzzy_metrics["precision"]
        and hybrid_metrics["fp"] <= fuzzy_metrics["fp"]
    )
    # Also accept equal F1 with strictly fewer FN (recall lift) at same FP
    if not improved:
        improved = (
            hybrid_metrics["f1"] >= fuzzy_metrics["f1"]
            and hybrid_metrics["recall"] > fuzzy_metrics["recall"]
            and hybrid_metrics["fp"] <= fuzzy_metrics["fp"]
            and hybrid_metrics["precision"] >= fuzzy_metrics["precision"]
        )

    return {
        "threshold": threshold,
        "n": len(sample),
        "backend": hybrid_m._embedder.backend,
        "fuzzy": fuzzy_metrics,
        "hybrid": hybrid_metrics,
        "gate_pass": bool(improved),
        "delta": {
            "precision": round(
                float(hybrid_metrics["precision"]) - float(fuzzy_metrics["precision"]),
                4,
            ),
            "recall": round(
                float(hybrid_metrics["recall"]) - float(fuzzy_metrics["recall"]),
                4,
            ),
            "f1": round(float(hybrid_metrics["f1"]) - float(fuzzy_metrics["f1"]), 4),
            "fn": int(hybrid_metrics["fn"]) - int(fuzzy_metrics["fn"]),
            "fp": int(hybrid_metrics["fp"]) - int(fuzzy_metrics["fp"]),
        },
        "details": details,
    }


def ensure_qa_sample_file(path: Path | None = None) -> Path:
    """Write default QA sample JSON if missing; return path."""
    sample_path = path or DEFAULT_QA_SAMPLE_PATH
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    if not sample_path.exists():
        with open(sample_path, "w", encoding="utf-8") as f:
            json.dump(build_default_qa_rows(), f, ensure_ascii=False, indent=2)
            f.write("\n")
    return sample_path


# Re-export helpers used by tests
__all__ = [
    "DEFAULT_QA_SAMPLE_PATH",
    "build_default_qa_rows",
    "ensure_qa_sample_file",
    "evaluate_matchers",
    "load_qa_sample",
]
