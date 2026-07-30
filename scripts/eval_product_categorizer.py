#!/usr/bin/env python3
"""Train + evaluate product categorizer; print precision report JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.product_categorizer import ProductCategorizer, evaluate_precision, load_labels


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--labels",
        type=Path,
        default=None,
        help="Path to labels JSON (default: data/seeds/product_categorizer_labels.json)",
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        default=None,
        help="Where to write/load joblib artifact",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Train in-memory only (do not write artifact)",
    )
    args = parser.parse_args()

    labels = load_labels(args.labels)
    cat = ProductCategorizer(model_path=args.artifact) if args.artifact else ProductCategorizer()
    train_summary = cat.train(labels, persist=not args.no_persist)
    report = evaluate_precision(cat, labels, split="test")
    # Drop per-row details from default stdout for readability; keep counts.
    slim = {k: v for k, v in report.items() if k != "details"}
    out = {"train": train_summary, "test": slim, "test_details": report["details"]}
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
