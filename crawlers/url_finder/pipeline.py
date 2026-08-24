"""Find an official website for one firm. Identity in, URL out — no gold fields."""

from __future__ import annotations

import logging
from typing import Any

from crawlers.url_finder.config_loader import load_config
from crawlers.url_finder.decide import Decision, decide, decide_rules
from crawlers.url_finder.denylist import is_aggregator_host
from crawlers.url_finder.domain import registrable_domain
from crawlers.url_finder.evidence import PageFetcher, ScoredCandidate, score_candidate
from crawlers.url_finder.hypothesis import hypothesize_urls
from crawlers.url_finder.identity import assert_no_url_fields
from crawlers.url_finder.search import SearchClient, SearchHit, render_queries

logger = logging.getLogger(__name__)


def _dedupe_hits(
    hits: list[SearchHit],
    locale: str,
    limit: int,
    *,
    seen: set[str] | None = None,
) -> list[SearchHit]:
    out: list[SearchHit] = []
    seen_domains = seen if seen is not None else set()
    for hit in hits:
        if is_aggregator_host(hit.url, locale=locale):
            continue
        domain = registrable_domain(hit.url)
        if not domain or domain in seen_domains:
            continue
        seen_domains.add(domain)
        out.append(hit)
        if len(out) >= limit:
            break
    return out


def collect_hits(
    identity: dict[str, Any],
    searcher: SearchClient,
    *,
    locale: str = "vi",
) -> tuple[list[SearchHit], list[str], str]:
    assert_no_url_fields(identity, context="url_finder.collect_hits")
    cfg = load_config(locale)
    limit = int(cfg.get("max_candidates") or 8)
    hypothesis_limit = int(cfg.get("max_hypothesis_candidates") or limit)
    prefilter = bool(cfg.get("hypothesis_dns_prefilter", True))
    queries = render_queries(identity, locale=locale)
    raw: list[SearchHit] = []
    for query in queries:
        if searcher.blocked:
            break
        raw.extend(searcher.search(query))
    seen: set[str] = set()
    kept = _dedupe_hits(raw, locale, limit, seen=seen)
    # Union, not fallback: a partially working SERP can still miss the real domain,
    # and hypothesis candidates are free (DNS prefilter drops the dead ones).
    guessed = _dedupe_hits(
        hypothesize_urls(
            identity,
            locale=locale,
            resolve=prefilter,
            limit=hypothesis_limit,
        ),
        locale,
        hypothesis_limit,
        seen=seen,
    )
    if kept and guessed:
        source = "search+hypothesis"
    elif kept:
        source = "search"
    elif guessed:
        source = "domain_hypothesis"
    else:
        source = "none"
    return [*kept, *guessed], queries, source


def collapse_scored_by_domain(scored: list[ScoredCandidate]) -> list[ScoredCandidate]:
    """Keep the best score per registrable domain after redirects.

    Several hypothesized hosts often redirect to the same homepage; without this
    collapse, decide_rules sees identical scores and abstains on thin_margin.
    """
    best: dict[str, ScoredCandidate] = {}
    order: list[str] = []
    for cand in scored:
        key = cand.domain or cand.final_url or cand.url
        if not key:
            continue
        prev = best.get(key)
        if prev is None:
            best[key] = cand
            order.append(key)
            continue
        if cand.score > prev.score or (
            cand.score == prev.score and cand.fetch_ok and not prev.fetch_ok
        ):
            best[key] = cand
    return [best[k] for k in order]


def find_url(
    identity: dict[str, Any],
    *,
    searcher: SearchClient,
    fetcher: PageFetcher | None = None,
    locale: str = "vi",
    allow_llm: bool = False,
    fetch_pages: bool = True,
) -> dict[str, Any]:
    """Blind finder: never reads website/gold fields from identity."""
    payload = {
        "ticker": identity.get("ticker"),
        "legal_name": identity.get("legal_name"),
        "tax_id": identity.get("tax_id"),
        "address": identity.get("address"),
        "province": identity.get("province"),
        "aliases": identity.get("aliases") or [],
    }
    assert_no_url_fields(payload, context="url_finder.find_url")
    hits, queries, candidate_source = collect_hits(payload, searcher, locale=locale)
    owns_fetcher = fetcher is None
    page_client = fetcher or PageFetcher()
    try:
        scored: list[ScoredCandidate] = []
        for hit in hits:
            fetched = page_client.fetch(hit.url) if fetch_pages else None
            scored.append(score_candidate(payload, hit, fetched, locale=locale))
        # Drop directory/tax-lookup hosts even if they appear after redirects.
        scored = [
            c
            for c in scored
            if not is_aggregator_host(c.final_url or c.url, locale=locale)
        ]
        scored = collapse_scored_by_domain(scored)
        decision: Decision = (
            decide(scored, identity=payload, locale=locale, allow_llm=allow_llm)
            if allow_llm
            else decide_rules(scored, identity=payload, locale=locale)
        )
        # Naive baseline = first non-aggregator SERP hit. Domain guesses are not a
        # baseline, so keep them out of this number.
        baseline = next((h.url for h in hits if h.source == "search"), None)
        return {
            "ticker": identity.get("ticker"),
            "queries": queries,
            "n_candidates": len(hits),
            "candidate_source": candidate_source,
            "search_blocked": bool(searcher.blocked),
            "search_block_detail": searcher.block_detail,
            "baseline_first_non_aggregator": baseline,
            "predicted_url": decision.url,
            "predicted_domain": decision.domain,
            "abstain": decision.abstain,
            "backend": decision.backend,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "ranked": [
                {
                    "url": c.final_url or c.url,
                    "domain": c.domain,
                    "score": c.score,
                    "reasons": c.reasons,
                    "fetch_ok": c.fetch_ok,
                    "fetch_detail": c.fetch_detail,
                }
                for c in decision.ranked[:8]
            ],
        }
    finally:
        if owns_fetcher:
            page_client.close()
