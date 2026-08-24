"""Choose a URL or abstain. Rules always run; LLM is optional overlay."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import httpx

from backend.app.services.narrative_llm import resolve_narrative_llm_completions_url
from crawlers.url_finder.config_loader import load_config
from crawlers.url_finder.evidence import ScoredCandidate

logger = logging.getLogger(__name__)

_LLM_KEY_ENVS = ("URL_FINDER_LLM_KEY", "OPENAI_API_KEY")
_LLM_BASE_URL_ENV = "URL_FINDER_LLM_BASE_URL"
_LLM_MODEL_ENV = "URL_FINDER_LLM_MODEL"


@dataclass
class Decision:
    url: str | None
    domain: str | None
    abstain: bool
    backend: str
    confidence: float
    reason: str
    ranked: list[ScoredCandidate] = field(default_factory=list)


def _domain_core(domain: str | None) -> str:
    return (domain or "").split(".")[0].replace("-", "").lower()


def _sorted(candidates: list[ScoredCandidate], *, ticker: str = "") -> list[ScoredCandidate]:
    tick = (ticker or "").strip().lower()

    def key(c: ScoredCandidate) -> tuple:
        core = _domain_core(c.domain)
        return (
            -c.score,
            0 if c.fetch_ok else 1,
            0 if tick and core == tick else 1,
            len(core),
            c.domain or "",
        )

    return sorted(candidates, key=key)


def decide_rules(
    candidates: list[ScoredCandidate],
    *,
    locale: str = "vi",
    identity: dict[str, Any] | None = None,
) -> Decision:
    cfg = load_config(locale)
    ev = cfg.get("evidence") or {}
    min_score = float(ev.get("min_score") or 4.0)
    margin = float(ev.get("margin") or 1.0)
    ticker = str((identity or {}).get("ticker") or "")
    ranked = _sorted(candidates, ticker=ticker)
    if not ranked:
        return Decision(
            url=None,
            domain=None,
            abstain=True,
            backend="rules",
            confidence=0.0,
            reason="no_candidates",
            ranked=[],
        )
    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    second_score = second.score if second else 0.0
    if top.score < min_score:
        return Decision(
            url=None,
            domain=None,
            abstain=True,
            backend="rules",
            confidence=round(top.score / max(min_score, 1e-6), 3),
            reason=f"below_min_score:{top.score}<{min_score}",
            ranked=ranked,
        )
    gap = top.score - second_score
    if gap < margin:
        top_tax = any(r == "tax_id_on_page" for r in top.reasons)
        second_tax = bool(second and any(r == "tax_id_on_page" for r in second.reasons))
        if top_tax and not second_tax:
            return Decision(
                url=top.final_url or top.url,
                domain=top.domain,
                abstain=False,
                backend="rules",
                confidence=min(1.0, round(top.score / (min_score + 4.0), 3)),
                reason="tax_id_breaks_tie:" + ",".join(top.reasons[:4]),
                ranked=ranked,
            )
        # Fetch-ok page beats URL-only twin at the same score.
        if top.fetch_ok and second and not second.fetch_ok:
            return Decision(
                url=top.final_url or top.url,
                domain=top.domain,
                abstain=False,
                backend="rules",
                confidence=min(1.0, round(top.score / (min_score + 4.0), 3)),
                reason="fetch_ok_breaks_tie:" + ",".join(top.reasons[:4]),
                ranked=ranked,
            )
        # Exact ticker host beats longer brand twin (fpt.com.vn vs fptcorp.com.vn).
        tick = ticker.strip().lower()
        top_core = _domain_core(top.domain)
        second_core = _domain_core(second.domain) if second else ""
        if tick and top_core == tick and second_core != tick:
            return Decision(
                url=top.final_url or top.url,
                domain=top.domain,
                abstain=False,
                backend="rules",
                confidence=min(1.0, round(top.score / (min_score + 4.0), 3)),
                reason="ticker_breaks_tie:" + ",".join(top.reasons[:4]),
                ranked=ranked,
            )
        return Decision(
            url=None,
            domain=None,
            abstain=True,
            backend="rules",
            confidence=round(gap / max(margin, 1e-6), 3),
            reason=f"thin_margin:{top.score}-{second_score}<{margin}",
            ranked=ranked,
        )
    return Decision(
        url=top.final_url or top.url,
        domain=top.domain,
        abstain=False,
        backend="rules",
        confidence=min(1.0, round(top.score / (min_score + 4.0), 3)),
        reason="top_clear:" + ",".join(top.reasons[:4]),
        ranked=ranked,
    )


def _llm_key() -> str | None:
    for env in _LLM_KEY_ENVS:
        value = (os.environ.get(env) or "").strip()
        if value:
            return value
    return None


def _try_llm(
    identity: dict[str, Any],
    ranked: list[ScoredCandidate],
    *,
    locale: str,
) -> Decision | None:
    api_key = _llm_key()
    if not api_key:
        return None
    model = (os.environ.get(_LLM_MODEL_ENV) or "gpt-4o-mini").strip()
    url = resolve_narrative_llm_completions_url(_LLM_BASE_URL_ENV)
    payload_candidates = [
        {
            "url": c.final_url or c.url,
            "domain": c.domain,
            "score": c.score,
            "reasons": c.reasons,
            "title": c.title,
        }
        for c in ranked[:5]
    ]
    prompt = (
        "You assign the official corporate website of a manufacturing firm. "
        "Return JSON only: {\"url\": string|null, \"abstain\": bool, \"reason\": string}. "
        "Abstain if evidence is thin, if the page is a directory/news/marketplace, "
        "or if two domains look equally plausible. Prefer the legal-entity homepage "
        "over a shop subdomain.\n"
        f"Firm: {json.dumps({k: identity.get(k) for k in ('ticker','legal_name','tax_id','address')}, ensure_ascii=False)}\n"
        f"Candidates: {json.dumps(payload_candidates, ensure_ascii=False)}"
    )
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except Exception as exc:  # noqa: BLE001
        logger.warning("URL-finder LLM failed: %s — falling back to rules", exc)
        return None
    abstain = bool(parsed.get("abstain")) or not parsed.get("url")
    chosen = str(parsed.get("url") or "").strip() or None
    domain = None
    if chosen:
        from crawlers.url_finder.domain import registrable_domain

        domain = registrable_domain(chosen)
    return Decision(
        url=None if abstain else chosen,
        domain=None if abstain else domain,
        abstain=abstain,
        backend="llm",
        confidence=0.0 if abstain else 0.8,
        reason=str(parsed.get("reason") or "llm"),
        ranked=ranked,
    )


def decide(
    candidates: list[ScoredCandidate],
    *,
    identity: dict[str, Any],
    locale: str = "vi",
    allow_llm: bool = True,
) -> Decision:
    rules = decide_rules(candidates, locale=locale, identity=identity)
    if not allow_llm:
        return rules
    llm = _try_llm(identity, rules.ranked, locale=locale)
    if llm is None:
        return rules
    return llm
