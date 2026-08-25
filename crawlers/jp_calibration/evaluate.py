"""Blind eval of T03 URL-finder on the Japan 300, then open silver labels."""

from __future__ import annotations

import csv
import json
import logging
from collections import defaultdict
from typing import Any

from crawlers.jp_calibration.identity import load_jp_identity, load_jp_labels
from crawlers.jp_calibration.paths import (
    COMPARISON_FILE,
    ERROR_ANALYSIS_FILE,
    IDENTITY_FILE,
    LABELS_FILE,
    METRICS_FILE,
    PAGE_CACHE_DIR,
    PREDICTIONS_FILE,
    PROCESSED_DIR,
    REVIEW_CSV,
    RQ3_FILE,
    SAMPLE_MANIFEST,
    SERP_CACHE_DIR,
    VN_METRICS_FILE,
)
from crawlers.url_finder.evaluate import render_error_analysis, score_prediction, summarize
from crawlers.url_finder.evidence import PageFetcher
from crawlers.url_finder.identity import sha256_file, utcnow_iso
from crawlers.url_finder.pipeline import find_url
from crawlers.url_finder.search import SearchClient

logger = logging.getLogger(__name__)

JP_CAVEAT = (
    "Japan n≈300 manufacturing 株式会社 in Shizuoka/Aichi/Osaka with a gBizINFO "
    "website URL (silver). Not a national estimate. Silver labels are self-reported "
    "and can be stale (T16 will measure that). When search is blocked, scores are "
    "domain-hypothesis + on-page evidence only — same method as T03 v0."
)

RQ3_TEXT = """# RQ3 — logic changes required to run Japan (T08)

T08 rule: reuse the T03 URL-finder; only locale config should change.
Anything below is a *recorded* exception, not a silent fork.

## Must-fix (scoring would collapse without it)

1. **`crawlers/url_finder/domain.py` — Japanese 2nd-level TLDs.**
   `toyota.co.jp` was parsed as eTLD+1 `co.jp` (last two labels). Added
   `.co.jp`, `.or.jp`, `.ne.jp`, `.ac.jp`, `.go.jp`, `.ed.jp`, `.gr.jp`, `.lg.jp`
   to the existing multi-part TLD list. Vietnam `.com.vn` behaviour is unchanged.

## Config-lifting (same scores on Vietnam if `vi.json` matches the old constants)

2. **TLD bonuses** moved from `if locale == "vi"` in `evidence.py` to
   `evidence.tld_bonuses` in the locale JSON. `ja.json` prefers `.co.jp` / `.jp`.
3. **`accept_language`** is read from locale JSON in `SearchClient` and
   `PageFetcher` (was hard-coded `vi-VN`).
4. **`PageFetcher(locale=...)`** is passed from `find_url` so Japan fetches send
   `Accept-Language: ja`.

## Adapter, not a scoring fork

5. **Japan identity loader** (`crawlers/jp_calibration/identity.py`) accepts a
   13-digit 法人番号 as `ticker`/`tax_id`. The Vietnam `load_identity` 10-digit
   MST check is untouched. The finder still receives the same five fields
   (`ticker`, `legal_name`, `tax_id`, `address`, `aliases`).
6. **Forbidden identity keys** gained `company_url` / `homepage_url` so a gBizINFO
   field name cannot leak into the finder table.

## Known non-fixes (transferability evidence)

7. Hypothesis slugs still come from `[a-z0-9]+` after fold — kanji/kana names
   produce no slug unless `aliases` carry romaji/English (filled from NTA
   `enName` / furigana). That is why T08 identity keeps those aliases.
8. Address-token evidence uses a Latin/Vietnamese token regex; Japanese addresses
   rarely contribute `address_tokens`. Not patched.
9. `tax_id_on_page` is a raw substring of the 13-digit number; hyphenated 法人番号
   on pages will miss. Not patched.
10. Search is still DuckDuckGo HTML. If it returns HTTP 202, Japan is
    hypothesis-first — the same limitation as T03.

Scoring (`decide_rules`, `score_html` weights, `classify_error`) was not rewritten
per country.
"""


STRATUM_ORDER = ("0-20", "21-50", "51-300", "301+")


def _bucket_sort_key(key: str, order: tuple[str, ...] = STRATUM_ORDER) -> tuple[int, str]:
    try:
        return (order.index(key), key)
    except ValueError:
        return (len(order), key)


