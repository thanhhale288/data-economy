"""Blind metrics for URL-finder v0. Labels are opened only here."""

from __future__ import annotations

import math
from typing import Any

from crawlers.url_finder.domain import domains_match, registrable_domain


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    p = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = p + z2 / (2.0 * n)
    adj = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)
    low = max(0.0, (centre - adj) / denom)
    high = min(1.0, (centre + adj) / denom)
    return (round(low, 4), round(high, 4))


def classify_error(predicted: str | None, gold: str, abstain: bool) -> str:
    if abstain or not predicted:
        return "abstain"
    if domains_match(predicted, gold):
        return "hit"
    pred_d = registrable_domain(predicted)
    gold_d = registrable_domain(gold)
    pred_core = pred_d.split(".")[0]
    gold_core = gold_d.split(".")[0]
    if pred_core and gold_core and (pred_core in gold_core or gold_core in pred_core):
        return "wrong_related_domain"
    return "wrong_other"


def score_prediction(
    *,
    ticker: str,
    predicted_url: str | None,
    abstain: bool,
    gold_url: str,
    backend: str,
    reason: str,
) -> dict[str, Any]:
    error = classify_error(predicted_url, gold_url, abstain)
    return {
        "ticker": ticker,
        "predicted_url": predicted_url,
        "predicted_domain": registrable_domain(predicted_url) if predicted_url else None,
        "gold_url": gold_url,
        "gold_domain": registrable_domain(gold_url),
        "abstain": bool(abstain or not predicted_url),
        "hit": error == "hit",
        "error_type": error,
        "backend": backend,
        "reason": reason,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    hits = sum(1 for r in rows if r.get("hit"))
    abstain = sum(1 for r in rows if r.get("error_type") == "abstain")
    decided = n - abstain
    wrong = sum(1 for r in rows if r.get("error_type", "").startswith("wrong"))
    precision = (hits / decided) if decided else 0.0
    recall = (hits / n) if n else 0.0
    hit_rate = recall
    return {
        "n": n,
        "hits": hits,
        "abstain": abstain,
        "wrong": wrong,
        "decided": decided,
        "hit_rate": round(hit_rate, 4),
        "precision_among_decided": round(precision, 4),
        "recall": round(recall, 4),
        "abstain_rate": round((abstain / n) if n else 0.0, 4),
        "hit_rate_wilson95": list(wilson_interval(hits, n)),
        "precision_wilson95": list(wilson_interval(hits, decided)) if decided else [0.0, 0.0],
        "error_counts": {
            "hit": hits,
            "abstain": abstain,
            "wrong_related_domain": sum(
                1 for r in rows if r.get("error_type") == "wrong_related_domain"
            ),
            "wrong_other": sum(1 for r in rows if r.get("error_type") == "wrong_other"),
        },
        "caveat": (
            "n=28 listed manufacturers known to have websites. "
            "Not comparable to European 83–88% URL-finding on mixed SME samples. "
            "Wilson 95% CI is wide by design. "
            "When search is blocked, scores reflect domain-hypothesis + on-page "
            "evidence only (not a live SERP URL-finder)."
        ),
    }


def render_error_analysis(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> str:
    lines = [
        "# URL-finder v0 — error analysis (28 listed firms)",
        "",
        f"- n = {metrics['n']}; hits = {metrics['hits']}; abstain = {metrics['abstain']}; wrong = {metrics['wrong']}",
        f"- hit-rate = {metrics['hit_rate']:.1%} (Wilson 95% CI {metrics['hit_rate_wilson95'][0]:.1%}–{metrics['hit_rate_wilson95'][1]:.1%})",
        f"- precision among decided = {metrics['precision_among_decided']:.1%}",
        f"- abstain-rate = {metrics['abstain_rate']:.1%}",
        "",
        metrics["caveat"],
        "",
    ]
    if metrics.get("search_blocked"):
        lines.extend(
            [
                "Search was blocked in this environment "
                f"({metrics.get('search_block_detail') or 'unknown'}). "
                "Candidates are domain hypotheses from legal name / aliases / ticker, "
                "then checked on the page (tax id, name). This is not a live web-search "
                "URL-finder and is not comparable to European 83–88% SME figures.",
                "",
            ]
        )
    if metrics.get("candidate_source_counts"):
        lines.append(f"- candidate sources: {metrics['candidate_source_counts']}")
        lines.append("")
    lines.extend(
        [
            "| ticker | error_type | predicted | gold | reason |",
            "|--------|------------|-----------|------|--------|",
        ]
    )
    order = {"wrong_related_domain": 0, "wrong_other": 1, "abstain": 2, "hit": 3}
    for row in sorted(rows, key=lambda r: (order.get(r["error_type"], 9), r["ticker"])):
        lines.append(
            f"| {row['ticker']} | {row['error_type']} | {row['predicted_url'] or '—'} | "
            f"{row['gold_url']} | {row['reason']} |"
        )
    lines.append("")
    lines.extend(
        [
            "## Ghi chú cho buổi gặp GVHD",
            "",
            "- Con số này là **URL-finder v0 hypothesis-first**: DuckDuckGo HTML bị chặn "
            f"({metrics.get('search_block_detail') or 'blocked'}) nên không dùng được SERP live.",
            "- Ứng viên = suy domain từ tên pháp nhân / alias / ticker + kiểm chứng on-page "
            "(MST, tên, địa chỉ). Không rò rỉ `website_url` từ seed.",
            "- So với công bố châu Âu 83–88%: mẫu khác (28 DN đã biết có website, không phải SME hỗn hợp) "
            "và phương pháp khác (không có search engine ổn định) — **không so trực tiếp**.",
            "- Ca abstain chủ yếu `thin_margin` (hai domain cùng điểm). Ca wrong_related "
            "thường là `.com` ↔ `.com.vn` hoặc brand song song (cùng pháp nhân).",
            "- Ca không suy được từ tên (`idiseafood`, `ttcagris`, `tonnamkim`, `sochemvn`) "
            "cần search API ở vòng sau — đây là giới hạn có chủ đích của v0.",
            "",
        ]
    )
    return "\n".join(lines)
