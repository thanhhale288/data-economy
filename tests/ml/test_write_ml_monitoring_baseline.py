"""Task #72 — write ml_monitoring_baseline.json from ModelRegistry MAPE."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path

import pytest

from backend.app.models import ModelRegistry
from backend.app.services import ml_monitoring as svc


def _load_writer():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "write_ml_monitoring_baseline.py"
    )
    spec = importlib.util.spec_from_file_location("write_ml_monitoring_baseline", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


writer = _load_writer()


@pytest.fixture()
def db_session(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from backend.app.database import Base

    engine = create_engine(f"sqlite:///{tmp_path / 'ml_baseline_writer_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _add_registry(db, name: str, mape, trained_at, *, metrics_extra=None):
    metrics = {"mae": 1.0, "rmse": 1.5}
    if mape is not None:
        metrics["mape"] = mape
    if metrics_extra:
        metrics.update(metrics_extra)
    db.add(
        ModelRegistry(
            model_name=name,
            model_type=name,
            version="1.0",
            metrics=metrics,
            is_active=True,
            trained_at=trained_at,
        )
    )


def test_writer_empty_registry_exits_nonzero_and_writes_nothing(db_session, tmp_path):
    models, omitted = writer.collect_latest_mape(db_session)
    assert models == {}
    assert any(item.endswith(":registry_missing") for item in omitted)

    out = tmp_path / "ml_monitoring_baseline.json"
    payload = writer.build_payload(models)
    with pytest.raises(ValueError, match="empty baseline"):
        writer.write_baseline_file(payload, out, dry_run=False)
    assert not out.exists()

    rc = writer.main(
        [
            "--database-url",
            str(db_session.get_bind().url),
            "--output",
            str(out),
        ]
    )
    assert rc == 1
    assert not out.exists()


def test_writer_sqlite_fixture_mape_then_drift_computes(db_session, tmp_path):
    """Fixture MAPE only — not production numbers."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "arima_model.joblib").write_bytes(b"fake")
    (models_dir / "xgboost_model.joblib").write_bytes(b"fake")

    _add_registry(
        db_session,
        "arima",
        12.0,
        datetime(2024, 6, 1, 12, 0, 0),
    )
    _add_registry(
        db_session,
        "xgboost",
        8.0,
        datetime(2024, 6, 2, 12, 0, 0),
    )
    # Older arima row must not win (latest trained_at).
    db_session.add(
        ModelRegistry(
            model_name="arima",
            model_type="arima",
            version="0.9",
            metrics={"mae": 9.0, "rmse": 9.0, "mape": 99.0},
            is_active=False,
            trained_at=datetime(2024, 1, 1, 0, 0, 0),
        )
    )
    # Non-numeric mape omitted.
    db_session.add(
        ModelRegistry(
            model_name="lstm",
            model_type="lstm",
            version="1.0",
            metrics={"mae": 1.0, "rmse": 1.0, "mape": "n/a"},
            is_active=True,
            trained_at=datetime(2024, 6, 3, 0, 0, 0),
        )
    )
    db_session.commit()

    models, omitted = writer.collect_latest_mape(db_session)
    assert set(models) == {"arima", "xgboost"}
    assert models["arima"]["mape"] == 12.0
    assert models["xgboost"]["mape"] == 8.0
    assert "lstm:mape_missing" in omitted
    assert "lightgbm:registry_missing" in omitted

    out = tmp_path / "ml_monitoring_baseline.json"
    payload = writer.build_payload(models)
    writer.write_baseline_file(payload, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["source"] == "ModelRegistry"
    assert data["mape_drift_threshold"] == 5.0
    assert data["models"]["arima"]["mape"] == 12.0
    assert data["models"]["xgboost"]["mape"] == 8.0
    assert "lstm" not in data["models"]
    assert "lightgbm" not in data["models"]

    # Current MAPE matches baseline → no drift flag; missing file still null (sibling tests).
    status = svc.get_monitoring_status(
        db_session,
        baseline_path=out,
        models_dir=models_dir,
    )
    by_name = {s.model_name: s for s in status.models}
    assert status.counters.baseline_available is True
    assert by_name["arima"].drift_score == pytest.approx(0.0)
    assert by_name["arima"].drift_flag is False
    assert by_name["xgboost"].drift_flag is False
    assert by_name["lstm"].drift_flag is None
    assert by_name["lightgbm"].drift_flag is None


def test_writer_dry_run_does_not_write(db_session, tmp_path):
    _add_registry(db_session, "arima", 4.5, datetime(2024, 6, 1))
    db_session.commit()
    out = tmp_path / "ml_monitoring_baseline.json"
    rc = writer.main(
        [
            "--dry-run",
            "--database-url",
            str(db_session.get_bind().url),
            "--output",
            str(out),
        ]
    )
    assert rc == 0
    assert not out.exists()


def test_writer_skips_missing_mape_does_not_fill_zeros(db_session):
    _add_registry(db_session, "arima", None, datetime(2024, 6, 1))
    db_session.commit()
    models, omitted = writer.collect_latest_mape(db_session)
    assert "arima" not in models
    assert "arima:mape_missing" in omitted
    assert all(row.get("mape") != 0 for row in models.values())