def _summarize_by_stratum(scored: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        buckets[str(row.get("employee_stratum") or "unknown")].append(row)
    return {
        key: summarize(rows)
        for key, rows in sorted(buckets.items(), key=lambda item: _bucket_sort_key(item[0]))
    }


def stamp_jp_caveat(metrics: dict[str, Any]) -> dict[str, Any]:
    """Replace the T03 n=28 caveat that `summarize()` stamps on every bucket."""
    metrics["caveat"] = JP_CAVEAT
    for group in ("by_stratum", "by_prefecture"):
        for part in (metrics.get(group) or {}).values():
            part["caveat"] = JP_CAVEAT
    return metrics


def run_finder(
    *,
    locale: str = "ja",
    allow_llm: bool = False,
    fetch_pages: bool = True,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    identities = load_jp_identity()
    if limit is not None:
        identities = identities[: max(0, limit)]
    predictions: list[dict[str, Any]] = []
    with SearchClient(locale=locale, cache_dir=SERP_CACHE_DIR) as searcher, PageFetcher(
        locale=locale, cache_dir=PAGE_CACHE_DIR
    ) as fetcher:
        for identity in identities:
            result = find_url(
                identity,
                searcher=searcher,
                fetcher=fetcher,
                locale=locale,
                allow_llm=allow_llm,
                fetch_pages=fetch_pages,
            )
            predictions.append(result)
            logger.info(
                "%s abstain=%s url=%s reason=%s",
                result["ticker"],
                result["abstain"],
                result["predicted_url"],
                result["reason"],
            )
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    PREDICTIONS_FILE.write_text(
        json.dumps(predictions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return predictions


def open_labels_and_score(predictions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if predictions is None:
        predictions = json.loads(PREDICTIONS_FILE.read_text(encoding="utf-8"))
    labels = load_jp_labels()
    scored: list[dict[str, Any]] = []
    missing: list[str] = []
    for pred in predictions:
        ticker = str(pred["ticker"])
        gold = labels.get(ticker)
        if gold is None:
            missing.append(ticker)
            continue
        row = score_prediction(
            ticker=ticker,
            predicted_url=pred.get("predicted_url"),
            abstain=bool(pred.get("abstain")),
            gold_url=gold["gold_url"],
            backend=str(pred.get("backend") or "rules"),
            reason=str(pred.get("reason") or ""),
        )
        row["employee_stratum"] = gold.get("employee_stratum") or ""
        row["prefecture"] = gold.get("prefecture") or ""
        scored.append(row)
    metrics = summarize(scored)
    metrics["missing_label"] = missing
    metrics["identity_sha256"] = sha256_file(IDENTITY_FILE)
    metrics["labels_sha256"] = sha256_file(LABELS_FILE)
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
    metrics["by_stratum"] = _summarize_by_stratum(scored)
    pref_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        pref_buckets[str(row.get("prefecture") or "unknown")].append(row)
    metrics["by_prefecture"] = {
        key: summarize(rows) for key, rows in sorted(pref_buckets.items())
    }
    stamp_jp_caveat(metrics)
    METRICS_FILE.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    ERROR_ANALYSIS_FILE.write_text(
        _render_jp_analysis(scored, metrics), encoding="utf-8"
    )
    _write_review_sheet(scored)
    _write_comparison(metrics)
    RQ3_FILE.write_text(RQ3_TEXT, encoding="utf-8")
    return metrics


def _render_jp_analysis(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> str:
    header = render_error_analysis(rows, metrics)
    extra = [
        "",
        "## Japan strata",
        "",
    ]
    for key, part in (metrics.get("by_stratum") or {}).items():
        extra.append(
            f"- {key}: n={part['n']} hit-rate={part['hit_rate']:.1%} "
            f"precision={part['precision_among_decided']:.1%} "
            f"abstain={part['abstain_rate']:.1%}"
        )
    extra.extend(["", "## Silver-label caveat", "", metrics["caveat"], ""])
    # Strip the VN 28-firm advisor blurb; keep the table.
    lines = header.splitlines()
    cut = []
    for line in lines:
        if line.startswith("## Ghi chú"):
            break
        cut.append(line)
    cut[0] = "# URL-finder — Japan calibration (gBizINFO silver, T08)"
    return "\n".join(cut + extra) + "\n"


def _write_review_sheet(rows: list[dict[str, Any]], n: int = 30) -> None:
    order = {"wrong_other": 0, "wrong_related_domain": 1, "abstain": 2, "hit": 3}
    ranked = sorted(rows, key=lambda r: (order.get(r["error_type"], 9), r["ticker"]))
    picked = ranked[:n]
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with REVIEW_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "ticker",
                "error_type",
                "predicted_url",
                "gold_url",
                "reason",
                "employee_stratum",
                "prefecture",
                "human_silver_ok",
                "human_error_owner",
                "human_notes",
            ],
        )
        writer.writeheader()
        for row in picked:
            writer.writerow(
                {
                    "ticker": row["ticker"],
                    "error_type": row["error_type"],
                    "predicted_url": row.get("predicted_url") or "",
                    "gold_url": row.get("gold_url") or "",
                    "reason": row.get("reason") or "",
                    "employee_stratum": row.get("employee_stratum") or "",
                    "prefecture": row.get("prefecture") or "",
                    "human_silver_ok": "",
                    "human_error_owner": "",
                    "human_notes": "",
                }
            )


def _write_comparison(jp: dict[str, Any]) -> None:
    vn: dict[str, Any] = {}
    if VN_METRICS_FILE.exists():
        vn = json.loads(VN_METRICS_FILE.read_text(encoding="utf-8"))
    lines = [
        "# T03 Vietnam n=28 vs T08 Japan n≈300",
        "",
        "Same URL-finder (rules, hypothesis-first when search is blocked). "
        "Japan labels are gBizINFO silver URLs, not hand gold.",
        "",
        "| metric | VN listed 28 | JP manufacturing 300 |",
        "|--------|--------------|----------------------|",
    ]

    def fmt(metrics: dict[str, Any], key: str) -> str:
        if not metrics:
            return "—"
        value = metrics.get(key)
        if isinstance(value, float):
            return f"{value:.1%}" if key.endswith("rate") or "precision" in key or "recall" in key else f"{value:.4f}"
        return str(value)

    for key in (
        "n",
        "hits",
        "abstain",
        "wrong",
        "hit_rate",
        "precision_among_decided",
        "recall",
        "abstain_rate",
    ):
        lines.append(f"| {key} | {fmt(vn, key)} | {fmt(jp, key)} |")
    lines.extend(
        [
            "",
            f"- VN search_blocked: {vn.get('search_blocked')} ({vn.get('search_block_detail') or ''})",
            f"- JP search_blocked: {jp.get('search_blocked')} ({jp.get('search_block_detail') or ''})",
            f"- identity_sha256: `{jp.get('identity_sha256')}`",
            f"- labels_sha256: `{jp.get('labels_sha256')}`",
            "",
        ]
    )
    if SAMPLE_MANIFEST.exists():
        manifest = json.loads(SAMPLE_MANIFEST.read_text(encoding="utf-8"))
        lines.append(f"- sample seed: {manifest.get('seed')}; prefectures: {manifest.get('prefectures')}")
        lines.append(
            f"- nta_join_hits: {manifest.get('nta_join_hits')}/{manifest.get('n')}; "
            f"skipped_no_url (gBizINFO profile had no website): {manifest.get('skipped_no_url')}"
        )
        lines.append("")
    lines.extend(
        [
            "## By employment stratum (Japan)",
            "",
            "| stratum | n | hits | hit_rate | precision_among_decided | abstain_rate |",
            "|---------|---|------|----------|-------------------------|--------------|",
        ]
    )
    for key, part in (jp.get("by_stratum") or {}).items():
        lines.append(
            f"| {key} | {part['n']} | {part['hits']} | {part['hit_rate']:.1%} | "
            f"{part['precision_among_decided']:.1%} | {part['abstain_rate']:.1%} |"
        )
    lines.extend(
        [
            "",
            "These two samples are **not** the same population: T03 is 28 listed Vietnamese "
            "manufacturers already known to have a website; T08 is 300 Japanese 株式会社 with "
            "a gBizINFO silver URL, stratified by employment, mostly without a live search "
            "engine. Hit-rate drop is expected; it is not a country ranking.",
            "",
        ]
    )
    COMPARISON_FILE.write_text("\n".join(lines), encoding="utf-8")
