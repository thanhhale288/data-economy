"""Shallow company-universe contract (Task #39 scale architecture).

Not the deep listed sample (`companies` / seed allowlist). Rows here must not
enter Digital VA, CafeF enrich, or marketplace crawl until explicitly promoted
via onboard. See ADR-0003.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UniverseSourceType(StrEnum):
    """Candidate source kinds — none are wired as national ingest yet."""

    BUSINESS_REGISTRATION = "business_registration"
    GSO_ENTERPRISE_STATS = "gso_enterprise_stats"
    EXCHANGE_LISTED = "exchange_listed"
    MANUAL_CURATED = "manual_curated"
    UNKNOWN = "unknown"


class UniverseIngestStatus(StrEnum):
    """Per-row / per-batch status for future queue workers."""

    PENDING = "pending"
    FETCHED = "fetched"
    VERIFIED = "verified"
    REJECTED = "rejected"
    PROMOTED = "promoted"


class MetricCoverageLabel(StrEnum):
    """Honesty labels for aggregates — do not mix tiers silently."""

    OFFICIAL_MACRO = "official_macro"
    UNIVERSE_COVERAGE = "universe_coverage"
    LISTED_SAMPLE = "listed_sample"
    DEEP_SAMPLE = "deep_sample"
    PROTOTYPE_ESTIMATE = "prototype_estimate"


class UniverseProvenance(BaseModel):
    """Row-level provenance required for any future shallow ingest."""

    model_config = ConfigDict(extra="forbid")

    source_type: UniverseSourceType = UniverseSourceType.UNKNOWN
    source_dataset: str | None = None
    source_url: str | None = None
    source_record_id: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime | None = None
    vsic_evidence: str | None = Field(
        default=None,
        description="How VSIC was assigned (table cell, mapping note, …)",
    )
    notes: str | None = None


class UniverseFirmShallow(BaseModel):
    """Minimal firm identity for Section C universe — no BCTC / digital FKs."""

    model_config = ConfigDict(extra="forbid")

    universe_id: str = Field(..., min_length=1, description="Stable id within source")
    legal_name: str = Field(..., min_length=1)
    vsic_code: str | None = Field(
        default=None,
        description="VSIC Section C code when known; null if source lacks industry",
    )
    stock_code: str | None = Field(
        default=None,
        description="Exchange ticker when listed; null for unlisted firms",
    )
    website_url: str | None = None
    province: str | None = None
    active: bool | None = None
    ingest_status: UniverseIngestStatus = UniverseIngestStatus.PENDING
    provenance: UniverseProvenance = Field(default_factory=UniverseProvenance)

    @field_validator("vsic_code")
    @classmethod
    def _vsic_looks_section_c(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        code = value.strip()
        # Section C divisions are 10–33; accept 2–4 digit codes in that range.
        if not code.isdigit():
            raise ValueError("vsic_code must be numeric when set")
        div = int(code[:2]) if len(code) >= 2 else int(code)
        if div < 10 or div > 33:
            raise ValueError("vsic_code must be VSIC Section C (divisions 10–33)")
        return code


class UniverseBatchManifest(BaseModel):
    """Batch / queue manifest for future rate-limited shallow ingest."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str
    source_type: UniverseSourceType
    created_at: datetime
    rate_limit_per_host_seconds: float = Field(
        default=1.5,
        ge=0.0,
        description="Minimum interval between HTTP calls to the same host",
    )
    max_rows: int | None = Field(
        default=None,
        description="Cap for a batch run; None = unspecified (still no invent)",
    )
    cursor: str | None = None
    status: UniverseIngestStatus = UniverseIngestStatus.PENDING
    row_ids: list[str] = Field(default_factory=list)
    provenance_notes: str | None = None


class UniverseCoverageNote(BaseModel):
    """API/docs helper: never claim national coverage from deep-sample metrics."""

    model_config = ConfigDict(extra="forbid")

    coverage_label: MetricCoverageLabel
    deep_sample_size: int
    universe_row_count: int
    claim: Literal[
        "prototype_listed_sample",
        "universe_shallow_only",
        "official_macro",
        "insufficient_data",
    ]
    detail: str


DIGITAL_VA_COVERAGE_CLAIM = "prototype_listed_sample"
PERCENTILE_COVERAGE_CLAIM = "prototype_listed_sample"
