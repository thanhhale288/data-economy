"""CLI: harvest identity (no URLs) then blind-eval URL-finder on 28 listed firms."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from crawlers.url_finder.evaluate import render_error_analysis, score_prediction, summarize
from crawlers.url_finder.evidence import PageFetcher
from crawlers.url_finder.harvest import harvest_identity_and_labels
from crawlers.url_finder.identity import load_identity, load_labels, sha256_file, utcnow_iso
from crawlers.url_finder.paths import (
    ERROR_ANALYSIS_FILE,
    IDENTITY_FILE,
    LABELS_FILE,
    MANIFEST_FILE,
    METRICS_FILE,
    PREDICTIONS_FILE,
    PROCESSED_DIR,
    SEED_FILE,
)
from crawlers.url_finder.pipeline import find_url
from crawlers.url_finder.search import SearchClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def cmd_harvest(args: argparse.Namespace) -> int:
    identities, labels = harvest_identity_and_labels(locale=args.locale)
    print(f"identity={len(identities)} labels={len(labels)} -> {IDENTITY_FILE}")
    return 0 if len(identities) == 28 else 2


def cmd_eval(args: argparse.Namespace) -> int:
    identities = load_identity()
    # Predictions first — labels stay closed until every firm is scored.
    predictions: list[dict] = []
    with SearchClient(locale=args.locale) as searcher, PageFetcher() as fetcher:
        for identity in identities:
            result = find_url(
                identity,
                searcher=searcher,
                fetcher=fetcher,
                locale=args.locale,
                allow_llm=args.llm,
                fetch_pages=not args.no_fetch,
            )
            predictions.append(result)
            logger.info(
                "%s abstain=%s source=%s url=%s reason=%s",
                result["ticker"],
                result["abstain"],
                result.get("candidate_source"),
                result["predicted_url"],
                result["reason"],
            )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    PREDICTIONS_FILE.write_text(
        json.dumps(predictions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    labels = load_labels()
    scored = []
    missing_label = []
    for pred in predictions:
        ticker = str(pred["ticker"])
        gold = labels.get(ticker)
        if gold is None:
            missing_label.append(ticker)
            continue
        scored.append(
            score_prediction(
                ticker=ticker,
                predicted_url=pred.get("predicted_url"),
                abstain=bool(pred.get("abstain")),
                gold_url=gold["gold_url"],
                backend=str(pred.get("backend") or "rules"),
                reason=str(pred.get("reason") or ""),
            )
        )
    metrics = summarize(scored)
    metrics["missing_label"] = missing_label
    metrics["identity_sha256"] = sha256_file(IDENTITY_FILE)
    metrics["labels_sha256"] = sha256_file(LABELS_FILE)
    metrics["seed_sha256"] = sha256_file(SEED_FILE)
    metrics["generated_at"] = utcnow_iso()
    metrics["search_blocked"] = any(bool(p.get("search_blocked")) for p in predictions)
    metrics["search_block_detail"] = next(
        (str(p.get("search_block_detail") or "") for p in predictions if p.get("search_block_detail")),
        "",
    )
    source_counts: dict[str, int] = {}
    for pred in predictions:
        key = str(pred.get("candidate_source") or "unknown")
        source_counts[key] = source_counts.get(key, 0) + 1
    metrics["candidate_source_counts"] = source_counts
    METRICS_FILE.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    ERROR_ANALYSIS_FILE.write_text(render_error_analysis(scored, metrics), encoding="utf-8")
    manifest = {
        "task": "evol1-t03-url-finder-v0",
        "n_identity": len(identities),
        "n_scored": len(scored),
        "identity_sha256": metrics["identity_sha256"],
        "labels_sha256": metrics["labels_sha256"],
        "predictions": str(PREDICTIONS_FILE),
    }
    MANIFEST_FILE.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: metrics[k] for k in ("n", "hits", "abstain", "wrong", "hit_rate", "precision_among_decided", "recall", "abstain_rate", "hit_rate_wilson95")}, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locale", default="vi")
    sub = parser.add_subparsers(dest="cmd", required=True)

    harvest = sub.add_parser("harvest", help="Build identity_28.json without URL fields")
    harvest.set_defaults(func=cmd_harvest)

    ev = sub.add_parser("eval", help="Blind-eval finder then open labels")
    ev.add_argument("--llm", action="store_true", help="Optional LLM decide (needs API key)")
    ev.add_argument("--no-fetch", action="store_true", help="Score from SERP title/snippet only")
    ev.set_defaults(func=cmd_eval)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
