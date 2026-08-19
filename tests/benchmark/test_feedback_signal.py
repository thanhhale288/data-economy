"""Task #64 — Feedback-to-training signal (safe: no raw PDF/bytes/API keys)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.main import app
from backend.app.schemas.feedback_signal import FeedbackSignalIn, FieldDiff
from backend.app.services import feedback_signal as svc
from backend.app.services import ml_monitoring as monitoring_svc


@pytest.fixture()
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "training_signals.jsonl"


@pytest.fixture()
def db_session(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from backend.app.database import Base

    engine = create_engine(f"sqlite:///{tmp_path / 'feedback_test.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_edit_confirm_creates_one_signal_record(store_path: Path):
    payload = FeedbackSignalIn(
        source_type="docai_extract",
        ticker="RAL",
        before={"operating_revenue": 1_000_000, "employees": 100},
        after={"operating_revenue": 1_200_000, "employees": 100},
    )
    out = svc.append_signal(payload, store_path=store_path)

    assert out.stored is True
    assert out.signal.diff_count == 1
    assert out.signal.ticker == "RAL"
    assert out.signal.source_type == "docai_extract"
    assert out.signal.timestamp is not None
    assert len(out.signal.field_diffs) == 1
    assert out.signal.field_diffs[0].field == "operating_revenue"
    assert out.signal.field_diffs[0].before == 1_000_000
    assert out.signal.field_diffs[0].after == 1_200_000

    lines = store_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert set(record.keys()) >= {
        "id",
        "timestamp",
        "field_diffs",
        "ticker",
        "source_type",
        "diff_count",
    }
    assert "raw_pdf" not in record
    assert "file_bytes" not in record
    assert "api_key" not in record
    assert "filename" not in record
    assert "content" not in record


def test_does_not_persist_raw_pdf_or_secrets(store_path: Path):
    """Poisoned client payload must never land in the JSONL store."""
    # Extra forbidden keys are ignored by schema (extra='ignore').
    poisoned = FeedbackSignalIn.model_validate(
        {
            "source_type": "docai_extract",
            "ticker": "ABC",
            "field_diffs": [
                {"field": "employees", "before": 10, "after": 12},
            ],
            "raw_pdf": b"%PDF-1.4 fake binary",
            "file_bytes": "AQID",
            "api_key": "sk-secret-should-never-store",
            "content": "data:application/pdf;base64," + ("A" * 600),
            "filename": "/tmp/secret-report.pdf",
        }
    )
    out = svc.append_signal(poisoned, store_path=store_path)
    blob = store_path.read_text(encoding="utf-8").lower()

    assert out.stored is True
    assert "raw_pdf" not in blob
    assert "file_bytes" not in blob
    assert "api_key" not in blob
    assert "sk-secret" not in blob
    assert "%pdf" not in blob
    assert "secret-report.pdf" not in blob
    assert "authorization" not in blob

    record = json.loads(store_path.read_text(encoding="utf-8").strip())
    assert list(record["field_diffs"][0].keys()) == ["field", "before", "after"]


def test_assert_record_is_safe_rejects_binary_diff_value():
    with pytest.raises(ValueError, match="binary|secret|unsafe|forbidden"):
        svc.assert_record_is_safe(
            {
                "id": "x",
                "timestamp": "2024-01-01T00:00:00",
                "source_type": "docai_extract",
                "field_diffs": [
                    {"field": "employees", "before": 1, "after": b"\x00\x01"},
                ],
                "diff_count": 1,
            }
        )


def test_benchmark_feedback_api(store_path: Path, monkeypatch, db_session):
    monkeypatch.setattr(svc, "DEFAULT_STORE_PATH", store_path)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        res = client.post(
            "/api/benchmark/feedback",
            json={
                "source_type": "docai_extract",
                "ticker": "RAL",
                "before": {"profit_before_tax": 100},
                "after": {"profit_before_tax": 150},
                "raw_pdf": "SHOULD_BE_IGNORED",
                "api_key": "SHOULD_BE_IGNORED",
            },
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["stored"] is True
        assert body["signal"]["diff_count"] == 1
        assert body["signal"]["ticker"] == "RAL"
        blob = store_path.read_text(encoding="utf-8").lower()
        assert "should_be_ignored" not in blob
        assert "raw_pdf" not in blob
        assert "api_key" not in blob
    finally:
        app.dependency_overrides.clear()


def test_monitoring_counter_includes_feedback_signals(db_session, store_path: Path, tmp_path):
    svc.append_signal(
        FeedbackSignalIn(
            source_type="cafef_prefill",
            ticker="RAL",
            field_diffs=[
                FieldDiff(field="employees", before=10, after=11),
            ],
        ),
        store_path=store_path,
    )
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    status = monitoring_svc.get_monitoring_status(
        db_session,
        baseline_path=tmp_path / "missing_baseline.json",
        models_dir=models_dir,
        feedback_store_path=store_path,
    )
    assert status.counters.feedback_signals_count == 1


def test_scheduler_ingest_hook_counts(store_path: Path):
    svc.append_signal(
        FeedbackSignalIn(
            source_type="manual",
            before={"vsic_code": "2410"},
            after={"vsic_code": "2420"},
        ),
        store_path=store_path,
    )
    count, detail = svc.ingest_feedback_for_scheduler(store_path=store_path)
    assert count == 1
    assert "feedback_signals=1" in detail

@pytest.mark.parametrize("source_type", ["cafef_prefill", "manual"])
def test_cafef_prefill_and_manual_source_types_store_diffs_not_pdf(source_type, store_path: Path):
    """Task #78 — CafeF prefill and typed forms use existing source_type values; never raw PDF."""
    payload = FeedbackSignalIn.model_validate(
        {
            "source_type": source_type,
            "ticker": "RAL",
            "before": {"operating_revenue": 100, "employees": 8, "vsic_code": "2750"},
            "after": {"operating_revenue": 150, "employees": 8, "vsic_code": "2750"},
            "raw_pdf": b"%PDF-1.4 should-never-store",
            "file_bytes": "AQID",
            "api_key": "sk-secret-should-never-store",
            "filename": "/tmp/bctc.pdf",
        }
    )
    out = svc.append_signal(payload, store_path=store_path)

    assert out.stored is True
    assert out.signal.source_type == source_type
    assert out.signal.diff_count == 1
    assert out.signal.field_diffs[0].field == "operating_revenue"
    assert out.signal.field_diffs[0].before == 100
    assert out.signal.field_diffs[0].after == 150

    blob = store_path.read_text(encoding="utf-8").lower()
    record = json.loads(store_path.read_text(encoding="utf-8").strip())
    assert "raw_pdf" not in blob
    assert "file_bytes" not in blob
    assert "api_key" not in blob
    assert "sk-secret" not in blob
    assert "%pdf" not in blob
    assert "bctc.pdf" not in blob
    assert "filename" not in record
    assert list(record["field_diffs"][0].keys()) == ["field", "before", "after"]


def test_benchmark_feedback_api_accepts_cafef_and_manual(store_path: Path, monkeypatch, db_session):
    monkeypatch.setattr(svc, "DEFAULT_STORE_PATH", store_path)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        for source_type in ("cafef_prefill", "manual"):
            res = client.post(
                "/api/benchmark/feedback",
                json={
                    "source_type": source_type,
                    "ticker": "vnm",
                    "before": {"profit_before_tax": 10},
                    "after": {"profit_before_tax": 20},
                    "raw_pdf": "SHOULD_BE_IGNORED",
                    "api_key": "SHOULD_BE_IGNORED",
                },
            )
            assert res.status_code == 200, res.text
            body = res.json()
            assert body["stored"] is True
            assert body["signal"]["source_type"] == source_type
            assert body["signal"]["ticker"] == "VNM"
            assert body["signal"]["diff_count"] == 1
        blob = store_path.read_text(encoding="utf-8").lower()
        assert "should_be_ignored" not in blob
        assert "raw_pdf" not in blob
        assert "api_key" not in blob
        lines = [ln for ln in store_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 2
        types = {json.loads(ln)["source_type"] for ln in lines}
        assert types == {"cafef_prefill", "manual"}
    finally:
        app.dependency_overrides.clear()

