"""Product name → VSIC 4-digit classifier (Section C whitelist)."""

from ml.product_categorizer.categorizer import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_MARGIN_THRESHOLD,
    CategorizeResult,
    ProductCategorizer,
    evaluate_precision,
    load_labels,
)

__all__ = [
    "DEFAULT_CONFIDENCE_THRESHOLD",
    "DEFAULT_MARGIN_THRESHOLD",
    "CategorizeResult",
    "ProductCategorizer",
    "evaluate_precision",
    "load_labels",
]
