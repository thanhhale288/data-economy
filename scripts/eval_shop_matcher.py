#!/usr/bin/env python3
"""Train + evaluate shop matcher v2; print QA gate report JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.shop_matcher.evaluate import (
    ensure_qa_sample_file,
    evaluate_matchers,
    load_qa_sample,
)
from ml.shop_matcher.hybrid import HybridShopMatcher


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        choices=["auto", "sentence_transformers", "tfidf"],
        default="auto",
        help="Vector backend (auto tries sentence-transformers first)",
    )
    parser.add_argument(
        "--sample",
        type=Path,
        default=None,
        help="QA sample JSON path",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Skip writing data/models/shop_matcher.joblib",
    )
    args = parser.parse_args()

    sample_path = ensure_qa_sample_file(args.sample)
    rows = load_qa_sample(sample_path)
    hybrid = HybridShopMatcher(embedder_backend=args.backend)
    train_summary = None
    if not args.no_persist:
        train_summary = hybrid.train()
    else:
        # Fit embedder in-memory on sample + seed via evaluate's lazy path
        pass

    report = evaluate_matchers(rows, hybrid=hybrid)
    slim = {k: v for k, v in report.items() if k != "details"}
    out = {
        "train": train_summary,
        "qa_gate": slim,
        "rescued": [
            d
            for d in report["details"]
            if d["label"] == 1 and d["fuzzy_pred"] == 0 and d["hybrid_pred"] == 1
        ],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
