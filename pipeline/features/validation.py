"""Post-build validation for macro and optional feature frames."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd

# Macro source columns for which ``build_features`` creates standard lags and
# trailing means when the source column is available.
MACRO_LAG_COLS = ("iip", "mei_ip", "indigo")
_REQUIRED_LAGS = (1, 2, 3)
_REQUIRED_ROLLING_WINDOWS = (3, 6)

DIGITAL_FEATURE_COLUMNS = (
    "digital_adoption_score",
    "channel_diversity",
    "online_revenue_ratio",
)
FINANCIAL_FEATURE_COLUMNS = ("roa", "roe", "current_ratio")
CROSS_FEATURE_COLUMNS = ("online_revenue_ratio_x_iip_growth",)

_LAG_COLUMN_RE = re.compile(r"^(?P<base>.+)_lag(?P<lag>\d+)$")


class FeatureValidationError(ValueError):
    """Raised when a feature frame is structurally invalid or leaks future data."""


def _missing(columns: Iterable[str], available: pd.Index) -> list[str]:
    return [column for column in columns if column not in available]


def _series_match(actual: pd.Series, expected: pd.Series) -> bool:
    """Compare lag values, allowing normal floating-point round-off."""
    actual_missing = actual.isna()
    expected_missing = expected.isna()
    if not actual_missing.equals(expected_missing):
        return False

    present = ~actual_missing
    if not present.any():
        return True

    actual_present = actual.loc[present]
    expected_present = expected.loc[present]
    if pd.api.types.is_numeric_dtype(actual_present) and pd.api.types.is_numeric_dtype(
        expected_present
    ):
        return bool(
            np.isclose(
                actual_present.astype(float),
                expected_present.astype(float),
                rtol=1e-9,
                atol=1e-12,
                equal_nan=True,
            ).all()
        )
    return actual_present.equals(expected_present)


def _mei_ip_provenance_columns(columns: pd.Index) -> list[str]:
    """Return recognized peer-country provenance fields for MEI IP."""
    return [
        column
        for column in columns
        if column.lower().startswith("mei_ip")
        and any(token in column.lower() for token in ("country", "peer", "provenance"))
    ]


def validate_feature_frame(
    df: pd.DataFrame,
    *,
    require_digital: bool = False,
    require_financial: bool = False,
    check_lags: bool = True,
) -> dict[str, Any]:
    """Validate a post-build feature frame and return a successful report.

    Hard failures raise :class:`FeatureValidationError`: an invalid base schema,
    fabricated ``mei_bci``, missing required macro-derived columns, invalid lag
    values, Vietnam MEI-IP peer provenance, or explicitly required optional
    feature groups.  When optional groups are not required, their absence is
    recorded in ``notes`` instead.

    Lag comparisons use a frame sorted by ``period`` and compare each
    ``*_lagK`` to its source column shifted by ``K`` rows.  Set
    ``check_lags=False`` when the frame has already dropped warm-up rows (so
    ``shift`` on the truncated frame is no longer a valid identity).  The input
    frame is never reordered or mutated.
    """
    if not isinstance(df, pd.DataFrame):
        raise FeatureValidationError("Feature frame must be a pandas DataFrame.")

    errors: list[str] = []
    notes: list[str] = []
    columns = df.columns

    missing_schema = _missing(("period", "iip"), columns)
    if missing_schema:
        errors.append(
            "Feature frame must contain required columns: "
            + ", ".join(missing_schema)
            + "."
        )

    if "mei_bci" in columns:
        errors.append(
            "Forbidden fabricated feature 'mei_bci' is present. "
            "MEI_BCI is unavailable for VNM and must not be invented."
        )

    for base_column in MACRO_LAG_COLS:
        if base_column not in columns:
            continue
        expected_columns = (
            *(f"{base_column}_lag{lag}" for lag in _REQUIRED_LAGS),
            *(f"{base_column}_roll{window}m" for window in _REQUIRED_ROLLING_WINDOWS),
        )
        missing_derived = _missing(expected_columns, columns)
        if missing_derived:
            errors.append(
                f"Base column '{base_column}' is present but post-build columns "
                f"are missing: {', '.join(missing_derived)}."
            )

    if check_lags and "period" in columns:
        sorted_frame = df.sort_values("period", kind="stable").reset_index(drop=True)
        for feature_column in columns:
            match = _LAG_COLUMN_RE.match(feature_column)
            if not match:
                continue
            base_column = match.group("base")
            lag = int(match.group("lag"))
            if base_column not in sorted_frame.columns:
                errors.append(
                    f"Lag feature '{feature_column}' has no source column "
                    f"'{base_column}'."
                )
                continue
            expected = sorted_frame[base_column].shift(lag)
            if not _series_match(sorted_frame[feature_column], expected):
                errors.append(
                    f"Future-leak check failed: '{feature_column}' must equal "
                    f"'{base_column}.shift({lag})' after sorting by period."
                )
    elif not check_lags:
        notes.append("Lag future-leak check skipped (frame may be post warm-up dropna).")

    if "mei_ip" in columns:
        provenance_columns = _mei_ip_provenance_columns(columns)
        if not provenance_columns:
            # MEI_IP's EA20 peer policy is enforced in the macro load path via
            # PEER_MEI_IP_COUNTRY; this frame need not duplicate provenance.
            notes.append(
                "MEI-IP provenance is absent; EA20 peer policy is enforced at the load path."
            )
        for provenance_column in provenance_columns:
            values = df[provenance_column].dropna().astype(str).str.upper()
            if values.eq("VNM").any():
                errors.append(
                    f"MEI-IP provenance column '{provenance_column}' contains VNM; "
                    "MEI_IP must use a non-Vietnam peer (EA20)."
                )

    optional_groups = (
        ("digital", DIGITAL_FEATURE_COLUMNS, require_digital),
        ("financial", FINANCIAL_FEATURE_COLUMNS, require_financial),
    )
    for group_name, group_columns, required in optional_groups:
        absent = _missing(group_columns, columns)
        if not absent:
            continue
        message = f"Missing {group_name} feature columns: {', '.join(absent)}."
        if required:
            errors.append(message)
        else:
            notes.append(message)

    if errors:
        raise FeatureValidationError(" ".join(errors))

    return {
        "valid": True,
        "notes": notes,
        "checked_macro_columns": [
            column for column in MACRO_LAG_COLS if column in columns
        ],
    }
