"""Walk-forward split tests: chronological order, no leakage."""

from __future__ import annotations

import numpy as np
import pytest

from ml.evaluation.walk_forward import (
    assert_no_leakage,
    evaluate_walk_forward,
    iter_time_splits,
)


def test_fixed_split_2020_2024_indices(monthly_periods_2020_2024):
    """train_end=2023-12, test_start=2024-01 → train 0..47, test 48..59."""
    periods = monthly_periods_2020_2024
    assert len(periods) == 60

    splits = list(
        iter_time_splits(
            periods,
            train_end="2023-12",
            test_start="2024-01",
            min_train_size=24,
            mode="fixed",
        )
    )
    assert len(splits) == 1
    split = splits[0]

    assert split.train_indices.tolist() == list(range(0, 48))
    assert split.test_indices.tolist() == list(range(48, 60))
    assert split.train_end == periods[47]
    assert split.test_start == periods[48]
    assert_no_leakage(split)
    assert int(split.train_indices.max()) < int(split.test_indices.min())


def test_assert_no_leakage_raises_on_overlap():
    from ml.evaluation.walk_forward import TimeSplit

    bad = TimeSplit(
        fold=0,
        train_indices=np.array([0, 1, 2, 5]),
        test_indices=np.array([4, 5, 6]),
        train_end=None,
        test_start=None,
    )
    with pytest.raises(AssertionError, match="leakage"):
        assert_no_leakage(bad)


def test_expanding_mode_multiple_folds_no_leakage(monthly_periods_2020_2024):
    periods = monthly_periods_2020_2024
    splits = list(
        iter_time_splits(
            periods,
            train_end="2023-12",
            test_start="2024-01",
            min_train_size=24,
            test_size=3,
            step_size=2,
            mode="expanding",
        )
    )
    assert len(splits) >= 2
    for split in splits:
        assert_no_leakage(split)
        assert int(split.train_indices.max()) < int(split.test_indices.min())
        # Expanding: train always starts at 0
        assert int(split.train_indices[0]) == 0


def test_evaluate_walk_forward_aggregates(monthly_periods_2020_2024, synthetic_iip_series):
    periods = monthly_periods_2020_2024
    y = synthetic_iip_series.values

    def predict_fn(split):
        # Naive: predict last train value for each test step
        last = y[split.train_indices[-1]]
        return np.full(len(split.test_indices), last, dtype=float)

    result = evaluate_walk_forward(
        periods,
        y,
        predict_fn,
        train_end="2023-12",
        test_start="2024-01",
        mode="fixed",
    )
    assert result["status"] == "ok"
    assert result["n_folds"] == 1
    assert result["mae"] is not None
    assert np.isfinite(result["mae"])
    assert np.isfinite(result["rmse"])
    assert np.isfinite(result["mape"])
