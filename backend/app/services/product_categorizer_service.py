"""Thin ProductCategorizer wrapper — load artifact once, never train on request."""

from __future__ import annotations

from functools import lru_cache

from ml.product_categorizer import CategorizeResult, ProductCategorizer


@lru_cache(maxsize=1)
def get_categorizer() -> ProductCategorizer:
    """Module singleton: load ``data/models/product_categorizer.joblib`` once.

    Missing/corrupt artifact is honest — ``predict()`` abstains with
    ``model_not_loaded`` rather than training or inventing a VSIC.
    """
    cat = ProductCategorizer()
    cat.load()
    return cat


def categorize_product(product_name: str) -> CategorizeResult:
    """Classify one product name; abstain → vsic_code=None + reason."""
    return get_categorizer().predict(product_name)
