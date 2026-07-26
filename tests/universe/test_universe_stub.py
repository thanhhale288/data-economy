"""Tests for Task #39 company-universe stub (no invented firms)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.schemas.universe import (
    DIGITAL_VA_COVERAGE_CLAIM,
    UniverseBatchManifest,
    UniverseFirmShallow,
    UniverseIngestStatus,
    UniverseProvenance,
    UniverseSourceType,
)
from backend.app.services.universe_service import (
    can_auto_promote_to_deep_sample,
    coverage_note,
    load_universe_rows,
    promotion_blocked_reason,
    universe_rows_path,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_universe_rows_file_is_empty_array():
    path = universe_rows_path()
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == []


def test_load_universe_rows_returns_empty():
    rows = load_universe_rows()
    assert rows == []


def test_shallow_row_accepts_section_c_vsic_and_nullable_ticker():
    row = UniverseFirmShallow(
        universe_id="example-src:1",
        legal_name="Example Manufacturing Co",
        vsic_code="2410",
        stock_code=None,
        website_url="https://example.invalid",
        provenance=UniverseProvenance(
            source_type=UniverseSourceType.MANUAL_CURATED,
            source_dataset="fixture",
            notes="test only — not a real firm",
        ),
    )
    assert row.vsic_code == "2410"
    assert row.stock_code is None
    assert can_auto_promote_to_deep_sample(row) is False
    assert "onboard" in promotion_blocked_reason(row)


def test_shallow_row_rejects_non_section_c_vsic():
    with pytest.raises(ValidationError):
        UniverseFirmShallow(
            universe_id="bad",
            legal_name="Retailer",
            vsic_code="4711",  # retail, not Section C
        )


def test_batch_manifest_defaults():
    from datetime import datetime, timezone

    manifest = UniverseBatchManifest(
        batch_id="batch-1",
        source_type=UniverseSourceType.UNKNOWN,
        created_at=datetime.now(timezone.utc),
    )
    assert manifest.rate_limit_per_host_seconds == 1.5
    assert manifest.status == UniverseIngestStatus.PENDING
    assert manifest.row_ids == []


def test_coverage_note_is_prototype_not_national():
    note = coverage_note(deep_sample_size=28, universe_row_count=0)
    assert note.claim == DIGITAL_VA_COVERAGE_CLAIM
    assert note.claim == "prototype_listed_sample"
    assert note.universe_row_count == 0
    assert "national" in note.detail.lower() or "Section C" in note.detail


def test_seed_companies_still_deep_sample_not_universe():
    """Sanity: seed allowlist remains the deep sample; universe stays empty."""
    seed = json.loads(
        (REPO_ROOT / "data" / "seeds" / "companies.json").read_text(encoding="utf-8")
    )
    assert isinstance(seed, list)
    assert 20 <= len(seed) <= 40
    assert load_universe_rows() == []
    # Must not scale by copying seed into universe.
    assert all("stock_code" in c for c in seed)
