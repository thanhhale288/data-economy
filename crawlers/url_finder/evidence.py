"""On-page evidence scoring (name / tax id / address / domain tokens)."""

from __future__ import annotations

import logging
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from crawlers.companies.website_detector import HTTP_TIMEOUT
from crawlers.url_finder.config_loader import load_config
from crawlers.url_finder.domain import host_from_url, registrable_domain, strip_www
from crawlers.url_finder.paths import PAGE_CACHE_DIR
from crawlers.url_finder.search import BROWSER_UA, SearchHit

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+")

# Single-token cores that match almost any Vietnamese legal name — never enough
# evidence on their own (thanh.vn, nam.com.vn, hoa.com).
_WEAK_DOMAIN_CORES = frozenset(
    {
        "cong",
        "ty",
        "congty",
        "hoa",
        "nam",
        "viet",
        "thanh",
        "binh",
        "minh",
        "tien",
        "dien",
        "vinh",
        "the",
        "and",
        "group",
        "corp",
        "steel",
        "food",
        "tech",
        "vn",
        "chat",
        "hoachat",
    }
)

_PARKING_MARKERS = (
    "hugedomains.com",
    "godaddy.com",
    "sedo.com",
    "dan.com",
    "afternic.com",
    "domain is for sale",
    "buy this domain",
    "this domain may be for sale",
    "parked free",
)


def _tld_bonus_rules(ev: dict[str, Any], locale: str) -> list[tuple[str, float, str]]:
    """Longest-suffix-first TLD bonuses from locale config (not ``if locale ==``)."""
    raw = ev.get("tld_bonuses")
    rules: list[tuple[str, float, str]] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            suffix = str(item.get("suffix") or "").strip().lower()
            if not suffix:
                continue
            if not suffix.startswith("."):
                suffix = f".{suffix}"
            reason = str(item.get("reason") or suffix.lstrip("."))
            rules.append((suffix, float(item.get("bonus") or 0.0), reason))
    if not rules and locale == "vi":
        rules = [
            (".com.vn", float(ev.get("tld_com_vn_bonus") or 1.5), "com.vn"),
            (".vn", float(ev.get("tld_vn_bonus") or 0.75), "vn"),
        ]
    return sorted(rules, key=lambda row: -len(row[0]))


def _vi_ascii_table() -> dict[int, int]:
    marks = (
        "àáảãạăằắẳẵặâầấẩẫậ"
        "èéẻẽẹêềếểễệ"
        "ìíỉĩị"
        "òóỏõọôồốổỗộơờớởỡợ"
        "ùúủũụưừứửữự"
        "ỳýỷỹỵđ"
    )
    base = (
        "aaaaaaaaaaaaaaaaa"
        "eeeeeeeeeee"
        "iiiii"
        "ooooooooooooooooo"
        "uuuuuuuuuuu"
        "yyyyyd"
    )
    if len(marks) != len(base):
        raise RuntimeError(f"VI fold table length mismatch {len(marks)} != {len(base)}")
    table = str.maketrans(marks, base)
    for src, dst in zip(marks, base, strict=True):
        upper_src = src.upper()
        upper_dst = "D" if dst == "d" else dst.upper()
        table[ord(upper_src)] = ord(upper_dst)
    return table


_VI_ASCII = _vi_ascii_table()


def fold(text: str) -> str:
    translated = (text or "").translate(_VI_ASCII)
    raw = unicodedata.normalize("NFKD", translated)
    stripped = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return stripped.lower()


def strip_legal_prefix(name: str, prefixes: list[str]) -> str:
    folded_name = fold(name).strip()
    for prefix in prefixes:
        p = fold(prefix).strip()
        if folded_name.startswith(p + " "):
            return folded_name[len(p) :].strip()
    return folded_name


def name_variants(identity: dict[str, Any], prefixes: list[str]) -> list[str]:
    values = [str(identity.get("legal_name") or "")]
    values.extend(str(a) for a in (identity.get("aliases") or []))
    out: list[str] = []
    for value in values:
        if not value.strip():
            continue
        out.append(fold(value))
        stripped = strip_legal_prefix(value, prefixes)
        if stripped and stripped not in out:
            out.append(stripped)
    return out


