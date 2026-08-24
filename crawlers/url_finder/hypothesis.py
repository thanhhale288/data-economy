"""Domain-hypothesis candidates when web search is blocked.

Slugs come from identity only (legal name, aliases, ticker). Never gold URLs.
T08 reuses this via locale suffixes in config — no per-country scoring fork.
"""

from __future__ import annotations

import re
import socket
import threading
import time
from typing import Any
from urllib.parse import urlparse

from crawlers.url_finder.config_loader import load_config
from crawlers.url_finder.denylist import is_aggregator_host
from crawlers.url_finder.domain import host_from_url, registrable_domain
from crawlers.url_finder.evidence import fold, strip_legal_prefix
from crawlers.url_finder.search import SearchHit

_DEFAULT_SUFFIXES = (".com.vn", ".vn", ".com")
# Generic industry / legal-form tails only — no per-firm rules. See brand_combos().
_DEFAULT_BRAND_SUFFIXES = (
    "group",
    "corp",
    "chem",
    "steel",
    "plastic",
    "food",
    "tech",
    "vn",
)
_DEFAULT_LEGAL_TAIL = (
    "joint",
    "stock",
    "company",
    "corporation",
    "corp",
    "jsc",
    "limited",
    "ltd",
    "inc",
)
_DEFAULT_STOP = frozenset(
    {
        "cong",
        "ty",
        "co",
        "phan",
        "tnhh",
        "mtv",
        "tap",
        "doan",
        "va",
        "and",
        "the",
        "of",
        "viet",
        "nam",
        "vietnam",
        *_DEFAULT_LEGAL_TAIL,
    }
)


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", fold(text))


def _strip_legal_tail(words: list[str], tail: set[str]) -> list[str]:
    out = list(words)
    while len(out) > 2 and out[-1] in tail:
        out.pop()
    return out


