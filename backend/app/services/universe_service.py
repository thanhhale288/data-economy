"""Company-universe helpers — shallow tier only (ADR-0003).

Loads zero invented firms. Promotion into the deep listed sample is gated:
callers must use onboard + seed, never auto-enrich BCTC/marketplace.
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.schemas.universe import (
    DIGITAL_VA_COVERAGE_CLAIM,
    PERCENTILE_COVERAGE_CLAIM,
    MetricCoverageLabel,
    UniverseCoverageNote,
    UniverseFirmShallow,
    UniverseIngestStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
UNIVERSE_DIR = REPO_ROOT / "data" / "raw" / "company_universe"
UNIVERSE_ROWS_PATH = UNIVERSE_DIR / "rows.json"


def universe_rows_path() -> Path:
    return UNIVERSE_ROWS_PATH


def load_universe_rows(path: Path | None = None) -> list[UniverseFirmShallow]:
    """Load shallow universe rows from JSON. Empty list is the current truth."""
    target = path or UNIVERSE_ROWS_PATH
    if not target.exists():
        return []
    raw = json.loads(target.read_text(encoding="utf-8"))
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("company_universe rows.json must be a JSON array")
    return [UniverseFirmShallow.model_validate(item) for item in raw]


def coverage_note(
    *,
    deep_sample_size: int,
    universe_row_count: int | None = None,
) -> UniverseCoverageNote:
    """Honesty note for Digital VA / percentile surfaces."""
    n_universe = (
        universe_row_count
        if universe_row_count is not None
        else len(load_universe_rows())
    )
    return UniverseCoverageNote(
        coverage_label=MetricCoverageLabel.PROTOTYPE_ESTIMATE,
        deep_sample_size=deep_sample_size,
        universe_row_count=n_universe,
        claim=DIGITAL_VA_COVERAGE_CLAIM,
        detail=(
            f"Digital VA and peer percentiles cover the listed deep sample "
            f"(n={deep_sample_size}), not national Section C. "
            f"Shallow universe rows loaded={n_universe}. "
            f"Percentile claim={PERCENTILE_COVERAGE_CLAIM}."
        ),
    )


def get_coverage_note(db) -> UniverseCoverageNote:
    """Build coverage note from DB deep-sample count + stub universe rows.

    ``companies`` row count is the listed deep sample only — never Section C
    national coverage (ADR-0003).
    """
    from backend.app.models import Company

    deep_n = db.query(Company).count()
    return coverage_note(deep_sample_size=deep_n)


def can_auto_promote_to_deep_sample(row: UniverseFirmShallow) -> bool:
    """Always False — promotion is explicit onboard only (ADR-0003)."""
    _ = row
    return False


def promotion_blocked_reason(row: UniverseFirmShallow) -> str:
    if row.ingest_status == UniverseIngestStatus.PROMOTED:
        return "already_marked_promoted_but_deep_sample_requires_onboard_script"
    return "auto_promote_forbidden_use_onboard_company"
