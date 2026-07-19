"""Unit tests for pipeline.cleaning.cleaner — gaps, IQR, Z-score, provenance."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.cleaning.cleaner import (
    CleanProvenance,
    clean_timeseries,
    detect_outliers_iqr,
    detect_outliers_zscore,
    fill_missing_long_gaps,
    fill_missing_short_gaps,
)


def test_fill_missing_short_gaps_fills_run_of_length_at_most_max_gap():
    # Contiguous NaN run of length 2 (default max_gap) between known endpoints.
    s = pd.Series([10.0, np.nan, np.nan, 40.0])
    out = fill_missing_short_gaps(s, max_gap=2)
    assert out.isna().sum() == 0
    assert out.iloc[1] == pytest.approx(20.0)
    assert out.iloc[2] == pytest.approx(30.0)


def test_fill_missing_short_gaps_leaves_longer_runs_as_nan():
    # Run of 3 NaNs > max_gap=2 → stay NaN until long pass.
    s = pd.Series([10.0, np.nan, np.nan, np.nan, 50.0])
    out = fill_missing_short_gaps(s, max_gap=2)
    assert out.isna().tolist() == [False, True, True, True, False]
    assert out.iloc[0] == 10.0
    assert out.iloc[4] == 50.0


def test_fill_missing_short_gaps_respects_custom_max_gap():
    s = pd.Series([0.0, np.nan, np.nan, np.nan, 4.0])
    out = fill_missing_short_gaps(s, max_gap=3)
    assert out.isna().sum() == 0
    assert list(out) == pytest.approx([0.0, 1.0, 2.0, 3.0, 4.0])


def test_fill_missing_long_gaps_unlimited_linear():
    s = pd.Series([10.0, np.nan, np.nan, np.nan, 50.0])
    out = fill_missing_long_gaps(s)
    assert out.isna().sum() == 0
    assert list(out) == pytest.approx([10.0, 20.0, 30.0, 40.0, 50.0])


def test_clean_timeseries_short_then_long_with_provenance():
    df = pd.DataFrame(
        {
            "period": pd.date_range("2024-01-01", periods=7, freq="MS"),
            "value": [10.0, np.nan, np.nan, np.nan, 50.0, np.nan, 70.0],
        }
    )
    # Positions 1–3: long run (3) → long_gap; position 5: short run (1) → short_gap.
    cleaned, prov = clean_timeseries(
        df,
        value_col="value",
        max_gap=2,
        fill_long_gaps=True,
        outlier_method="none",
        return_provenance=True,
    )
    assert isinstance(prov, CleanProvenance)
    assert cleaned["value"].isna().sum() == 0
    assert prov.short_gap_filled == 1
    assert prov.long_gap_filled == 3
    assert prov.outliers_detected == 0
    assert prov.outlier_method == "none"
    assert cleaned["value"].iloc[1] == pytest.approx(20.0)
    assert cleaned["value"].iloc[5] == pytest.approx(60.0)


def test_clean_timeseries_fill_long_gaps_false_leaves_long_runs():
    df = pd.DataFrame({"value": [10.0, np.nan, np.nan, np.nan, 50.0]})
    cleaned, prov = clean_timeseries(
        df,
        fill_long_gaps=False,
        outlier_method="none",
        return_provenance=True,
    )
    assert cleaned["value"].isna().sum() == 3
    assert prov.long_gap_filled == 0
    assert any("long gaps" in n for n in prov.notes)


def test_detect_outliers_iqr_flags_extremes_not_nans():
    # Tight cluster + one clear high outlier; NaN must not be flagged.
    s = pd.Series([10.0, 11.0, 12.0, 10.5, 11.5, 100.0, np.nan])
    mask = detect_outliers_iqr(s, factor=1.5)
    assert mask.dtype == bool or mask.dtype == np.bool_
    assert bool(mask.iloc[5]) is True
    assert bool(mask.iloc[6]) is False  # NaN never flagged
    assert int(mask.sum()) >= 1


def test_detect_outliers_zscore_flags_extremes_not_nans():
    # Many near-equal points so a single spike clears |z| > 3 (ddof=0).
    s = pd.Series([10.0] * 30 + [1_000.0, np.nan])
    mask = detect_outliers_zscore(s, threshold=3.0)
    assert bool(mask.iloc[30]) is True
    assert bool(mask.iloc[31]) is False  # NaN never flagged
    assert int(mask.sum()) == 1


def test_detect_outliers_iqr_zero_spread_flags_none():
    s = pd.Series([5.0, 5.0, 5.0, 5.0])
    mask = detect_outliers_iqr(s)
    assert not mask.any()


def test_clean_timeseries_iqr_median_is_deterministic():
    values = [10.0, 11.0, 12.0, 10.5, 11.5, 10.2, 11.1, 12.2, 10.8, 200.0]
    df = pd.DataFrame({"value": values})
    a, pa = clean_timeseries(
        df, outlier_method="iqr", outlier_action="median", return_provenance=True
    )
    b, pb = clean_timeseries(
        df, outlier_method="iqr", outlier_action="median", return_provenance=True
    )
    pd.testing.assert_series_equal(a["value"], b["value"])
    assert pa.outliers_detected == pb.outliers_detected
    assert pa.outliers_detected >= 1
    assert pa.outliers_handled == pa.outliers_detected
    assert a["value"].iloc[-1] != 200.0
    assert a["value"].iloc[-1] == pytest.approx(float(pd.Series(values).median()))


def test_clean_timeseries_zscore_selectable():
    values = [10.0] * 30 + [1_000.0]
    df = pd.DataFrame({"value": values})
    cleaned, prov = clean_timeseries(
        df,
        outlier_method="zscore",
        outlier_action="null",
        zscore_threshold=3.0,
        return_provenance=True,
    )
    assert prov.outlier_method == "zscore"
    assert prov.zscore_threshold == 3.0
    assert prov.outliers_detected >= 1
    assert cleaned["value"].isna().sum() == prov.outliers_handled
    assert pd.isna(cleaned["value"].iloc[-1])


def test_clean_timeseries_winsorize_clips_to_fences():
    values = [10.0, 11.0, 12.0, 10.5, 11.5, 10.2, 11.1, 12.2, 10.8, 200.0]
    df = pd.DataFrame({"value": values})
    cleaned, prov = clean_timeseries(
        df,
        outlier_method="iqr",
        outlier_action="winsorize",
        return_provenance=True,
    )
    assert prov.outliers_handled >= 1
    assert cleaned["value"].iloc[-1] < 200.0
    assert cleaned["value"].notna().all()


def test_clean_timeseries_without_provenance_returns_dataframe_only():
    df = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
    out = clean_timeseries(df, outlier_method="none")
    assert isinstance(out, pd.DataFrame)
    assert "value" in out.columns


def test_provenance_to_dict_keys():
    df = pd.DataFrame({"value": [1.0, np.nan, 3.0]})
    _, prov = clean_timeseries(df, outlier_method="none", return_provenance=True)
    d = prov.to_dict()
    for key in (
        "value_col",
        "short_gap_filled",
        "long_gap_filled",
        "outliers_detected",
        "outliers_handled",
        "outlier_method",
        "outlier_action",
        "max_gap",
    ):
        assert key in d
