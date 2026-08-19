"""Shop ↔ company name matching (threshold 0.65 per CONTEXT.md).

Default ``ShopMatcher`` is the Task #60 hybrid (RapidFuzz + vector/rerank).
Runtime vector backend defaults to TF-IDF; optional ``SHOP_MATCHER_BACKEND``
can select sentence-transformers without changing the production default.
``FuzzyShopMatcher`` remains available as the v1 baseline for QA gates.
"""

from ml.shop_matcher.hybrid import (
    BACKEND_ENV,
    DEFAULT_EMBEDDER_BACKEND,
    HybridShopMatcher,
    ShopMatcher,
    resolve_embedder_backend,
)
from ml.shop_matcher.matcher import DEFAULT_THRESHOLD, FuzzyShopMatcher

__all__ = [
    "BACKEND_ENV",
    "DEFAULT_EMBEDDER_BACKEND",
    "DEFAULT_THRESHOLD",
    "FuzzyShopMatcher",
    "HybridShopMatcher",
    "ShopMatcher",
    "resolve_embedder_backend",
]
