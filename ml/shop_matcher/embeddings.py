"""Vector backends for shop↔company matching (Task #60).

Primary: ``sentence-transformers`` multilingual MiniLM.
Offline/CI fallback: char TF-IDF fitted on the training corpus (still a
vector path so hybrid logic and tests run without a Hub download).
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Iterable, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

DEFAULT_ST_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Industry / brand lexicon appended to company docs (helps TF-IDF + ST).
_BRAND_HINTS: dict[str, str] = {
    "rangdong": "den led bong den lighting bulb chieu sang cong nghiep",
    "dienquang": "den led lighting bulb dien quang chieu sang",
    "dienquangofficialstore": "den led lighting bulb",
    "vinamilk": "sua tuoi dairy milk yogurt",
    "hoaphat": "thep steel xay dung",
    "fpt": "cong nghe digital tech",
    "masan": "thuc pham consumer food",
    "pnj": "vang bac trang suc jewelry gold",
    "gvr": "cao su rubber",
    "bmp": "nhua plastic pipe ong",
    "ree": "co dien lanh electric",
    "vinhhoan": "ca tra thuy san seafood",
    "namviet": "thuy san seafood",
    "anphat": "nhua plastic bio",
}

_SHOP_SYNONYMS: list[tuple[str, str]] = [
    ("chieusang", "chieu sang lighting den led"),
    ("lighting", "chieu sang den led bulb"),
    ("bongden", "bong den bulb lighting"),
    ("suatuoi", "sua tuoi milk dairy"),
    ("trangsuc", "trang suc jewelry vang"),
    ("jewelry", "trang suc vang bac"),
]


def _strip_diacritics(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def normalize_for_embed(text: str) -> str:
    ascii_text = _strip_diacritics(text or "").lower()
    ascii_text = ascii_text.replace("@", " ")
    ascii_text = re.sub(r"[_\-.]+", " ", ascii_text)
    ascii_text = re.sub(r"[^a-z0-9\s]", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def expand_synonyms(text: str) -> str:
    """Append marketplace synonym phrases when compact needles appear."""
    base = normalize_for_embed(text)
    compact = base.replace(" ", "")
    extra: list[str] = []
    for needle, phrase in _SHOP_SYNONYMS:
        if needle in compact or needle in base:
            extra.append(phrase)
    if not extra:
        return base
    return f"{base} {' '.join(extra)}".strip()


def company_embedding_text(company_name: str, aliases: Sequence[str] | None = None) -> str:
    """Rich company document for vector encode (name + aliases + hints)."""
    from ml.shop_matcher.matcher import _brand_aliases, _company_signals

    tokens, compact, marker_aliases = _company_signals(company_name)
    all_aliases = list(dict.fromkeys([*(aliases or ()), *marker_aliases]))
    parts = [
        expand_synonyms(company_name),
        " ".join(tokens),
        " ".join(all_aliases),
        compact,
    ]
    for alias in all_aliases:
        hint = _BRAND_HINTS.get(alias)
        if hint:
            parts.append(hint)
    return " ".join(p for p in parts if p).strip()


def shop_embedding_text(shop_name: str) -> str:
    from ml.shop_matcher.matcher import _shop_signals

    tokens, compact = _shop_signals(shop_name)
    return " ".join(
        p for p in (expand_synonyms(shop_name), " ".join(tokens), compact) if p
    ).strip()


class ShopEmbedder:
    """Encode shop/company strings to L2-normalizable vectors."""

    def __init__(
        self,
        backend: str = "auto",
        model_name: str = DEFAULT_ST_MODEL,
    ) -> None:
        if backend not in {"auto", "sentence_transformers", "tfidf"}:
            raise ValueError(f"Unknown embedder backend: {backend!r}")
        self.backend_requested = backend
        self.model_name = model_name
        self.backend: str | None = None
        self._st = None
        self._tfidf: TfidfVectorizer | None = None

    @property
    def is_fitted(self) -> bool:
        return self.backend is not None and (
            self._st is not None or self._tfidf is not None
        )

    def _try_load_st(self) -> bool:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            logger.warning("sentence-transformers not installed — using TF-IDF")
            return False
        try:
            self._st = SentenceTransformer(self.model_name)
            self.backend = "sentence_transformers"
            return True
        except Exception as exc:  # noqa: BLE001 — Hub/offline fallback
            logger.warning(
                "Could not load SentenceTransformer %s (%s) — using TF-IDF",
                self.model_name,
                exc,
            )
            self._st = None
            return False

    def fit(self, corpus: Iterable[str]) -> "ShopEmbedder":
        texts = [t for t in (str(x).strip() for x in corpus) if t]
        if not texts:
            texts = ["placeholder"]

        want_st = self.backend_requested in {"auto", "sentence_transformers"}
        want_tfidf = self.backend_requested in {"auto", "tfidf"}

        if want_st and self.backend_requested == "sentence_transformers":
            if not self._try_load_st():
                raise RuntimeError(
                    "sentence_transformers backend requested but model unavailable"
                )
            # Still fit TF-IDF as portable artifact companion
            want_tfidf = True
        elif want_st and self.backend_requested == "auto":
            self._try_load_st()

        if want_tfidf or self.backend is None:
            self._tfidf = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                min_df=1,
                sublinear_tf=True,
            )
            self._tfidf.fit(texts)
            if self.backend is None:
                self.backend = "tfidf"
        return self

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("ShopEmbedder.fit() required before encode()")
        cleaned = [t if t else " " for t in texts]
        if self.backend == "sentence_transformers" and self._st is not None:
            vectors = self._st.encode(
                cleaned,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return np.asarray(vectors, dtype=np.float64)
        assert self._tfidf is not None
        matrix = self._tfidf.transform(cleaned)
        dense = np.asarray(matrix.toarray(), dtype=np.float64)
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-12)
        return dense / norms

    def cosine(self, a: str, b: str) -> float:
        va, vb = self.encode([a, b])
        return float(np.dot(va, vb))

    def cosine_matrix(self, left: Sequence[str], right: Sequence[str]) -> np.ndarray:
        if not left or not right:
            return np.zeros((len(left), len(right)), dtype=np.float64)
        return cosine_similarity(self.encode(left), self.encode(right))

    def to_state(self) -> dict:
        return {
            "backend_requested": self.backend_requested,
            "backend": self.backend,
            "model_name": self.model_name,
            "tfidf": self._tfidf,
            # ST model is re-loaded by name; do not pickle the full weights.
        }

    @classmethod
    def from_state(cls, state: dict) -> "ShopEmbedder":
        obj = cls(
            backend=state.get("backend_requested") or "tfidf",
            model_name=state.get("model_name") or DEFAULT_ST_MODEL,
        )
        obj.backend = state.get("backend") or "tfidf"
        obj._tfidf = state.get("tfidf")
        if obj.backend == "sentence_transformers":
            # Prefer live ST; fall back to stored TF-IDF if Hub unavailable.
            if not obj._try_load_st():
                if obj._tfidf is not None:
                    obj.backend = "tfidf"
                else:
                    raise RuntimeError("Cannot restore embedder without TF-IDF or ST")
        elif obj._tfidf is None:
            raise RuntimeError("TF-IDF missing from embedder state")
        return obj
