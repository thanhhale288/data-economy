"""Rule-based website ecommerce / checkout detector.

Detects shop/catalog signals and checkout/cart signals from HTML keywords
and light structural cues (cart forms, checkout links). Never guesses on
HTTP failure — returns DetectionResult(ok=False) so callers can keep prior state.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 15.0
USER_AGENT = "Mozilla/5.0 (compatible; MfgDataEconomy/1.0; +research)"

# Catalog / shop presence (broader than checkout).
ECOMMERCE_KEYWORDS: tuple[str, ...] = (
    "shop",
    "cửa hàng",
    "sản phẩm",
    "product",
    "mua hàng",
    "cửa hàng trực tuyến",
    "online store",
    "add to cart",
    "giỏ hàng",
)

# Purchase / cart / payment flow.
CHECKOUT_KEYWORDS: tuple[str, ...] = (
    "giỏ hàng",
    "cart",
    "checkout",
    "mua ngay",
    "đặt hàng",
    "add to cart",
    "shop now",
    "thanh toán",
    "thêm vào giỏ",
)

CHECKOUT_HREF_RE = re.compile(
    r"(checkout|/cart\b|gio-hang|giỏ-hàng|thanh-toan|thanh-toán|/basket\b)",
    re.IGNORECASE,
)
CART_FORM_ACTION_RE = re.compile(
    r"(cart|checkout|gio-hang|thanh-toan|add[_-]?to[_-]?cart)",
    re.IGNORECASE,
)

# ASCII tokens need word boundaries ("shop" must not match "showroom").
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


@dataclass(frozen=True)
class DetectionResult:
    """Outcome of website digital detection for one URL/page."""

    ok: bool
    has_ecommerce: bool = False
    has_checkout: bool = False
    detail: str = ""


def analyze_html(html: str) -> DetectionResult:
    """Rule-based detect ecommerce/checkout from HTML (always ok=True)."""
    if html is None:
        html = ""
    text = html.lower()
    soup = BeautifulSoup(html, "html.parser") if html.strip() else None

    has_ecommerce = any(_keyword_present(text, kw) for kw in ECOMMERCE_KEYWORDS)
    has_checkout = any(_keyword_present(text, kw) for kw in CHECKOUT_KEYWORDS)

    if soup is not None:
        # Structural: checkout/cart links.
        for a in soup.find_all("a", href=True):
            href = a.get("href") or ""
            if CHECKOUT_HREF_RE.search(href):
                has_ecommerce = True
                has_checkout = True
                break
        # Structural: forms posting to cart/checkout.
        if not has_checkout:
            for form in soup.find_all("form", action=True):
                action = form.get("action") or ""
                if CART_FORM_ACTION_RE.search(action):
                    has_ecommerce = True
                    has_checkout = True
                    break

    return DetectionResult(
        ok=True,
        has_ecommerce=has_ecommerce,
        has_checkout=has_checkout,
        detail="analyzed",
    )


def detect_website(url: str, *, client: httpx.Client | None = None) -> DetectionResult:
    """Fetch URL and detect ecommerce/checkout. On HTTP fail/block: ok=False."""
    if not url or not str(url).strip():
        return DetectionResult(ok=False, detail="missing_url")

    owns_client = client is None
    http = client or httpx.Client(
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )
    try:
        response = http.get(url)
        if response.status_code != 200:
            detail = f"http_fail status={response.status_code}"
            logger.warning("Website detect fail %s: %s — not guessing", url, detail)
            return DetectionResult(ok=False, detail=detail)
        analyzed = analyze_html(response.text)
        return DetectionResult(
            ok=True,
            has_ecommerce=analyzed.has_ecommerce,
            has_checkout=analyzed.has_checkout,
            detail="ok",
        )
    except Exception as exc:  # noqa: BLE001 — network/parse; never invent flags
        detail = f"error:{type(exc).__name__}:{exc}"
        logger.warning("Website detect fail %s: %s — not guessing", url, detail)
        return DetectionResult(ok=False, detail=detail)
    finally:
        if owns_client:
            http.close()
