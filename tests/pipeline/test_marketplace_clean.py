"""Unit tests for pipeline.cleaning.marketplace_clean — outliers, nulls, matcher."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.shop_matcher import DEFAULT_THRESHOLD
from pipeline.cleaning.marketplace_clean import (
    clean_marketplace_listings,
    resolve_shop_to_company,
)


COMPANIES = {
    1: "Công ty Cổ phần Bóng đèn Rạng Đông",
    2: "Tập đoàn Hòa Phát",
    3: "Công ty Cổ phần Sữa Việt Nam",
}


def _listings_frame(**overrides) -> pd.DataFrame:
    base = {
        "price": [45_000.0, 50_000.0, 48_000.0, 47_000.0, 49_000.0, 5_000_000.0],
        "units_sold_est": [100, 110, 105, 95, 102, 108],
        "revenue_est": [4_500_000.0, 5_500_000.0, 5_040_000.0, 4_465_000.0, 4_998_000.0, None],
        "shop_name": [
            "rangdong_official",
            "unrelated_random_shop_xyz",
            "vinamilk_official",
            None,
            "rangdong_official",
            "hoaphat_steel",
        ],
        "company_id": [None, None, None, None, 1, None],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def test_clean_marketplace_does_not_impute_nulls():
    df = _listings_frame()
    # Explicit nulls in price / units must stay null (no invented fills).
    df.loc[1, "price"] = np.nan
    df.loc[2, "units_sold_est"] = np.nan
    cleaned, prov = clean_marketplace_listings(
        df,
        company_names=COMPANIES,
        outlier_method="iqr",
        outlier_action="flag",
        run_entity_resolution=False,
    )
    assert pd.isna(cleaned.loc[1, "price"])
    assert pd.isna(cleaned.loc[2, "units_sold_est"])
    assert pd.isna(cleaned.loc[5, "revenue_est"])
    assert prov.nulls_preserved["price"] >= 1
    assert prov.nulls_preserved["units_sold_est"] >= 1
    assert prov.nulls_preserved["revenue_est"] >= 1


def test_clean_marketplace_flag_keeps_outlier_values():
    df = _listings_frame()
    cleaned, prov = clean_marketplace_listings(
        df,
        company_names=None,
        outlier_method="iqr",
        outlier_action="flag",
        run_entity_resolution=False,
    )
    assert "price_outlier" in cleaned.columns
    assert prov.outliers_flagged.get("price", 0) >= 1
    # Flag path keeps the extreme price
    assert cleaned.loc[5, "price"] == 5_000_000.0
    assert bool(cleaned.loc[5, "price_outlier"]) is True


def test_clean_marketplace_winsorize_clips_outliers():
    df = _listings_frame()
    cleaned, prov = clean_marketplace_listings(
        df,
        outlier_method="iqr",
        outlier_action="winsorize",
        run_entity_resolution=False,
    )
    assert cleaned.loc[5, "price"] < 5_000_000.0
    assert cleaned.loc[5, "price"] > 0
    assert prov.outliers_flagged.get("price", 0) >= 1


def test_clean_marketplace_null_action_nullifies_outliers():
    df = _listings_frame()
    cleaned, prov = clean_marketplace_listings(
        df,
        outlier_method="iqr",
        outlier_action="null",
        run_entity_resolution=False,
    )
    assert pd.isna(cleaned.loc[5, "price"])
    assert prov.outliers_nullified.get("price", 0) >= 1


def test_resolve_shop_below_threshold_no_company_id():
    company_id, score = resolve_shop_to_company(
        "completely_unrelated_marketplace_handle_zzz",
        COMPANIES,
        threshold=DEFAULT_THRESHOLD,
    )
    assert company_id is None
    assert score < DEFAULT_THRESHOLD


def test_resolve_shop_at_or_above_threshold_assigns():
    company_id, score = resolve_shop_to_company(
        "rangdong_official",
        COMPANIES,
        threshold=DEFAULT_THRESHOLD,
    )
    assert company_id == 1
    assert score >= DEFAULT_THRESHOLD


def test_resolve_shop_exact_threshold_boundary_assigns():
    """Score == threshold must assign (contract: at/above → company_id)."""

    class _FixedMatcher:
        threshold = DEFAULT_THRESHOLD

        def match_score(self, company: str, shop: str) -> float:
            return DEFAULT_THRESHOLD  # exactly 0.65

    company_id, score = resolve_shop_to_company(
        "any_shop",
        {9: "Any Company"},
        threshold=DEFAULT_THRESHOLD,
        matcher=_FixedMatcher(),  # type: ignore[arg-type]
    )
    assert score == DEFAULT_THRESHOLD
    assert company_id == 9


def test_resolve_shop_just_below_threshold_skips():
    class _FixedMatcher:
        threshold = DEFAULT_THRESHOLD

        def match_score(self, company: str, shop: str) -> float:
            return DEFAULT_THRESHOLD - 1e-9

    company_id, score = resolve_shop_to_company(
        "any_shop",
        {9: "Any Company"},
        threshold=DEFAULT_THRESHOLD,
        matcher=_FixedMatcher(),  # type: ignore[arg-type]
    )
    assert company_id is None
    assert score < DEFAULT_THRESHOLD


def test_clean_marketplace_entity_resolution_threshold():
    df = _listings_frame()
    cleaned, prov = clean_marketplace_listings(
        df,
        company_names=COMPANIES,
        outlier_method="none",
        run_entity_resolution=True,
    )
    # Existing company_id=1 on row 4 must be preserved (idempotent).
    assert cleaned.loc[4, "company_id"] == 1
    # Positive RAL shop → assigned
    assert cleaned.loc[0, "company_id"] == 1
    # Unrelated shop → no invent
    assert pd.isna(cleaned.loc[1, "company_id"]) or cleaned.loc[1, "company_id"] is None
    assert prov.matches_assigned >= 1
    assert prov.matches_skipped_below_threshold >= 1
    assert prov.threshold == DEFAULT_THRESHOLD


def test_clean_marketplace_deterministic_no_random():
    df = _listings_frame()
    a, pa = clean_marketplace_listings(
        df, company_names=COMPANIES, outlier_method="iqr", outlier_action="flag"
    )
    b, pb = clean_marketplace_listings(
        df, company_names=COMPANIES, outlier_method="iqr", outlier_action="flag"
    )
    pd.testing.assert_frame_equal(a, b)
    assert pa.to_dict() == pb.to_dict()
