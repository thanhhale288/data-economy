"""CLI: ``python -m ml.shop_matcher`` — train / evaluate shop matcher v2."""

from __future__ import annotations

import argparse
import json
import sys

from ml.shop_matcher.evaluate import (
    ensure_qa_sample_file,
    evaluate_matchers,
    load_qa_sample,
)
from ml.shop_matcher.hybrid import HybridShopMatcher


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Shop matcher v2 — hybrid RapidFuzz + vector/rerank"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_train = sub.add_parser("train", help="Fit aliases + embedder; write joblib")
    p_train.add_argument(
        "--backend",
        choices=["auto", "sentence_transformers", "tfidf"],
        default="auto",
        help="Vector backend (default auto: ST if available else TF-IDF)",
    )
    p_train.add_argument(
        "--artifact",
        default=None,
        help="Optional joblib path (default data/models/shop_matcher.joblib)",
    )

    p_eval = sub.add_parser("evaluate", help="QA gate report vs fuzzy baseline")
    p_eval.add_argument(
        "--backend",
        choices=["auto", "sentence_transformers", "tfidf"],
        default="tfidf",
        help="Hybrid vector backend for the report (default tfidf for offline CI)",
    )
    p_eval.add_argument(
        "--sample",
        default=None,
        help="QA sample JSON (default data/seeds/shop_matcher_qa_sample.json)",
    )
    p_eval.add_argument(
        "--train-first",
        action="store_true",
        help="Train hybrid (and persist artifact) before evaluating",
    )

    args = parser.parse_args(argv)

    if args.cmd == "train":
        from pathlib import Path

        kwargs: dict = {"embedder_backend": args.backend}
        if args.artifact:
            kwargs["model_path"] = Path(args.artifact)
        matcher = HybridShopMatcher(**kwargs)
        summary = matcher.train()
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "evaluate":
        from pathlib import Path

        sample_path = ensure_qa_sample_file(
            Path(args.sample) if args.sample else None
        )
        rows = load_qa_sample(sample_path)
        hybrid = HybridShopMatcher(embedder_backend=args.backend)
        if args.train_first:
            hybrid.train()
        report = evaluate_matchers(rows, hybrid=hybrid)
        slim = {k: v for k, v in report.items() if k != "details"}
        print(json.dumps(slim, indent=2, ensure_ascii=False))
        return 0 if report["gate_pass"] else 2

    return 1


if __name__ == "__main__":
    sys.exit(main())
