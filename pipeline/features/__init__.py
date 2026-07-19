"""Public exports for the feature-engineering package."""

from pipeline.features.digital_features import (
    DIGITAL_FEATURE_COLUMNS,
    aggregate_digital_features,
    digital_features_for_calendar,
    load_digital_metrics_frame,
)
from pipeline.features.engineering import build_features, load_macro_dataframe, run_feature_engineering
from pipeline.features.financial_features import (
    FINANCIAL_FEATURE_COLUMNS,
    aggregate_financial_features,
    compute_firm_ratios,
    financial_features_for_calendar,
    load_financial_reports_frame,
)
from pipeline.features.macro_helpers import add_lag_features, add_rolling_features
from pipeline.features.validation import (
    CROSS_FEATURE_COLUMNS,
    FeatureValidationError,
    validate_feature_frame,
)

__all__ = [
    "DIGITAL_FEATURE_COLUMNS",
    "FINANCIAL_FEATURE_COLUMNS",
    "CROSS_FEATURE_COLUMNS",
    "FeatureValidationError",
    "add_lag_features",
    "add_rolling_features",
    "aggregate_digital_features",
    "aggregate_financial_features",
    "build_features",
    "compute_firm_ratios",
    "digital_features_for_calendar",
    "financial_features_for_calendar",
    "load_digital_metrics_frame",
    "load_financial_reports_frame",
    "load_macro_dataframe",
    "run_feature_engineering",
    "validate_feature_frame",
]
