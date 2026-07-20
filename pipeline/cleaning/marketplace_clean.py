"""Clean marketplace listing scrapes: outliers + optional shop↔company resolution.

``MarketplaceListing`` has no ``shop_name`` column — listings are usually already
tied to a company at scrape/upsert time. Numeric outlier cleaning is the primary
path for listing DataFrames. Use ``resolve_shop_to_company`` for shop-discovery
rows (or any frame that carries a shop handle) before assigning ``company_id``.

Does **not** invent values for missing price / units / revenue — nulls stay null
and are counted in provenance. Persistence (DB upsert of flags / company_id) is
left to the caller / DAG layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

from ml.shop_matcher import DEFAULT_THRESHOLD, ShopMatcher

try:
    from pipeline.cleaning.cleaner import detect_outliers_iqr as _detect_outliers_iqr
except ImportError:  # pragma: no cover — package layout fallback
    _detect_outliers_iqr = None  # type: ignore[assignment]

NUMERIC_COLS = ("price", "units_sold_est", "revenue_est")
OutlierMethod = Literal["iqr", "zscore", "none"]
OutlierAction = Literal["flag", "winsorize", "null"]


def detect_outliers_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
    """Boolean mask of IQR outliers (True = outlier). NaNs are False."""
    if _detect_outliers_iqr is not None:
        mask = _detect_outliers_iqr(series, factor=factor)
        return mask.fillna(False).astype(bool)
    numeric = pd.to_numeric(series, errors="coerce")
    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    iqr = q3 - q1
    if pd.isna(iqr) or iqr == 0:
        return pd.Series(False, index=series.index)
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return ((numeric < lower) | (numeric > upper)).fillna(False)


def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Boolean mask of |z| > threshold outliers. NaNs are False."""
    numeric = pd.to_numeric(series, errors="coerce")
    mean = numeric.mean()
    std = numeric.std(ddof=0)
    if pd.isna(std) or std == 0 or pd.isna(mean):
        return pd.Series(False, index=series.index)
    z = (numeric - mean) / std
    return (z.abs() > threshold).fillna(False)


def _iqr_fences(series: pd.Series, factor: float = 1.5) -> tuple[float, float] | None:
    numeric = pd.to_numeric(series, errors="coerce")
    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    iqr = q3 - q1
    if pd.isna(iqr) or pd.isna(q1) or pd.isna(q3):
        return None
    return float(q1 - factor * iqr), float(q3 + factor * iqr)


def _zscore_fences(series: pd.Series, threshold: float = 3.0) -> tuple[float, float] | None:
    numeric = pd.to_numeric(series, errors="coerce")
    mean = numeric.mean()
    std = numeric.std(ddof=0)
    if pd.isna(std) or std == 0 or pd.isna(mean):
        return None
    return float(mean - threshold * std), float(mean + threshold * std)


def _outlier_flag_col(value_col: str) -> str:
    return f"{value_col}_outlier"


@dataclass
class MarketplaceCleanProvenance:
    rows_in: int
    rows_out: int
    nulls_preserved: dict[str, int]
    outliers_flagged: dict[str, int]
    outliers_nullified: dict[str, int]
    matches_assigned: int
    matches_skipped_below_threshold: int
    outlier_method: str
    threshold: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def resolve_shop_to_company(
    shop_name: str,
    companies: dict[int, str],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    matcher: ShopMatcher | None = None,
) -> tuple[int | None, float]:
    """Best company match for a marketplace shop handle.

    Returns ``(company_id, score)``. ``company_id`` is ``None`` when no candidate
    reaches ``threshold`` (default 0.65). Does not invent a company assignment.
    """
    if not shop_name or not companies:
        return None, 0.0

    m = matcher or ShopMatcher(threshold=threshold)
    best_id: int | None = None
    best_score = 0.0
    for company_id, name in companies.items():
        if not name:
            continue
        score = m.match_score(name, shop_name)
        if score > best_score:
            best_score = score
            best_id = int(company_id)

    if best_id is None or best_score < threshold:
        return None, float(best_score)
    return best_id, float(best_score)


def _company_id_is_set(value: object) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return True


