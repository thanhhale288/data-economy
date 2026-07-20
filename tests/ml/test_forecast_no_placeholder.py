"""Prove forecast_* / generate_forecast are not the old growth placeholder."""

from __future__ import annotations

import numpy as np
import pytest


def growth_placeholder(last: float, horizon: int) -> np.ndarray:
    """Old trainer placeholder: last * (1 + 0.008 * i) for i=1..h."""
    return np.asarray(
        [last * (1.0 + 0.008 * i) for i in range(1, horizon + 1)], dtype=float
    )


def test_forecast_arima_not_placeholder(synthetic_iip_series, tmp_path):
    pytest.importorskip("statsmodels")
    from ml.models.arima_model import forecast_arima, train_arima_model

    path = tmp_path / "arima_model.joblib"
    train_arima_model(
        synthetic_iip_series,
        periods=synthetic_iip_series.index,
        artifact_path=path,
    )
    horizon = 6
    preds = forecast_arima(path, steps=horizon)
    last = float(synthetic_iip_series.iloc[-1])
    placeholder = growth_placeholder(last, horizon)
    assert preds.shape == (horizon,)
    assert not np.allclose(preds, placeholder, rtol=0, atol=1e-6)


def test_forecast_xgboost_not_placeholder(synthetic_feature_frame, tmp_path):
    pytest.importorskip("xgboost")
    from ml.models.xgboost_model import forecast_xgboost, train_xgboost_model

    train_xgboost_model(
        synthetic_feature_frame,
        artifact_dir=tmp_path,
        n_estimators=20,
        max_depth=3,
    )
    horizon = 6
    preds = forecast_xgboost(
        tmp_path / "xgboost_model.joblib",
        history_df=synthetic_feature_frame,
        steps=horizon,
    )
    last = float(synthetic_feature_frame["iip"].iloc[-1])
    placeholder = growth_placeholder(last, horizon)
    assert preds.shape == (horizon,)
    assert not np.allclose(preds, placeholder, rtol=0, atol=1e-6)


def test_forecast_lstm_not_placeholder(synthetic_iip_series, tmp_path):
    pytest.importorskip("torch")
    from ml.models.lstm_model import forecast_lstm, train_lstm_model

    train_lstm_model(
        synthetic_iip_series,
        periods=synthetic_iip_series.index,
        epochs=5,
        horizon=6,
        seq_len=12,
        artifact_dir=tmp_path,
        seed=7,
    )
    horizon = 6
    preds = forecast_lstm(
        tmp_path,
        history=synthetic_iip_series.values,
        steps=horizon,
    )
    last = float(synthetic_iip_series.iloc[-1])
    placeholder = growth_placeholder(last, horizon)
    assert preds.shape == (horizon,)
    assert not np.allclose(preds, placeholder, rtol=0, atol=1e-6)


def test_generate_forecast_arima_not_placeholder(
    monkeypatch, tmp_path, synthetic_iip_series
):
    """Optional trainer path: monkeypatch MODELS_DIR + sqlite IIP rows."""
    pytest.importorskip("statsmodels")
    from datetime import date

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from backend.app.database import Base
    from backend.app.models import GsoMacro, VsicCode
    from ml.models import trainer as trainer_mod
    from ml.models.arima_model import train_arima_model

    artifact_path = tmp_path / "arima_model.joblib"
    train_arima_model(
        synthetic_iip_series,
        periods=synthetic_iip_series.index,
        artifact_path=artifact_path,
    )

    monkeypatch.setattr(trainer_mod, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(trainer_mod, "ARIMA_ARTIFACT", artifact_path)

    engine = create_engine(f"sqlite:///{tmp_path / 'forecast_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(
        VsicCode(
            vsic_code="C",
            isic_code="C",
            level=1,
            name_vi="Che bien",
            name_en="Manufacturing",
        )
    )
    for period, value in synthetic_iip_series.items():
        p = period.date() if hasattr(period, "date") else date(period.year, period.month, 1)
        db.add(
            GsoMacro(
                vsic_code="C",
                indicator_code="IIP_C",
                indicator_name="IIP Section C",
                period=p,
                value=float(value),
                unit="index",
                source="test",
            )
        )
    db.commit()

    try:
        horizon = 6
        out = trainer_mod.generate_forecast(db, "arima", horizon)
        assert out["model"] == "arima"
        assert out["horizon"] == horizon
        assert len(out["forecasts"]) == horizon
        preds = np.asarray([f["predicted_value"] for f in out["forecasts"]], dtype=float)
        last = float(synthetic_iip_series.iloc[-1])
        placeholder = growth_placeholder(last, horizon)
        # generate_forecast rounds to 2 decimals — compare against rounded placeholder
        placeholder_rounded = np.round(placeholder, 2)
        assert not np.allclose(preds, placeholder_rounded, rtol=0, atol=1e-6)
    finally:
        db.close()
        engine.dispose()
