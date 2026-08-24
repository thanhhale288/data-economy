#!/usr/bin/env python3
"""Evol-1 T05: run extraction cascade on cohort; write raw indicators + conflicts.

Tier-1 (rules) always runs when fetch succeeds. Tier-2 (local LLM) is optional
via --llm; when disabled, tier-2 abstains so CI/offline still produces tables.
Does not scrape marketplace listing pages — only company websites + outbound links.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from crawlers.extraction_cascade.cohort import (
    build_cohort,
    cohort_sha256,
    write_cohort,
)
from crawlers.extraction_cascade.fetch import USER_AGENT, fetch_page
from crawlers.extraction_cascade.paths import (
    CONFLICT_NOTES_MD,
    CONFLICTS_CSV,
    INDICATORS_CSV,
    INDICATORS_JSONL,
    MANIFEST_JSON,
    PROCESSED_DIR,
    PROVENANCE_MD,
    RAW_DIR,
    SUMMARY_JSON,
)
from crawlers.extraction_cascade.pipeline import flatten_indicator_rows, run_on_page
from crawlers.extraction_cascade.schema import FirmCascadeResult
from ml.local_llm.client import LocalLlmSettings, load_pin, prompt_sha256, schema_sha256


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--llm",
        action="store_true",
        help="Call pinned local LLM (T04). Default: tier2 abstains.",
    )
    p.add_argument(
        "--verify-pin",
        action="store_true",
        help="Verify Ollama model digest before inference.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process only the first N cohort firms (0 = all).",
    )
    p.add_argument(
        "--frame-urls",
        type=Path,
        default=None,
        help="Optional JSON list of frame_pilot URLs from URL-finder.",
    )
    p.add_argument(
        "--listed-only",
        action="store_true",
        help="Ignore frame_urls even if present.",
    )
    p.add_argument(
        "--sleep",
        type=float,
        default=0.4,
        help="Seconds between homepage fetches.",
    )
    return p.parse_args()


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    # Flatten evidence for CSV
    flat: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        ev = item.pop("evidence", None)
        item["evidence"] = json.dumps(ev, ensure_ascii=False) if ev is not None else ""
        flat.append(item)
    fieldnames = list(flat[0].keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat)


def _summarize(results: list[FirmCascadeResult]) -> dict[str, Any]:
    n = len(results)
    fetch_ok = [r for r in results if r.fetch_ok]
    t1_ok = [r for r in fetch_ok if r.tier1 is not None]
    listed = [r for r in results if r.source_cohort == "listed28"]
    frame = [r for r in results if r.source_cohort == "frame_pilot"]

    def rate(pred) -> float | None:
        if not t1_ok:
            return None
        return round(sum(1 for r in t1_ok if pred(r.tier1)) / len(t1_ok), 4)

    conflict_counts = {"agree": 0, "conflict": 0, "abstain": 0, "skip": 0}
    by_field: dict[str, dict[str, int]] = {}
    for r in results:
        for c in r.conflicts:
            conflict_counts[c.kind] = conflict_counts.get(c.kind, 0) + 1
            bucket = by_field.setdefault(
                c.field, {"agree": 0, "conflict": 0, "abstain": 0, "skip": 0}
            )
            bucket[c.kind] = bucket.get(c.kind, 0) + 1

    return {
        "generated_at": _utcnow(),
        "n_cohort": n,
        "n_listed28": len(listed),
        "n_frame_pilot": len(frame),
        "n_fetch_ok": len(fetch_ok),
        "fetch_ok_rate": round(len(fetch_ok) / n, 4) if n else None,
        "tier1_rates_among_fetch_ok": {
            "has_product_catalog": rate(lambda t: t.has_product_catalog),
            "has_order_cart": rate(lambda t: t.has_order_cart),
            "has_payment_methods": rate(lambda t: bool(t.payment_methods)),
            "has_social_links": rate(lambda t: bool(t.social_links)),
            "has_marketplace_links": rate(lambda t: bool(t.marketplace_links)),
        },
        "tier_compare_counts": conflict_counts,
        "tier_compare_by_field": by_field,
        "caveat": (
            "Pilot descriptive rates only — not weighted national estimates. "
            "No survey weights, no confidence intervals for population inference. "
            "Marketplace signals are outbound links on the company website, "
            "not scraped Shopee/TikTok/Lazada listings."
        ),
    }


def _conflict_notes(results: list[FirmCascadeResult], limit: int = 12) -> str:
    lines = [
        "# Conflict notes (tier1 rules vs tier2 LLM)",
        "",
        "Interesting mismatches for advisor slides — not a gold-standard evaluation.",
        "",
    ]
    count = 0
    for r in results:
        for c in r.conflicts:
            if c.kind != "conflict":
                continue
            lines.append(
                f"- **{r.firm_id}** / `{c.field}`: tier1={c.tier1_value!r} "
                f"tier2={c.tier2_value!r} ({c.note or 'mismatch'})"
            )
            count += 1
            if count >= limit:
                break
        if count >= limit:
            break
    if count == 0:
        lines.append(
            "- No bool/presence conflicts in this run "
            "(common when tier2 is disabled/abstain)."
        )
    lines.append("")
    return "\n".join(lines)


def _provenance(
    *,
    cohort_hash: str,
    llm_enabled: bool,
    n: int,
    elapsed_s: float,
) -> str:
    pin = load_pin()
    lines = [
        "# PROVENANCE — Extraction cascade v0 (Evol-1 T05)",
        "",
        f"- Generated at (UTC): {_utcnow()}",
        f"- Cohort sha256: `{cohort_hash}`",
        f"- Firms processed: {n}",
        f"- Elapsed seconds: {elapsed_s:.1f}",
        f"- Tier2 LLM enabled: {llm_enabled}",
        f"- Local LLM pin model: `{pin.get('model')}`",
        f"- Schema sha256: `{schema_sha256()}`",
        f"- Prompt sha256: `{prompt_sha256()}`",
        "",
        "## Method",
        "",
        "1. Fetch company homepage (httpx). Fail → skip indicators (do not invent).",
        "2. Tier 1: locale JSON rules (cart, payment markers, marketplace/social hrefs).",
        "3. Tier 2: pinned Ollama JSON schema extractor from T04 (optional).",
        "4. Compare tiers field-by-field → agree / conflict / abstain / skip.",
        "",
        "## Limits",
        "",
        "- Not a national estimate; pilot cohort only.",
        "- Does **not** crawl marketplace product listings (anti-bot / out of scope).",
        "- Frame-pilot URLs only included when `data/raw/extraction_cascade/frame_urls.json` "
        "is supplied (from URL-finder); otherwise listed28 only.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    firms = build_cohort(
        frame_urls_path=args.frame_urls,
        include_listed=True,
    )
    if args.listed_only:
        firms = [f for f in firms if f.source_cohort == "listed28"]
    write_cohort(firms)
    if args.limit and args.limit > 0:
        firms = firms[: args.limit]

    settings = LocalLlmSettings.from_pin_and_env() if args.llm else None
    results: list[FirmCascadeResult] = []
    indicator_rows: list[dict[str, Any]] = []
    conflict_rows: list[dict[str, Any]] = []

    t0 = time.perf_counter()
    with httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=20.0,
        follow_redirects=True,
    ) as http_fetch:
        llm_client = None
        if args.llm:
            llm_client = httpx.Client(base_url=settings.base_url, timeout=120.0)
        try:
            for i, firm in enumerate(firms):
                page = fetch_page(firm.website_url, client=http_fetch)
                result = run_on_page(
                    firm_id=firm.firm_id,
                    source_cohort=firm.source_cohort,
                    website_url=firm.website_url,
                    page=page,
                    llm_enabled=args.llm,
                    http_llm=llm_client,
                    llm_settings=settings,
                    verify_pin=args.verify_pin and i == 0,
                )
                results.append(result)
                indicator_rows.extend(flatten_indicator_rows(result))
                conflict_rows.extend(c.to_dict() for c in result.conflicts)
                if args.sleep > 0 and i + 1 < len(firms):
                    time.sleep(args.sleep)
        finally:
            if llm_client is not None:
                llm_client.close()
    elapsed = time.perf_counter() - t0

    _write_jsonl(INDICATORS_JSONL, [r.to_dict() for r in results])
    _write_csv(INDICATORS_CSV, indicator_rows)
    _write_csv(CONFLICTS_CSV, conflict_rows)
    summary = _summarize(results)
    summary["llm_enabled"] = args.llm
    summary["elapsed_seconds"] = round(elapsed, 2)
    SUMMARY_JSON.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    c_hash = cohort_sha256(firms)
    manifest = {
        "task": "evol1-t05-extraction-cascade-v0",
        "generated_at": _utcnow(),
        "cohort_sha256": c_hash,
        "n": len(results),
        "llm_enabled": args.llm,
        "artifacts": {
            "indicators_jsonl": str(INDICATORS_JSONL.relative_to(PROCESSED_DIR.parent.parent)),
            "indicators_csv": str(INDICATORS_CSV.relative_to(PROCESSED_DIR.parent.parent)),
            "conflicts_csv": str(CONFLICTS_CSV.relative_to(PROCESSED_DIR.parent.parent)),
            "summary_json": str(SUMMARY_JSON.relative_to(PROCESSED_DIR.parent.parent)),
        },
    }
    # Fix relative paths — use repo-relative from ROOT
    from crawlers.extraction_cascade.paths import ROOT

    manifest["artifacts"] = {
        "indicators_jsonl": str(INDICATORS_JSONL.relative_to(ROOT)),
        "indicators_csv": str(INDICATORS_CSV.relative_to(ROOT)),
        "conflicts_csv": str(CONFLICTS_CSV.relative_to(ROOT)),
        "summary_json": str(SUMMARY_JSON.relative_to(ROOT)),
    }
    MANIFEST_JSON.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    PROVENANCE_MD.write_text(
        _provenance(
            cohort_hash=c_hash,
            llm_enabled=args.llm,
            n=len(results),
            elapsed_s=elapsed,
        ),
        encoding="utf-8",
    )
    CONFLICT_NOTES_MD.write_text(_conflict_notes(results), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