def clean_marketplace_listings(
    df: pd.DataFrame,
    *,
    company_names: dict[int, str] | None = None,
    shop_name_col: str = "shop_name",
    outlier_method: OutlierMethod = "iqr",
    outlier_action: OutlierAction = "flag",
    iqr_factor: float = 1.5,
    zscore_threshold: float = 3.0,
    match_threshold: float = DEFAULT_THRESHOLD,
    run_entity_resolution: bool = True,
) -> tuple[pd.DataFrame, MarketplaceCleanProvenance]:
    """Clean a marketplace listings DataFrame (copy); never invent numeric fills.

    Outlier handling (``price``, ``units_sold_est``, ``revenue_est`` when present):
    - ``flag`` (default): keep values; set ``{col}_outlier`` booleans (idempotent).
    - ``winsorize``: clip to method fences (deterministic).
    - ``null``: set outlier cells to NaN (removes suspects; does not invent).

    Entity resolution: existing non-null ``company_id`` is left unchanged. If
    ``shop_name_col`` is present and ``company_names`` is provided, unmatched
    rows may receive ``company_id`` only when ``ShopMatcher`` score ≥ threshold.
    ``MarketplaceListing`` itself has no shop field — without ``shop_name_col``,
    matching is skipped and noted; use ``resolve_shop_to_company`` for discovery.
    """
    out = df.copy()
    notes: list[str] = []
    rows_in = len(out)

    nulls_preserved: dict[str, int] = {}
    for col in NUMERIC_COLS:
        if col in out.columns:
            nulls_preserved[col] = int(out[col].isna().sum())
            # Explicit: do not impute — leave NaN as-is
        else:
            notes.append(f"column_missing:{col}")

    outliers_flagged: dict[str, int] = {}
    outliers_nullified: dict[str, int] = {}

    if outlier_method == "none":
        notes.append("outlier_detection_skipped")
    else:
        for col in NUMERIC_COLS:
            if col not in out.columns:
                continue

            series = out[col]
            if outlier_method == "iqr":
                mask = detect_outliers_iqr(series, factor=iqr_factor)
                fences = _iqr_fences(series, factor=iqr_factor)
            else:
                mask = detect_outliers_zscore(series, threshold=zscore_threshold)
                fences = _zscore_fences(series, threshold=zscore_threshold)

            flag_col = _outlier_flag_col(col)
            # Idempotent flag: recompute from current values (deterministic)
            out[flag_col] = mask.astype(bool)
            flagged_n = int(mask.sum())
            outliers_flagged[col] = flagged_n

            if outlier_action == "flag":
                continue

            if flagged_n == 0:
                outliers_nullified[col] = 0
                continue

            if outlier_action == "winsorize":
                if fences is None:
                    notes.append(f"winsorize_skipped_no_fences:{col}")
                    outliers_nullified[col] = 0
                    continue
                lower, upper = fences
                numeric = pd.to_numeric(out[col], errors="coerce")
                clipped = numeric.clip(lower=lower, upper=upper)
                # Only touch non-null outliers; preserve original nulls
                out.loc[mask & numeric.notna(), col] = clipped.loc[mask & numeric.notna()]
                outliers_nullified[col] = 0
            elif outlier_action == "null":
                before_null = int(out[col].isna().sum())
                out.loc[mask, col] = np.nan
                after_null = int(out[col].isna().sum())
                outliers_nullified[col] = after_null - before_null
                nulls_preserved[col] = after_null

    matches_assigned = 0
    matches_skipped_below_threshold = 0

    if not run_entity_resolution:
        notes.append("entity_resolution_skipped")
    elif shop_name_col not in out.columns:
        notes.append(
            f"entity_resolution_skipped: no '{shop_name_col}' column "
            "(MarketplaceListing has no shop_name; use resolve_shop_to_company "
            "for shop-discovery rows)"
        )
    elif not company_names:
        notes.append("entity_resolution_skipped: company_names not provided")
    else:
        if "company_id" not in out.columns:
            out["company_id"] = pd.NA
        if "match_score" not in out.columns:
            out["match_score"] = np.nan

        matcher = ShopMatcher(threshold=match_threshold)
        for idx in out.index:
            if _company_id_is_set(out.at[idx, "company_id"]):
                continue  # idempotent: keep existing assignment

            shop = out.at[idx, shop_name_col]
            if shop is None or (isinstance(shop, float) and pd.isna(shop)) or str(shop).strip() == "":
                continue

            company_id, score = resolve_shop_to_company(
                str(shop),
                company_names,
                threshold=match_threshold,
                matcher=matcher,
            )
            out.at[idx, "match_score"] = score
            if company_id is not None:
                out.at[idx, "company_id"] = company_id
                matches_assigned += 1
            else:
                matches_skipped_below_threshold += 1

    if "clean_notes" not in out.columns:
        out["clean_notes"] = ""
    # Deterministic summary note per row (idempotent overwrite of our tag)
    method_tag = f"outliers={outlier_method}/{outlier_action}"
    out["clean_notes"] = out["clean_notes"].fillna("").astype(str)
    # Avoid duplicating the same tag on re-run
    def _merge_note(existing: str) -> str:
        existing = existing.strip()
        if method_tag in existing:
            return existing
        return f"{existing}; {method_tag}".strip("; ").strip()

    out["clean_notes"] = out["clean_notes"].map(_merge_note)

    provenance = MarketplaceCleanProvenance(
        rows_in=rows_in,
        rows_out=len(out),
        nulls_preserved=nulls_preserved,
        outliers_flagged=outliers_flagged,
        outliers_nullified=outliers_nullified,
        matches_assigned=matches_assigned,
        matches_skipped_below_threshold=matches_skipped_below_threshold,
        outlier_method=outlier_method,
        threshold=match_threshold,
        notes=notes,
    )
    return out, provenance
