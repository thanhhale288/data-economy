"""Harvest MST/address for the 28 seed firms from masothue (no website field)."""

from __future__ import annotations

import json
import logging
from typing import Any

from rapidfuzz import fuzz

from crawlers.url_finder.domain import registrable_domain
from crawlers.url_finder.evidence import PageFetcher, fold
from crawlers.url_finder.identity import (
    load_seed_gold,
    parse_masothue_hq,
    utcnow_iso,
    write_json,
)
from crawlers.url_finder.paths import HINTS_FILE, IDENTITY_FILE, LABELS_FILE, PROVENANCE_FILE
from crawlers.url_finder.search import SearchClient, SearchHit, render_queries

logger = logging.getLogger(__name__)


def _is_masothue(url: str) -> bool:
    host = registrable_domain(url)
    return host in {"masothue.com", "www.masothue.com"} or host.endswith(".masothue.com")


def load_hints(path=HINTS_FILE) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return {str(k).upper(): str(v).strip() for k, v in payload.items() if str(v).strip()}


def _from_parsed(
    seed_row: dict[str, Any], parsed: dict[str, Any], *, match_ratio: float
) -> dict[str, Any]:
    return {
        "ticker": seed_row["ticker"],
        "legal_name": seed_row["legal_name"],
        "tax_id": parsed["tax_id"],
        "address": parsed["address"],
        "province": parsed["province"],
        "aliases": parsed.get("aliases") or [],
        "source_url": parsed["source_url"],
        "source_dataset": "masothue.com",
        "retrieved_at": utcnow_iso(),
        "name_match_ratio": round(match_ratio, 1),
    }


def harvest_from_hint(
    seed_row: dict[str, Any], fetcher: PageFetcher, hint_url: str
) -> dict[str, Any] | None:
    fetched = fetcher.fetch(hint_url)
    if not fetched.ok:
        return None
    parsed = parse_masothue_hq(fetched.html, fetched.final_url or hint_url)
    if parsed is None:
        return None
    ratio = float(
        fuzz.token_set_ratio(fold(seed_row["legal_name"]), fold(parsed["legal_name"]))
    )
    return _from_parsed(seed_row, parsed, match_ratio=ratio)


def harvest_one(
    seed_row: dict[str, Any],
    searcher: SearchClient,
    fetcher: PageFetcher,
    *,
    locale: str = "vi",
    hint_url: str | None = None,
) -> dict[str, Any] | None:
    if hint_url:
        found = harvest_from_hint(seed_row, fetcher, hint_url)
        if found:
            return found
        logger.warning("Hint failed for %s: %s", seed_row["ticker"], hint_url)

    identity_query = {
        "legal_name": seed_row["legal_name"],
        "tax_id": "",
        "province": "",
        "ticker": seed_row["ticker"],
    }
    queries = render_queries(
        identity_query, locale=locale, templates_key="identity_query_templates"
    )
    hits: list[SearchHit] = []
    for query in queries:
        hits.extend(searcher.search(query))
    best: dict[str, Any] | None = None
    best_ratio = 0.0
    target = fold(seed_row["legal_name"])
    seen: set[str] = set()
    for hit in hits:
        if not _is_masothue(hit.url) or hit.url in seen:
            continue
        seen.add(hit.url)
        fetched = fetcher.fetch(hit.url)
        if not fetched.ok:
            continue
        parsed = parse_masothue_hq(fetched.html, fetched.final_url or hit.url)
        if parsed is None:
            continue
        ratio = float(fuzz.token_set_ratio(target, fold(parsed["legal_name"])))
        if ratio > best_ratio:
            best_ratio = ratio
            best = parsed
    if best is None or best_ratio < 80:
        logger.warning(
            "No masothue HQ for %s (best_ratio=%.1f)",
            seed_row["ticker"],
            best_ratio,
        )
        return None
    return _from_parsed(seed_row, best, match_ratio=best_ratio)


def harvest_identity_and_labels(*, locale: str = "vi") -> tuple[list[dict], list[dict]]:
    gold_rows = load_seed_gold()
    hints = load_hints()
    labels = [
        {
            "ticker": row["ticker"],
            "gold_url": row["gold_url"],
            "gold_domain": row["gold_domain"],
            "note": row["note"],
        }
        for row in gold_rows
    ]
    identities: list[dict[str, Any]] = []
    missing: list[str] = []
    with SearchClient(locale=locale) as searcher, PageFetcher() as fetcher:
        for row in gold_rows:
            found = harvest_one(
                row,
                searcher,
                fetcher,
                locale=locale,
                hint_url=hints.get(row["ticker"]),
            )
            if found is None:
                missing.append(row["ticker"])
                continue
            identities.append(found)
    write_json(IDENTITY_FILE, identities)
    write_json(LABELS_FILE, labels)
    _write_provenance(identities, missing, hints)
    if missing:
        logger.warning("Identity harvest missing tickers: %s", ",".join(missing))
    return identities, labels


def _write_provenance(
    identities: list[dict[str, Any]], missing: list[str], hints: dict[str, str]
) -> None:
    PROVENANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PROVENANCE — URL-finder identity (Evol-1 T03)",
        "",
        f"- Retrieved at (UTC): {utcnow_iso()}",
        "- Identity source: public masothue.com HQ pages.",
        "- HQ page URLs in `masothue_hints.json` were resolved from the public web index "
        "(masothue listings), then fetched. **No website URL was sent to search.**",
        f"- Hint URLs provided: {len(hints)}",
        f"- Firms with HQ tax identity: {len(identities)} / 28",
        f"- Missing: {', '.join(missing) if missing else '(none)'}",
        "",
        "## Split",
        "",
        "- `identity_28.json` — ticker, legal name, tax_id (MST), address, province, aliases. **No URL fields.**",
        "- `labels_28.json` — gold official website = seed `website_url` (corporate homepage, not shop channel).",
        "- Finder pipeline reads identity only. Evaluator opens labels after predictions are written.",
        "",
        "## Limits",
        "",
        "- masothue is a public tax directory, not the official GSO/Cổng ĐKKD frame.",
        "- Address text follows the directory snapshot on retrieve day; may lag mergers.",
        "- Branch MST pages (`0123456789-001`) are dropped; only 10-digit HQ codes are kept.",
        "- GEE seed display name is 'Điện Gia Dụng Gelex'; directory legal name is "
        "'Công ty Cổ phần Điện lực Gelex' (same Gelex Electric listed vehicle).",
        "",
    ]
    PROVENANCE_FILE.write_text("\n".join(lines), encoding="utf-8")
