"""Pure unit tests for ml.evaluation.metrics."""

from __future__ import annotations

import numpy as np
import pytest

from ml.evaluation.metrics import compute_all_metrics, mae, mape, rmse


def test_mae_known_values():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 33.0])
    # | -2| + |2| + |-3| = 7 / 3
    assert mae(y_true, y_pred) == pytest.approx(7.0 / 3.0)


def test_rmse_known_values():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 33.0])
    # sqrt((4 + 4 + 9) / 3) = sqrt(17/3)
    assert rmse(y_true, y_pred) == pytest.approx(np.sqrt(17.0 / 3.0))


def test_mape_known_values():
    y_true = np.array([100.0, 200.0, 50.0])
    y_pred = np.array([110.0, 180.0, 50.0])
    # (0.1 + 0.1 + 0.0) / 3 * 100 = 20/3
    assert mape(y_true, y_pred) == pytest.approx(20.0 / 3.0)


def test_mape_ignores_zero_targets():
    y_true = np.array([0.0, 100.0])
    y_pred = np.array([5.0, 110.0])
    assert mape(y_true, y_pred) == pytest.approx(10.0)


def test_mape_all_zeros_returns_zero():
    y_true = np.array([0.0, 0.0])
    y_pred = np.array([1.0, 2.0])
    assert mape(y_true, y_pred) == 0.0


def test_compute_all_metrics_rounds():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 33.0])
    out = compute_all_metrics(y_true, y_pred)
    assert set(out) == {"mae", "rmse", "mape"}
    assert out["mae"] == round(7.0 / 3.0, 4)
    assert out["rmse"] == round(np.sqrt(17.0 / 3.0), 4)
    # mape: mean(|2|/10, |2|/20, |3|/30)*100 = mean(0.2, 0.1, 0.1)*100
    assert out["mape"] == round((0.2 + 0.1 + 0.1) / 3.0 * 100.0, 4)
