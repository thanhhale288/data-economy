"""Score tier-1 / tier-2 predictions against human gold on the mini-gold worksheet."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Literal

from crawlers.mini_gold.paths import (
    ALL_FIELDS,
    BOOL_FIELDS,
    ERROR_ANALYSIS_MD,
    LANG_FIELD,
    METRICS_JSON,
    PAYMENT_FIELD,
    PREDICTIONS_VS_GOLD_CSV,
    PRESENCE_FIELDS,
    PROCESSED_DIR,
    WORKSHEET_CSV,
)

TierName = Literal["tier1", "tier2"]
Outcome = Literal["hit", "wrong", "abstain_pred", "abstain_gold", "skip"]


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


def _norm_token(raw: str) -> str:
    return (raw or "").strip().lower()


def parse_gold_bool(raw: str) -> tuple[bool | None, bool]:
    """Return (value, is_abstain). value is None when abstain."""
    t = _norm_token(raw)
    if t in {"", "abstain"}:
        return None, True
    if t in {"true", "1", "yes"}:
        return True, False
    if t in {"false", "0", "no"}:
        return False, False
    raise ValueError(f"invalid gold bool: {raw!r}")


def parse_gold_presence(raw: str) -> tuple[bool | None, bool]:
    return parse_gold_bool(raw)


def parse_gold_payment(raw: str) -> tuple[frozenset[str] | None, bool]:
    t = (raw or "").strip()
    if _norm_token(t) == "abstain":
        return None, True
    # Empty string = decided "no payment methods observed" (not abstain).
    tokens = frozenset(x for x in (_norm_token(p) for p in t.split(",")) if x)
    return tokens, False


def parse_gold_lang(raw: str) -> tuple[str | None, bool]:
    t = _norm_token(raw)
    if t in {"", "abstain"}:
        return None, True
    return t, False


def parse_pred_bool(raw: str) -> tuple[bool | None, bool]:
    t = _norm_token(raw)
    if t in {"abstain", "null", ""}:
        return None, True
    if t in {"true", "1", "yes"}:
        return True, False
    if t in {"false", "0", "no"}:
        return False, False
    return None, True


def parse_pred_presence(raw: str) -> tuple[bool | None, bool]:
    return parse_pred_bool(raw)


def parse_pred_payment(raw: str) -> tuple[frozenset[str] | None, bool]:
    t = (raw or "").strip()
    if _norm_token(t) == "abstain":
        return None, True
    tokens = frozenset(x for x in (_norm_token(p) for p in t.split(",")) if x)
    return tokens, False


def parse_pred_lang(raw: str) -> tuple[str | None, bool]:
    t = _norm_token(raw)
    if t in {"", "abstain", "null"}:
        return None, True
    return t, False


def score_field(
    *,
    field: str,
    gold_raw: str,
    pred_raw: str,
) -> Outcome:
    if field in BOOL_FIELDS:
        gold, g_abs = parse_gold_bool(gold_raw)
        pred, p_abs = parse_pred_bool(pred_raw)
    elif field in PRESENCE_FIELDS:
        gold, g_abs = parse_gold_presence(gold_raw)
        pred, p_abs = parse_pred_presence(pred_raw)
    elif field == PAYMENT_FIELD:
        gold, g_abs = parse_gold_payment(gold_raw)
        pred, p_abs = parse_pred_payment(pred_raw)
    elif field == LANG_FIELD:
        gold, g_abs = parse_gold_lang(gold_raw)
        pred, p_abs = parse_pred_lang(pred_raw)
    else:
        raise ValueError(f"unknown field: {field}")

    if g_abs:
        return "abstain_gold"
    if p_abs:
        return "abstain_pred"
    if field == PAYMENT_FIELD:
        # Presence-compatible: empty set == no methods seen
        assert gold is not None and pred is not None
        g_pres = len(gold) > 0 and gold != frozenset({"none"})
        p_pres = len(pred) > 0 and pred != frozenset({"none"})
        # Also allow exact token-set match when both non-empty
        if gold == pred:
            return "hit"
        if g_pres == p_pres and (not g_pres):
            return "hit"
        if g_pres == p_pres and gold == pred:
            return "hit"
        # Same presence, different tokens → still count as hit on presence metric
        if g_pres == p_pres:
            return "hit"
        return "wrong"
    if field == LANG_FIELD:
        assert gold is not None and pred is not None
        if gold == pred:
            return "hit"
        if gold in {"unknown"} or pred in {"unknown"}:
            return "hit"
        return "wrong"
    assert gold is not None and pred is not None
    return "hit" if gold == pred else "wrong"


def load_worksheet(path: Path = WORKSHEET_CSV) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _pred_col(tier: TierName, field: str) -> str:
    prefix = "pre_t1" if tier == "tier1" else "pre_t2"
    return f"{prefix}_{field}"


def evaluate_worksheet(
    rows: list[dict[str, str]] | None = None,
    *,
    path: Path | None = None,
    require_reviewed: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = WORKSHEET_CSV if path is None else path
    rows = rows if rows is not None else load_worksheet(path)
    scored: list[dict[str, Any]] = []
    for row in rows:
        reviewed = _norm_token(row.get("reviewed") or "") in {"true", "1", "yes"}
        if require_reviewed and not reviewed:
            continue
        firm_id = row.get("firm_id") or ""
        for tier in ("tier1", "tier2"):
            for field in ALL_FIELDS:
                gold_raw = row.get(f"gold_{field}") or ""
                pred_raw = row.get(_pred_col(tier, field)) or ""  # type: ignore[arg-type]
                outcome = score_field(field=field, gold_raw=gold_raw, pred_raw=pred_raw)
                scored.append(
                    {
                        "firm_id": firm_id,
                        "source_cohort": row.get("source_cohort") or "",
                        "website_url": row.get("website_url") or "",
                        "tier": tier,
                        "field": field,
                        "gold": gold_raw,
                        "pred": pred_raw,
                        "outcome": outcome,
                        "notes": row.get("notes") or "",
                    }
                )
    metrics = summarize_metrics(scored, n_firms=len({r["firm_id"] for r in scored}))
    return scored, metrics


def summarize_metrics(
    scored: list[dict[str, Any]],
    *,
    n_firms: int,
) -> dict[str, Any]:
    by_tier_field: dict[str, dict[str, dict[str, int]]] = {
        "tier1": defaultdict(lambda: defaultdict(int)),
        "tier2": defaultdict(lambda: defaultdict(int)),
    }
    for row in scored:
        by_tier_field[row["tier"]][row["field"]][row["outcome"]] += 1

    def pack(counts: dict[str, int]) -> dict[str, Any]:
        hit = counts.get("hit", 0)
        wrong = counts.get("wrong", 0)
        abstain_pred = counts.get("abstain_pred", 0)
        abstain_gold = counts.get("abstain_gold", 0)
        # Denominator for P/R: gold decided (not abstain_gold)
        gold_decided = hit + wrong + abstain_pred
        pred_decided = hit + wrong
        precision = (hit / pred_decided) if pred_decided else 0.0
        recall = (hit / gold_decided) if gold_decided else 0.0
        return {
            "hit": hit,
            "wrong": wrong,
            "abstain_pred": abstain_pred,
            "abstain_gold": abstain_gold,
            "gold_decided": gold_decided,
            "pred_decided": pred_decided,
            "precision_among_decided": round(precision, 4),
            "recall_vs_gold_decided": round(recall, 4),
            "precision_wilson95": list(wilson_interval(hit, pred_decided))
            if pred_decided
            else [0.0, 0.0],
            "recall_wilson95": list(wilson_interval(hit, gold_decided))
            if gold_decided
            else [0.0, 0.0],
        }

    per_tier: dict[str, Any] = {}
    for tier in ("tier1", "tier2"):
        fields_out: dict[str, Any] = {}
        aggregate: dict[str, int] = defaultdict(int)
        for field in ALL_FIELDS:
            c = dict(by_tier_field[tier][field])
            fields_out[field] = pack(c)
            for k, v in c.items():
                aggregate[k] += v
        per_tier[tier] = {"by_field": fields_out, "aggregate": pack(dict(aggregate))}

    return {
        "task": "evol1-t06-mini-gold-eval",
        "n_firms_reviewed": n_firms,
        "n_scored_cells": len(scored),
        "tiers": per_tier,
        "caveat": (
            "Mini gold on T05 fetch_ok pilot firms only — not a national estimate. "
            "Precision = hit / (hit+wrong) among machine-decided cells. "
            "Recall = hit / (hit+wrong+abstain_pred) among human-decided gold cells. "
            "Human abstain_gold cells are excluded from P/R denominators. "
            "Payment and social/marketplace list fields are scored on presence "
            "(and language with unknown-compatible match)."
        ),
    }


def render_error_analysis(
    scored: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> str:
    lines = [
        "# Mini gold — error analysis (T06)",
        "",
        f"- Firms reviewed: {metrics['n_firms_reviewed']}",
        f"- Scored cells: {metrics['n_scored_cells']}",
        "",
        metrics["caveat"],
        "",
    ]
    for tier in ("tier1", "tier2"):
        agg = metrics["tiers"][tier]["aggregate"]
        lines.extend(
            [
                f"## {tier}",
                "",
                f"- precision among decided = {agg['precision_among_decided']:.1%} "
                f"(Wilson 95% {agg['precision_wilson95'][0]:.1%}–{agg['precision_wilson95'][1]:.1%})",
                f"- recall vs gold decided = {agg['recall_vs_gold_decided']:.1%} "
                f"(Wilson 95% {agg['recall_wilson95'][0]:.1%}–{agg['recall_wilson95'][1]:.1%})",
                f"- hit={agg['hit']} wrong={agg['wrong']} "
                f"abstain_pred={agg['abstain_pred']} abstain_gold={agg['abstain_gold']}",
                "",
                "| field | precision | recall | hit | wrong | abstain_pred |",
                "|-------|-----------|--------|-----|-------|--------------|",
            ]
        )
        for field in ALL_FIELDS:
            f = metrics["tiers"][tier]["by_field"][field]
            lines.append(
                f"| {field} | {f['precision_among_decided']:.1%} | "
                f"{f['recall_vs_gold_decided']:.1%} | {f['hit']} | {f['wrong']} | "
                f"{f['abstain_pred']} |"
            )
        lines.append("")

    wrongs = [r for r in scored if r["outcome"] == "wrong"]
    lines.extend(
        [
            "## Wrong cells (machine decided, disagrees with gold)",
            "",
            "| firm_id | tier | field | gold | pred |",
            "|---------|------|-------|------|------|",
        ]
    )
    for r in sorted(wrongs, key=lambda x: (x["tier"], x["field"], x["firm_id"]))[:80]:
        lines.append(
            f"| {r['firm_id']} | {r['tier']} | {r['field']} | {r['gold']} | {r['pred']} |"
        )
    if len(wrongs) > 80:
        lines.append(f"| … | … | … | ({len(wrongs) - 80} more) | … |")
    lines.append("")
    return "\n".join(lines)


def write_eval_artifacts(
    scored: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_JSON.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    ERROR_ANALYSIS_MD.write_text(
        render_error_analysis(scored, metrics), encoding="utf-8"
    )
    fields = [
        "firm_id",
        "source_cohort",
        "website_url",
        "tier",
        "field",
        "gold",
        "pred",
        "outcome",
        "notes",
    ]
    with PREDICTIONS_VS_GOLD_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in scored:
            writer.writerow({k: row.get(k, "") for k in fields})
