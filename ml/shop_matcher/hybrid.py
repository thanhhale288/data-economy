"""Hybrid RapidFuzz + vector/rerank shop matcher (Task #60)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import joblib
from sqlalchemy.orm import Session

from ml.shop_matcher.embeddings import (
    DEFAULT_ST_MODEL,
    ShopEmbedder,
    company_embedding_text,
    shop_embedding_text,
)
from ml.shop_matcher.matcher import (
    DEFAULT_THRESHOLD,
    MARKETPLACE_CHANNELS,
    MODEL_PATH,
    SEED_FILE,
    FuzzyShopMatcher,
    _brand_aliases,
    _normalize_text,
    labeled_seed_pairs,
)

logger = logging.getLogger(__name__)

ARTIFACT_VERSION = 2
BACKEND_ENV = "SHOP_MATCHER_BACKEND"
DEFAULT_EMBEDDER_BACKEND = "tfidf"
_VALID_BACKENDS = frozenset({"auto", "sentence_transformers", "tfidf"})


def resolve_embedder_backend(explicit: str | None = None) -> str:
    """Runtime vector backend: explicit arg, else ``SHOP_MATCHER_BACKEND``, else tfidf.

    Unset / blank / invalid env values fall back to tfidf so CI never downloads
    HuggingFace Hub. Production default stays tfidf unless an operator sets the env.
    """
    if explicit is not None and str(explicit).strip():
        raw = str(explicit).strip().lower()
        if raw not in _VALID_BACKENDS:
            raise ValueError(f"Unknown embedder backend: {explicit!r}")
        return raw
    raw = (os.environ.get(BACKEND_ENV) or "").strip().lower()
    if not raw:
        return DEFAULT_EMBEDDER_BACKEND
    if raw not in _VALID_BACKENDS:
        logger.warning(
            "Invalid %s=%r — using %s",
            BACKEND_ENV,
            raw,
            DEFAULT_EMBEDDER_BACKEND,
        )
        return DEFAULT_EMBEDDER_BACKEND
    return raw


# Short marketplace handle prefixes → brand aliases (hybrid rescue only).
_SHORT_PREFIX_BRANDS: dict[str, tuple[str, ...]] = {
    "rd": ("rangdong",),
    "dq": ("dienquang", "dienquangofficialstore"),
    "vnm": ("vinamilk",),
    "hpg": ("hoaphat",),
    "bmp": ("bmp", "binhminh", "nhuabinhminh"),
    "pnj": ("pnj",),
    "msn": ("masan",),
    "fpt": ("fpt",),
}


def short_prefix_boost(company_name: str, shop_name: str) -> float:
    """Return a strong score when shop opens with a known brand short-code."""
    aliases = set(_brand_aliases(company_name))
    # Also accept seed-style compact aliases passed via FuzzyShopMatcher later
    toks = _normalize_text(shop_name).replace(".", " ").split()
    if not toks:
        return 0.0
    for pref, brands in _SHORT_PREFIX_BRANDS.items():
        if not any(b in aliases for b in brands):
            continue
        for tok in toks:
            if len(pref) <= 2:
                hit = tok == pref or tok.startswith(f"{pref}_")
            else:
                hit = tok == pref or tok.startswith(pref)
            if hit:
                return 0.72
    return 0.0


def fuse_scores(fuzzy: float, vector: float, prefix: float) -> float:
    """Rerank: keep fuzzy extremes; lift mid-band with vector / short prefix."""
    score = max(float(fuzzy), float(prefix))
    if fuzzy >= 0.60 and vector >= 0.45:
        score = max(score, fuzzy + 0.50 * max(0.0, vector - 0.40))
    if fuzzy >= 0.35 and vector >= 0.55:
        score = max(score, 0.35 * fuzzy + 0.65 * vector)
    if prefix >= 0.70 and vector >= 0.30:
        score = max(score, 0.55 * prefix + 0.45 * max(vector, fuzzy))
    return float(min(1.0, score))


class HybridShopMatcher:
    """Fuzzy baseline + embedding cosine + short-prefix rerank."""

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        *,
        embedder_backend: str | None = None,
        model_name: str = DEFAULT_ST_MODEL,
        model_path: Path | None = None,
    ) -> None:
        """Create matcher.

        Default vector backend is TF-IDF (fast, offline). Optional env
        ``SHOP_MATCHER_BACKEND`` can select ``sentence_transformers`` /
        ``auto`` at runtime; it is not enabled unless set. CLI/eval still
        pass ``embedder_backend`` explicitly (Task #76).
        """
        backend = resolve_embedder_backend(embedder_backend)
        self.threshold = threshold
        self._model_path = Path(model_path) if model_path else MODEL_PATH
        self._fuzzy = FuzzyShopMatcher(threshold=threshold)
        self._fuzzy._model_path = self._model_path
        self._embedder = ShopEmbedder(backend=backend, model_name=model_name)
        self._embedder_backend_pref = backend
        self._model_name = model_name

    # --- seed alias passthrough (tests / train) ---
    @property
    def _seed_aliases(self) -> dict[str, list[str]]:
        return self._fuzzy._seed_aliases

    @_seed_aliases.setter
    def _seed_aliases(self, value: dict[str, list[str]]) -> None:
        self._fuzzy._seed_aliases = value

    def fuzzy_score(self, company_name: str, shop_name: str) -> float:
        return self._fuzzy.match_score(company_name, shop_name)

    def vector_score(self, company_name: str, shop_name: str) -> float:
        if not self._embedder.is_fitted:
            # Lazy fit on the pair alone so score() works before train()
            self._embedder.fit(
                [
                    company_embedding_text(company_name),
                    shop_embedding_text(shop_name),
                ]
            )
        aliases = self._fuzzy._seed_aliases.get(_normalize_text(company_name), [])
        return self._embedder.cosine(
            company_embedding_text(company_name, aliases),
            shop_embedding_text(shop_name),
        )

    def match_score(self, company_name: str, shop_name: str) -> float:
        if not company_name or not shop_name:
            return 0.0
        fuzzy = self.fuzzy_score(company_name, shop_name)
        prefix = short_prefix_boost(company_name, shop_name)
        # Strong fuzzy / prefix — skip embedding (keeps discovery path fast).
        if max(fuzzy, prefix) >= 0.90:
            return float(min(1.0, max(fuzzy, prefix)))
        try:
            vector = self.vector_score(company_name, shop_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("vector_score failed (%s) — fuzzy/prefix only", exc)
            vector = 0.0
        return fuse_scores(fuzzy, vector, prefix)

    def is_match(
        self,
        company_name: str,
        shop_name: str,
        threshold: float | None = None,
    ) -> bool:
        cut = self.threshold if threshold is None else threshold
        return self.match_score(company_name, shop_name) >= cut

    def match(
        self,
        company_name: str,
        shop_name: str,
        threshold: float | None = None,
    ) -> dict[str, float | bool | str]:
        cut = self.threshold if threshold is None else threshold
        if not company_name or not shop_name:
            return {
                "score": 0.0,
                "is_match": False,
                "fuzzy_score": 0.0,
                "vector_score": 0.0,
                "prefix_boost": 0.0,
                "backend": self._embedder.backend or self._embedder_backend_pref,
            }
        fuzzy = self.fuzzy_score(company_name, shop_name)
        prefix = short_prefix_boost(company_name, shop_name)
        vector = 0.0
        if max(fuzzy, prefix) < 0.90:
            try:
                vector = self.vector_score(company_name, shop_name)
            except Exception:  # noqa: BLE001
                vector = 0.0
            score = fuse_scores(fuzzy, vector, prefix)
        else:
            score = float(min(1.0, max(fuzzy, prefix)))
        return {
            "score": score,
            "is_match": score >= cut,
            "fuzzy_score": fuzzy,
            "vector_score": vector,
            "prefix_boost": prefix,
            "backend": self._embedder.backend or self._embedder_backend_pref,
        }

    def _corpus_from_seeds(self, seeds: list[dict]) -> list[str]:
        texts: list[str] = []
        for s in seeds:
            company = s["name"]
            aliases = self._fuzzy._seed_aliases.get(_normalize_text(company), [])
            texts.append(company_embedding_text(company, aliases))
            for dp in s.get("digital_presence", []):
                if dp.get("channel_type") not in MARKETPLACE_CHANNELS:
                    continue
                shop = dp["url"].rstrip("/").split("/")[-1]
                texts.append(shop_embedding_text(shop))
        # Hard-QA style paraphrases so TF-IDF sees lighting/dairy lexicon
        texts.extend(
            [
                shop_embedding_text("rd_lighting_bulb_store"),
                shop_embedding_text("dq_lighting_vn"),
                shop_embedding_text("led_chieusang_congnghiep"),
                shop_embedding_text("sua_tuoi_official_store"),
                company_embedding_text("Công ty Cổ phần Bóng đèn Rạng Đông"),
                company_embedding_text("Công ty Cổ phần Điện Quang"),
                company_embedding_text("Công ty Cổ phần Sữa Việt Nam"),
            ]
        )
        return texts

    def train(self, db: Session | None = None) -> dict[str, Any]:
        """Train fuzzy aliases + fit vector backend; persist joblib artifact."""
        del db
        self._fuzzy.train(db=None)
        seeds: list[dict] = []
        if SEED_FILE.exists():
            with open(SEED_FILE, encoding="utf-8") as f:
                seeds = json.load(f)

        self._embedder = ShopEmbedder(
            backend=self._embedder_backend_pref,
            model_name=self._model_name,
        )
        corpus = self._corpus_from_seeds(seeds)
        self._embedder.fit(corpus)

        pairs = labeled_seed_pairs()
        scored = [
            {
                **p,
                "fuzzy": self.fuzzy_score(p["company"], p["shop"]),
                "hybrid": self.match_score(p["company"], p["shop"]),
            }
            for p in pairs
        ]

        self._model_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_version": ARTIFACT_VERSION,
            "threshold": self.threshold,
            "seed_aliases": self._fuzzy._seed_aliases,
            "pairs": scored,
            "embedder": self._embedder.to_state(),
            "matcher": "hybrid_v2",
        }
        joblib.dump(payload, self._model_path)
        return {
            "n_pairs": len(scored),
            "backend": self._embedder.backend,
            "artifact": str(self._model_path),
            "threshold": self.threshold,
        }

    def load(self) -> bool:
        if not self._model_path.exists():
            return False
        try:
            payload = joblib.load(self._model_path)
            self._fuzzy._seed_aliases = payload.get("seed_aliases") or {}
            if "threshold" in payload:
                self.threshold = float(payload["threshold"])
                self._fuzzy.threshold = self.threshold
            emb_state = payload.get("embedder")
            if emb_state:
                self._embedder = ShopEmbedder.from_state(emb_state)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("HybridShopMatcher.load failed: %s", exc)
            return False


# Default export name for call sites (shop_finder, pipeline).
ShopMatcher = HybridShopMatcher