def domain_tokens(url: str) -> set[str]:
    host = strip_www(registrable_domain(url) or host_from_url(url))
    host = re.sub(r"\.(com|net|org|vn|info|biz)$", "", host)
    host = host.replace(".com", "").replace(".vn", "")
    parts = re.split(r"[.\-]+", host)
    return {p for p in parts if len(p) >= 3}


def _best_name_ratio(text: str, variants: list[str]) -> float:
    hay = fold(text)
    if not hay or not variants:
        return 0.0
    return max(float(fuzz.token_set_ratio(hay, v)) for v in variants)


@dataclass
class FetchResult:
    ok: bool
    url: str
    final_url: str = ""
    html: str = ""
    detail: str = ""


@dataclass
class ScoredCandidate:
    url: str
    title: str
    snippet: str
    score: float
    reasons: list[str] = field(default_factory=list)
    fetch_ok: bool = False
    fetch_detail: str = ""
    final_url: str = ""
    domain: str = ""


class PageFetcher:
    def __init__(
        self,
        *,
        cache_dir: Path | None = None,
        delay_seconds: float = 0.25,
        client: httpx.Client | None = None,
        timeout: float = 5.0,
        locale: str = "vi",
    ) -> None:
        self.cache_dir = cache_dir or PAGE_CACHE_DIR
        self.delay_seconds = delay_seconds
        self._owns = client is None
        cfg = load_config(locale)
        accept_language = str(
            cfg.get("accept_language") or "vi-VN,vi;q=0.9,en;q=0.8"
        )
        self.client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            verify=False,  # evidence crawl: many VN corporate certs are broken
            headers={
                "User-Agent": BROWSER_UA,
                "Accept-Language": accept_language,
            },
            trust_env=False,
        )
        self._last_at = 0.0

    def close(self) -> None:
        if self._owns:
            self.client.close()

    def __enter__(self) -> PageFetcher:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _cache_path(self, url: str) -> Path:
        import hashlib

        key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
        return self.cache_dir / f"{key}.html"

    def fetch(self, url: str, *, use_cache: bool = True) -> FetchResult:
        path = self._cache_path(url)
        if use_cache and path.exists():
            html = path.read_text(encoding="utf-8", errors="replace")
            return FetchResult(ok=True, url=url, final_url=url, html=html, detail="cache")
        wait = self.delay_seconds - (time.monotonic() - self._last_at)
        if wait > 0:
            time.sleep(wait)
        try:
            response = self.client.get(url)
            self._last_at = time.monotonic()
        except Exception as exc:  # noqa: BLE001 — never invent page text
            self._last_at = time.monotonic()
            detail = f"error:{type(exc).__name__}:{exc}"
            logger.warning("Page fetch fail %s: %s", url, detail)
            return FetchResult(ok=False, url=url, detail=detail)
        if response.status_code != 200:
            detail = f"http_fail status={response.status_code}"
            logger.warning("Page fetch fail %s: %s", url, detail)
            return FetchResult(ok=False, url=url, final_url=str(response.url), detail=detail)
        html = response.text or ""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8", errors="replace")
        return FetchResult(
            ok=True,
            url=url,
            final_url=str(response.url),
            html=html,
            detail="ok",
        )


