"""Records for one firm through the extraction cascade (tier1 rules + tier2 LLM).

Tier-2 field shapes match ``ml.local_llm.schema.ExtractionResult`` so T04/T05 share
one indicator vocabulary.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

CohortSource = Literal["listed28", "frame_pilot"]
TierId = Literal[1, 2]
ConflictKind = Literal["agree", "conflict", "abstain", "skip"]


@dataclass(frozen=True)
class EvidenceHit:
    kind: str
    detail: str


@dataclass
class Tier1Indicators:
    """Rule-layer indicators for one rendered page (always decided when fetch_ok)."""

    has_product_catalog: bool = False
    has_order_cart: bool = False
    payment_methods: list[str] = field(default_factory=list)
    social_links: list[dict[str, str]] = field(default_factory=list)
    marketplace_links: list[dict[str, str]] = field(default_factory=list)
    website_language: str | None = None
    evidence: list[EvidenceHit] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_product_catalog": self.has_product_catalog,
            "has_order_cart": self.has_order_cart,
            "payment_methods": list(self.payment_methods),
            "social_links": [dict(x) for x in self.social_links],
            "marketplace_links": [dict(x) for x in self.marketplace_links],
            "website_language": self.website_language,
            "evidence": [asdict(e) for e in self.evidence],
        }


@dataclass
class RenderedPage:
    url: str
    final_url: str
    ok: bool
    detail: str
    html: str = ""
    text: str = ""
    status_code: int | None = None


@dataclass
class ConflictRow:
    firm_id: str
    field: str
    kind: ConflictKind
    tier1_value: Any
    tier2_value: Any
    tier2_abstain: bool
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FirmCascadeResult:
    firm_id: str
    source_cohort: CohortSource
    website_url: str
    fetch_ok: bool
    fetch_detail: str
    tier1: Tier1Indicators | None
    tier2: dict[str, Any] | None
    tier2_decision: str | None
    conflicts: list[ConflictRow] = field(default_factory=list)
    model_id: str | None = None
    prompt_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "firm_id": self.firm_id,
            "source_cohort": self.source_cohort,
            "website_url": self.website_url,
            "fetch_ok": self.fetch_ok,
            "fetch_detail": self.fetch_detail,
            "tier1": self.tier1.to_dict() if self.tier1 else None,
            "tier2": self.tier2,
            "tier2_decision": self.tier2_decision,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
        }
