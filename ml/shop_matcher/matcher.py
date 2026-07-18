"""Fuzzy shop↔company matcher.

Links marketplace shop handles to listed-company names using normalized
Vietnamese tokens, brand aliases, and RapidFuzz ratios. Match threshold
defaults to **0.65** (CONTEXT.md). Only call sites that set ``is_match``
from ``is_match(...)`` should assign a company to a discovered shop.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Iterable

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 0.65

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SEED_FILE = DATA_DIR / "seeds" / "companies.json"
MODEL_PATH = DATA_DIR / "models" / "shop_matcher.joblib"

MARKETPLACE_CHANNELS = frozenset({"shopee", "tiktok", "lazada"})

# Legal / noise tokens stripped from company and shop strings
_COMPANY_NOISE = frozenset(
    {
        "cong",
        "ty",
        "cty",
        "cp",
        "co",
        "phan",
        "tap",
        "doan",
        "tnhh",
        "joint",
        "stock",
        "company",
        "corp",
        "corporation",
        "group",
        "the",
        "va",
        "and",
        "cua",
        "nganh",
        "nghiep",
        # Too generic in VN legal names — never use for handle containment
        "viet",
        "nam",
        "vietnam",
    }
)

_SHOP_NOISE = frozenset(
    {
        "official",
        "store",
        "shop",
        "vn",
        "vietnam",
        "viet",
        "nam",
        "consumer",
        "mall",
        "flagship",
        "global",
        "online",
    }
)

# Distinctive markers in normalized company names → marketplace brand tokens.
# Covers seed 10-DN brands where legal name ≠ handle (e.g. Vinamilk, PNJ).
_BRAND_MARKERS: list[tuple[str, tuple[str, ...]]] = [
    ("rang dong", ("rangdong",)),
    ("bong den", ("rangdong",)),
    ("sua viet nam", ("vinamilk",)),
    ("fpt", ("fpt",)),
    ("masan", ("masan",)),
    ("phu nhuan", ("pnj",)),
    ("vang bac", ("pnj",)),
    ("hoa phat", ("hoaphat",)),
    ("duc giang", ("ducgiang", "ducgiangchem")),
    ("cao su", ("gvr", "caosuvietnam")),
    ("co dien lanh", ("ree", "reecorp")),
    ("nhua binh minh", ("bmp", "binhminh", "nhuabinhminh")),
]


def _strip_diacritics(text: str) -> str:
    # đ/Đ do not decompose under NFD — map explicitly before stripping marks
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _normalize_text(text: str) -> str:
    ascii_text = _strip_diacritics(text or "").lower()
    ascii_text = ascii_text.replace("@", " ")
    ascii_text = re.sub(r"[_\-.]+", " ", ascii_text)
    ascii_text = re.sub(r"[^a-z0-9\s]", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def _tokens(text: str, noise: frozenset[str]) -> list[str]:
    return [t for t in _normalize_text(text).split() if t and t not in noise]


def _brand_aliases(company_name: str) -> list[str]:
    """Return brand handles associated with a company legal name."""
    normalized = _normalize_text(company_name)
    aliases: list[str] = []
    for marker, brands in _BRAND_MARKERS:
        if marker in normalized:
            aliases.extend(brands)
    # de-dupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for a in aliases:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def _company_signals(company_name: str) -> tuple[list[str], str, list[str]]:
    tokens = _tokens(company_name, _COMPANY_NOISE)
    aliases = _brand_aliases(company_name)
    compact = "".join(tokens)
    return tokens, compact, aliases


def _shop_signals(shop_name: str) -> tuple[list[str], str]:
    tokens = _tokens(shop_name, _SHOP_NOISE)
    compact = "".join(tokens) if tokens else re.sub(
        r"[^a-z0-9]", "", _normalize_text(shop_name)
    )
    return tokens, compact


class ShopMatcher:
    """Heuristic fuzzy matcher: company legal name ↔ marketplace shop handle."""

    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        self.threshold = threshold
        self._model_path = MODEL_PATH
        # Optional extra aliases loaded via train() from seed known shops
        self._seed_aliases: dict[str, list[str]] = {}

    def match_score(self, company_name: str, shop_name: str) -> float:
        """Return similarity in [0, 1] between company name and shop handle."""
        if not company_name or not shop_name:
            return 0.0

        company_tokens, company_compact, aliases = _company_signals(company_name)
        shop_tokens, shop_compact = _shop_signals(shop_name)

        seed_extra = self._seed_aliases.get(_normalize_text(company_name), [])
        all_brands = list(dict.fromkeys([*aliases, *seed_extra]))

        strong: list[float] = []

        # Brand-handle containment (latinized official shops)
        for brand in all_brands:
            if not brand or not shop_compact:
                continue
            if brand == shop_compact or shop_compact == brand:
                strong.append(1.0)
            elif len(brand) >= 4 and brand in shop_compact:
                strong.append(0.95)
            elif len(brand) >= 4 and shop_compact in brand:
                strong.append(0.90)
            elif len(brand) >= 3 and brand in shop_compact:
                # short ticker-like brands (fpt, pnj) only when substring of handle
                strong.append(0.92)

        # Distinctive company token ⊂ shop handle
        for tok in company_tokens:
            if len(tok) >= 4 and tok in shop_compact:
                strong.append(0.92)

        # Shop handle token ⊂ company compact (e.g. masan ⊂ tapdoanmasan)
        for tok in shop_tokens:
            if len(tok) >= 4 and tok in company_compact:
                strong.append(0.92)

        if strong:
            return float(min(1.0, max(strong)))

        # Fuzzy fallback — blended, not max(partial) (partial alone false-fires)
        if not company_compact or not shop_compact:
            return 0.0

        company_space = " ".join(company_tokens)
        shop_space = " ".join(shop_tokens)
        ratio = fuzz.ratio(company_compact, shop_compact) / 100.0
        partial = fuzz.partial_ratio(company_compact, shop_compact) / 100.0
        token_sort = (
            fuzz.token_sort_ratio(company_space, shop_space) / 100.0
            if company_space and shop_space
            else 0.0
        )
        # Brand fuzzy vs shop (long brands only)
        brand_fuzzy = 0.0
        for brand in all_brands:
            if len(brand) >= 5:
                brand_fuzzy = max(
                    brand_fuzzy,
                    fuzz.ratio(brand, shop_compact) / 100.0,
                    fuzz.partial_ratio(brand, shop_compact) / 100.0 * 0.85,
                )

        blended = 0.45 * ratio + 0.35 * token_sort + 0.20 * partial
        return float(min(1.0, max(blended, brand_fuzzy)))

    def is_match(
        self,
        company_name: str,
        shop_name: str,
        threshold: float | None = None,
    ) -> bool:
        """True when score >= threshold (default 0.65)."""
        cut = self.threshold if threshold is None else threshold
        return self.match_score(company_name, shop_name) >= cut

    def match(
        self,
        company_name: str,
        shop_name: str,
        threshold: float | None = None,
    ) -> dict[str, float | bool]:
        """Convenience: ``{score, is_match}`` for discovered-shop gating."""
        cut = self.threshold if threshold is None else threshold
        score = self.match_score(company_name, shop_name)
        return {"score": score, "is_match": score >= cut}

    def train(self, db: Session | None = None) -> None:
        """Persist labeled seed pairs + load brand aliases from seed shops.

        ``db`` is accepted for pipeline compatibility; training uses seed JSON.
        """
        del db  # unused — seed file is source of truth for aliases
        import joblib

        self._model_path.parent.mkdir(parents=True, exist_ok=True)
        pairs: list[dict] = []
        self._seed_aliases = {}

        if not SEED_FILE.exists():
            logger.warning("ShopMatcher.train: seed file missing at %s", SEED_FILE)
            return

        with open(SEED_FILE, encoding="utf-8") as f:
            seeds = json.load(f)

        for s in seeds:
            company = s["name"]
            key = _normalize_text(company)
            shop_handles: list[str] = []
            for dp in s.get("digital_presence", []):
                if dp.get("channel_type") not in MARKETPLACE_CHANNELS:
                    continue
                shop_name = dp["url"].rstrip("/").split("/")[-1]
                shop_handles.append(shop_name)
                _, shop_compact = _shop_signals(shop_name)
                if shop_compact and shop_compact not in self._seed_aliases.get(key, []):
                    self._seed_aliases.setdefault(key, []).append(shop_compact)
                pairs.append(
                    {
                        "company": company,
                        "shop": shop_name,
                        "label": 1,
                        "score": self.match_score(company, shop_name),
                    }
                )
            # Also alias website hostname brand when present
            website = s.get("website_url") or ""
            host = re.sub(r"^https?://(www\.)?", "", website).split("/")[0]
            host_brand = host.split(".")[0] if host else ""
            if host_brand and len(host_brand) >= 3:
                self._seed_aliases.setdefault(key, [])
                if host_brand not in self._seed_aliases[key]:
                    self._seed_aliases[key].append(host_brand)

        joblib.dump(
            {
                "pairs": pairs,
                "threshold": self.threshold,
                "seed_aliases": self._seed_aliases,
            },
            self._model_path,
        )

    def load(self) -> bool:
        """Load previously trained alias metadata if present."""
        import joblib

        if not self._model_path.exists():
            return False
        try:
            payload = joblib.load(self._model_path)
            self._seed_aliases = payload.get("seed_aliases") or {}
            if "threshold" in payload:
                self.threshold = float(payload["threshold"])
            return True
        except Exception as exc:  # noqa: BLE001 — optional artifact
            logger.warning("ShopMatcher.load failed: %s", exc)
            return False


def labeled_seed_pairs() -> list[dict]:
    """Return seed positive pairs for QA / tests (company, shop, ticker)."""
    if not SEED_FILE.exists():
        return []
    with open(SEED_FILE, encoding="utf-8") as f:
        seeds = json.load(f)
    out: list[dict] = []
    for s in seeds:
        for dp in s.get("digital_presence", []):
            if dp.get("channel_type") not in MARKETPLACE_CHANNELS:
                continue
            out.append(
                {
                    "ticker": s["stock_code"],
                    "company": s["name"],
                    "shop": dp["url"].rstrip("/").split("/")[-1],
                    "url": dp["url"],
                    "label": 1,
                }
            )
    return out


def iter_company_names(seeds: Iterable[dict] | None = None) -> list[tuple[str, str]]:
    """Return (ticker, company_name) for the seed set."""
    if seeds is None:
        if not SEED_FILE.exists():
            return []
        with open(SEED_FILE, encoding="utf-8") as f:
            seeds = json.load(f)
    return [(s["stock_code"], s["name"]) for s in seeds]