def score_html(
    identity: dict[str, Any],
    html: str,
    *,
    url: str,
    title_hint: str = "",
    locale: str = "vi",
) -> tuple[float, list[str]]:
    cfg = load_config(locale)
    ev = cfg.get("evidence") or {}
    prefixes = [str(p) for p in (cfg.get("legal_prefixes") or [])]
    variants = name_variants(identity, prefixes)
    has_page = bool((html or "").strip())
    soup = BeautifulSoup(html or "", "html.parser") if has_page else None
    title = title_hint
    footer = ""
    body = fold(html or "")
    if soup is not None:
        if soup.title and soup.title.string:
            title = soup.title.string
        foot = soup.find("footer")
        footer = foot.get_text(" ", strip=True) if foot else ""
        body = fold(soup.get_text(" ", strip=True))

    reasons: list[str] = []
    score = 0.0
    tax = str(identity.get("tax_id") or "")
    if has_page and tax and tax in (html or ""):
        score += float(ev.get("tax_id_weight") or 5.0)
        reasons.append("tax_id_on_page")

    if has_page:
        title_ratio = _best_name_ratio(title, variants)
        if title_ratio >= float(ev.get("name_title_threshold") or 80):
            score += float(ev.get("name_title_weight") or 3.0)
            reasons.append(f"name_in_title:{title_ratio:.0f}")

        body_source = footer or body[:4000]
        body_ratio = _best_name_ratio(body_source, variants)
        if body_ratio >= float(ev.get("name_body_threshold") or 75):
            score += float(ev.get("name_body_weight") or 2.0)
            reasons.append(f"name_in_body:{body_ratio:.0f}")

        address = fold(str(identity.get("address") or ""))
        addr_tokens = [t for t in _TOKEN_RE.findall(address) if len(t) >= 4]
        if addr_tokens:
            hits = sum(1 for t in addr_tokens if t in body)
            if hits >= max(1, len(addr_tokens) // 4):
                score += float(ev.get("address_weight") or 1.0)
                reasons.append(f"address_tokens:{hits}")

    name_tokens = set()
    for variant in variants:
        name_tokens.update(t for t in _TOKEN_RE.findall(variant) if len(t) >= 3)
    d_tokens = domain_tokens(url)
    # Drop weak single-syllable cores so thanh.vn / nam.com.vn cannot ride the
    # domain_token weight alone.
    strong_overlap = {
        t for t in (name_tokens & d_tokens) if len(t) >= 5 or t not in _WEAK_DOMAIN_CORES
    }
    core = strip_www(registrable_domain(url) or "").split(".")[0].replace("-", "")
    compact = "".join(_TOKEN_RE.findall("".join(variants)))
    if core and len(core) >= 5 and core in compact.replace(" ", ""):
        strong_overlap.add(core)
    # Brand stem: "tienlengroup" starts with alias compact "tienlen".
    if core and len(core) >= 6:
        for stem_len in range(min(len(core), 12), 5, -1):
            stem = core[:stem_len]
            if stem in compact and stem not in _WEAK_DOMAIN_CORES:
                strong_overlap.add(stem)
                break
    if strong_overlap and core not in _WEAK_DOMAIN_CORES:
        score += float(ev.get("domain_token_weight") or 2.5)
        reasons.append("domain_tokens:" + ",".join(sorted(strong_overlap)[:4]))
    elif core in _WEAK_DOMAIN_CORES or (core and len(core) < 5):
        # Actively penalize one-syllable hosts that only match a weak name token.
        score -= float(ev.get("weak_domain_penalty") or 2.0)
        reasons.append(f"weak_domain_core:{core}")

    # Locale TLD preference lives in config (vi: .com.vn; ja: .co.jp). Longest
    # suffix wins so .com.vn is not double-counted as .vn.
    host = strip_www(registrable_domain(url) or "")
    tld_rules = _tld_bonus_rules(ev, locale)
    for suffix, bonus, reason in tld_rules:
        if host.endswith(suffix):
            score += bonus
            reasons.append(f"tld_prefer:{reason}")
            break

    lower_html = (html or "").lower()
    if has_page and any(marker in lower_html for marker in _PARKING_MARKERS):
        score -= float(ev.get("parking_penalty") or 5.0)
        reasons.append("parking_page")

    return score, reasons


def score_candidate(
    identity: dict[str, Any],
    hit: SearchHit,
    fetched: FetchResult | None,
    *,
    locale: str = "vi",
) -> ScoredCandidate:
    url = fetched.final_url if fetched and fetched.final_url else hit.url
    html = fetched.html if fetched and fetched.ok else ""
    # Empty HTML → domain/TLD signals only. Do not paste SERP/hypothesis title as
    # fake page text (that made every fail-fetch look like name_in_title:100).
    score, reasons = score_html(
        identity,
        html,
        url=url,
        title_hint=(hit.title if html else ""),
        locale=locale,
    )
    if not html:
        reasons = [f"url_only:{r}" for r in reasons]
    else:
        cfg = load_config(locale)
        ev = cfg.get("evidence") or {}
        score += float(ev.get("fetch_ok_bonus") or 1.0)
        reasons.append("fetch_ok")
    return ScoredCandidate(
        url=hit.url,
        title=hit.title,
        snippet=hit.snippet,
        score=round(score, 3),
        reasons=reasons,
        fetch_ok=bool(fetched and fetched.ok),
        fetch_detail=(fetched.detail if fetched else "not_fetched"),
        final_url=url,
        domain=registrable_domain(url),
    )
