"""Tier-1 hard rules: cart, payments, marketplace/social hrefs, language hints."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from crawlers.extraction_cascade.config_loader import load_config
from crawlers.extraction_cascade.schema import EvidenceHit, Tier1Indicators

_ASCII_WORD_RE_CACHE: dict[str, re.Pattern[str]] = {}


def _keyword_present(text: str, keyword: str) -> bool:
    kw = keyword.lower()
    if kw.isascii() and " " not in kw:
        pattern = _ASCII_WORD_RE_CACHE.get(kw)
        if pattern is None:
            pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            _ASCII_WORD_RE_CACHE[kw] = pattern
        return pattern.search(text) is not None
    return kw in text


def _host_of(url: str) -> str:
    try:
        host = (urlparse(url).netloc or "").lower()
    except Exception:  # noqa: BLE001 — bad href
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def _absolutize(base_url: str | None, href: str) -> str:
    href = (href or "").strip()
    if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
        return ""
    if base_url:
        return urljoin(base_url, href)
    return href


def _match_host_map(host: str, host_map: dict[str, list[str]]) -> str | None:
    if not host:
        return None
    for platform, hosts in host_map.items():
        for needle in hosts:
            needle = needle.lower()
            if host == needle or host.endswith("." + needle):
                return platform
    return None


def _compile_any(patterns: list[str]) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)


def analyze_page_rules(
    html: str,
    *,
    base_url: str | None = None,
    locale: str = "vi",
) -> Tier1Indicators:
    """Rule-based indicators from HTML. Never invents when html is empty."""
    cfg = load_config(locale)
    evidence: list[EvidenceHit] = []
    if html is None:
        html = ""
    text = html.lower()
    soup = BeautifulSoup(html, "html.parser") if html.strip() else None

    has_catalog = False
    for kw in cfg.get("catalog_keywords") or []:
        if _keyword_present(text, str(kw)):
            has_catalog = True
            evidence.append(EvidenceHit("catalog_keyword", str(kw)))
            break

    has_cart = False
    for kw in cfg.get("order_cart_keywords") or []:
        if _keyword_present(text, str(kw)):
            has_cart = True
            evidence.append(EvidenceHit("cart_keyword", str(kw)))
            break

    href_re = _compile_any(list(cfg.get("order_cart_href_patterns") or []))
    form_re = _compile_any(list(cfg.get("order_cart_form_patterns") or []))

    payments: list[str] = []
    payment_markers: dict[str, list[str]] = cfg.get("payment_markers") or {}
    for token, markers in payment_markers.items():
        for marker in markers:
            if _keyword_present(text, str(marker)):
                if token not in payments:
                    payments.append(token)
                    evidence.append(EvidenceHit("payment_marker", f"{token}:{marker}"))
                break

    social_links: list[dict[str, str]] = []
    marketplace_links: list[dict[str, str]] = []
    seen_social: set[str] = set()
    seen_mkt: set[str] = set()
    social_hosts = cfg.get("social_hosts") or {}
    mkt_hosts = cfg.get("marketplace_hosts") or {}

    if soup is not None:
        for a in soup.find_all("a", href=True):
            href = a.get("href") or ""
            if href_re.search(href):
                has_cart = True
                has_catalog = True
                evidence.append(EvidenceHit("cart_href", href[:120]))
            abs_url = _absolutize(base_url, href)
            host = _host_of(abs_url)
            mkt = _match_host_map(host, mkt_hosts)
            if mkt and abs_url not in seen_mkt:
                seen_mkt.add(abs_url)
                marketplace_links.append({"platform": mkt, "url": abs_url})
                evidence.append(EvidenceHit("marketplace_href", f"{mkt}:{abs_url[:120]}"))
                continue
            soc = _match_host_map(host, social_hosts)
            if soc and abs_url not in seen_social:
                # TikTok shop hosts already counted as marketplace above when matched.
                seen_social.add(abs_url)
                social_links.append({"platform": soc, "url": abs_url})
                evidence.append(EvidenceHit("social_href", f"{soc}:{abs_url[:120]}"))

        if not has_cart:
            for form in soup.find_all("form", action=True):
                action = form.get("action") or ""
                if form_re.search(action):
                    has_cart = True
                    has_catalog = True
                    evidence.append(EvidenceHit("cart_form", action[:120]))
                    break

        # img alt / src hints for payment logos
        for img in soup.find_all("img"):
            blob = " ".join(
                str(img.get(attr) or "") for attr in ("alt", "src", "title", "aria-label")
            ).lower()
            if not blob:
                continue
            for token, markers in payment_markers.items():
                if token in payments:
                    continue
                if any(m.lower() in blob for m in markers):
                    payments.append(token)
                    evidence.append(EvidenceHit("payment_img", f"{token}:{blob[:80]}"))

    lang = _detect_language(text, cfg.get("language_hints") or {})
    if lang:
        evidence.append(EvidenceHit("language_hint", lang))

    if has_cart:
        has_catalog = True

    return Tier1Indicators(
        has_product_catalog=has_catalog,
        has_order_cart=has_cart,
        payment_methods=payments,
        social_links=social_links,
        marketplace_links=marketplace_links,
        website_language=lang,
        evidence=evidence,
    )


def _detect_language(text: str, hints: dict[str, list[str]]) -> str | None:
    if not text.strip():
        return None
    scores: dict[str, int] = {}
    for code, needles in hints.items():
        score = 0
        for n in needles:
            if n.lower() in text:
                score += 1
        if score:
            scores[code] = score
    if not scores:
        return "unknown"
    if "vi" in scores and scores["vi"] >= 2:
        if "en" in scores and scores["en"] >= 3 and scores["en"] > scores["vi"]:
            return "mixed"
        return "vi"
    if "en" in scores and scores["en"] >= 2:
        return "en"
    best = max(scores, key=scores.get)
    if len(scores) > 1:
        return "mixed"
    return best