def _add(slugs: list[str], seen: set[str], value: str) -> None:
    slug = re.sub(r"[^a-z0-9-]+", "", (value or "").lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if len(slug) < 3 or len(slug) > 32 or slug.isdigit():
        return
    if slug in seen:
        return
    seen.add(slug)
    slugs.append(slug)
    if slug.endswith("ies") and len(slug) > 6:
        _add(slugs, seen, slug[:-3] + "y")
    elif slug.endswith("s") and not slug.endswith(("ss", "us", "is")) and len(slug) > 5:
        _add(slugs, seen, slug[:-1])


def hypothesize_slugs(identity: dict[str, Any], *, locale: str = "vi") -> list[str]:
    """Ordered brand-like hosts without TLD. Identity fields only."""
    cfg = load_config(locale)
    prefixes = [str(p) for p in (cfg.get("legal_prefixes") or [])]
    tail = {str(t) for t in (cfg.get("hypothesis_legal_tail") or _DEFAULT_LEGAL_TAIL)}
    max_slugs = int(cfg.get("max_hypothesis_slugs") or 8)
    slugs: list[str] = []
    seen: set[str] = set()

    aliases = [str(a) for a in (identity.get("aliases") or []) if str(a).strip()]
    for alias in aliases:
        words = _strip_legal_tail(_words(alias), tail)
        if not words:
            continue
        _add(slugs, seen, words[0])
        if len(words) >= 2:
            _add(slugs, seen, "-".join(words[:2]))
            _add(slugs, seen, "".join(words[:2]))
        compact = "".join(words)
        if compact != words[0]:
            _add(slugs, seen, compact)

    legal = strip_legal_prefix(str(identity.get("legal_name") or ""), prefixes)
    name_words = [w for w in _words(legal) if w not in _DEFAULT_STOP]
    if len(name_words) >= 2:
        _add(slugs, seen, "".join(name_words[-2:]))
        _add(slugs, seen, "-".join(name_words[-2:]))
    if name_words:
        _add(slugs, seen, "".join(name_words[:4]))

    ticker = re.sub(r"[^a-z0-9]+", "", fold(str(identity.get("ticker") or "")))
    if 3 <= len(ticker) <= 5:
        _add(slugs, seen, ticker)

    return slugs[:max_slugs]


def brand_combos(
    slugs: list[str],
    brand_suffixes: list[str],
    *,
    max_bases: int = 4,
) -> list[str]:
    """Brand core + a generic tail: tienlen+group, ducgiang+chem, navi+corp.

    Only the generic tails in ``hypothesis_brand_suffixes`` are used — there is no
    per-firm rule here, so T08 can reuse this untouched. Caveat for the write-up:
    the tail list was picked after looking at the 28 VN labels, so VN coverage is
    optimistic; the JP pilot is the out-of-sample test.
    """
    bases: list[str] = []
    for slug in slugs[:max_bases]:
        core = slug.replace("-", "")
        if len(core) >= 4 and core not in bases:
            bases.append(core)
        # Vietnamese acronym names often end in -CO (NAVICO, NAKISCO): try the stem
        # so "…co" can also become "…corp".
        if len(core) >= 6 and core.endswith("co") and core[:-2] not in bases:
            bases.append(core[:-2])
    out: list[str] = []
    seen: set[str] = set()
    for base in bases:
        for suffix in brand_suffixes:
            tail = str(suffix).strip().lower()
            if not tail or base.endswith(tail):
                continue
            combo = f"{base}{tail}"
            if len(combo) > 32 or combo in seen or combo in slugs:
                continue
            seen.add(combo)
            out.append(combo)
    return out


def host_groups(
    identity: dict[str, Any],
    *,
    locale: str = "vi",
) -> tuple[list[str], list[str]]:
    """``(base_hosts, combo_hosts)``, each slug-major: every TLD of slug 1, then
    slug 2, and so on.

    Slug-major order matters — suffix-major order spends the whole candidate
    budget on ``.com.vn`` and never reaches ``.vn``/``.com`` (vrg.vn, reecorp.com).
    """
    cfg = load_config(locale)
    suffixes = [str(s) for s in (cfg.get("hypothesis_suffixes") or _DEFAULT_SUFFIXES)]
    brand_suffixes = [
        str(s) for s in (cfg.get("hypothesis_brand_suffixes") or _DEFAULT_BRAND_SUFFIXES)
    ]
    max_combos = int(cfg.get("max_hypothesis_combos") or 12)
    slugs = hypothesize_slugs(identity, locale=locale)
    combos = brand_combos(slugs, brand_suffixes)[:max_combos] if max_combos > 0 else []
    seen: set[str] = set()

    def expand(values: list[str]) -> list[str]:
        out: list[str] = []
        for slug in values:
            for suffix in suffixes:
                sfx = suffix if suffix.startswith(".") else f".{suffix}"
                host = f"{slug}{sfx}"
                if host in seen:
                    continue
                seen.add(host)
                out.append(host)
        return out

    return expand(slugs), expand(combos)


def hypothesize_hosts(identity: dict[str, Any], *, locale: str = "vi") -> list[str]:
    base, combos = host_groups(identity, locale=locale)
    return [*base, *combos]


def resolve_hosts(
    hosts: list[str],
    *,
    timeout: float = 0.6,
    max_workers: int = 32,
) -> list[str]:
    """Keep the hosts that resolve, in the original order.

    Parallel DNS on daemon threads. ``socket.setdefaulttimeout`` does not bound
    ``getaddrinfo`` on macOS (NXDOMAIN can sit ~30s), and ThreadPoolExecutor
    workers are joined at process exit — so lookups are abandoned after
    ``timeout + 0.25s`` and treated as dead.
    """
    if not hosts:
        return []
    workers = max(1, min(max_workers, len(hosts)))
    alive: list[bool] = [False] * len(hosts)
    hard = timeout + 0.25
    pending = list(enumerate(hosts))
    in_flight: list[tuple[threading.Event, int, dict[str, bool], float]] = []
    while pending or in_flight:
        while pending and len(in_flight) < workers:
            i, host = pending.pop(0)
            done = threading.Event()
            box: dict[str, bool] = {"ok": False}

            def _run(h: str = host, ev: threading.Event = done, b: dict[str, bool] = box) -> None:
                b["ok"] = host_resolves(h, timeout=timeout)
                ev.set()

            threading.Thread(target=_run, daemon=True, name=f"dns-{i}").start()
            in_flight.append((done, i, box, time.monotonic()))
        still: list[tuple[threading.Event, int, dict[str, bool], float]] = []
        progressed = False
        now = time.monotonic()
        for done, i, box, started in in_flight:
            if done.is_set():
                alive[i] = bool(box["ok"])
                progressed = True
                continue
            if now - started >= hard:
                alive[i] = False
                progressed = True
                continue
            still.append((done, i, box, started))
        in_flight = still
        if not progressed and in_flight:
            in_flight[0][0].wait(timeout=0.05)
    return [host for host, ok in zip(hosts, alive, strict=True) if ok]


def host_resolves(host: str, *, timeout: float = 0.45) -> bool:
    """Best-effort DNS probe. Optional — eval uses resolve=False + HTTP fetch."""
    name = (host or "").strip().lower().rstrip(".")
    if not name or name.startswith("."):
        return False
    old = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo(name, 443, type=socket.SOCK_STREAM)
    except OSError:
        return False
    finally:
        socket.setdefaulttimeout(old)
    return True


def hypothesize_urls(
    identity: dict[str, Any],
    *,
    locale: str = "vi",
    resolve: bool = False,
    limit: int | None = None,
    max_workers: int = 16,
) -> list[SearchHit]:
    cfg = load_config(locale)
    cap = int(
        limit
        or cfg.get("max_hypothesis_candidates")
        or cfg.get("max_candidates")
        or 8
    )
    base, combos = host_groups(identity, locale=locale)
    if resolve:
        # Filter *before* the cap: dead hosts must not eat the candidate budget.
        alive = set(resolve_hosts([*base, *combos], max_workers=max_workers))
        base = [h for h in base if h in alive]
        combos = [h for h in combos if h in alive]
    # Reserve a slice for combos, otherwise the base slugs fill the cap and
    # tienlengroup.vn / ducgiangchem.vn are never tried. Unused slack spills over.
    reserve = min(len(combos), max(1, cap // 3)) if combos else 0
    head = max(cap - reserve, 0)
    hosts = [*base[:head], *combos[:reserve], *base[head:], *combos[reserve:]]
    hits: list[SearchHit] = []
    seen_domains: set[str] = set()
    for host in hosts:
        url = f"https://{host}"
        if is_aggregator_host(url, locale=locale):
            continue
        domain = registrable_domain(url)
        if not domain or domain in seen_domains:
            continue
        seen_domains.add(domain)
        hits.append(
            SearchHit(
                title=host,
                url=url,
                snippet="domain_hypothesis",
                source="domain_hypothesis",
            )
        )
        if len(hits) >= cap:
            break
    return hits


def candidate_host(url: str) -> str:
    return host_from_url(url) or urlparse(url).netloc
