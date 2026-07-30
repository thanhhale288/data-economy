"""Shop ↔ company name matching (threshold 0.65 per CONTEXT.md).

Default ``ShopMatcher`` is the Task #60 hybrid (RapidFuzz + vector/rerank).
``FuzzyShopMatcher`` remains available as the v1 baseline for QA gates.
"""

from ml.shop_matcher.hybrid import HybridShopMatcher, ShopMatcher
from ml.shop_matcher.matcher import DEFAULT_THRESHOLD, FuzzyShopMatcher

__all__ = [
    "DEFAULT_THRESHOLD",
    "FuzzyShopMatcher",
    "HybridShopMatcher",
    "ShopMatcher",
]
