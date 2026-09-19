"""DT × % midpoint — only from survey revenue + bin. Never seed financials."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Midpoints apply only when revenue_vnd is a positive number and the bin is
# estimable. unknown / refuse / missing → skip (null estimate).
BIN_MIDPOINTS: dict[str, float] = {
    "zero": 0.0,
    "lt5": 0.025,
    "5to10": 0.075,
    "10to25": 0.175,
    "25to50": 0.375,
    "gt50": 0.75,
}

KNOWN_BINS = frozenset(BIN_MIDPOINTS) | frozenset({"unknown", "refuse"})
SKIP_BINS = frozenset({"unknown", "refuse"})

GT50_CAVEAT = (
    "gt50 midpoint 0.75 is wide (open interval above 50%); not a point estimate"
)


@dataclass(frozen=True)
class RevenueEstimate:
    bin_normalized: str | None
    midpoint: float | None
    estimated_online_revenue: float | None
    skipped_reason: str | None
    caveat: str | None


def normalize_bin(raw: Any) -> str:
    return str(raw or "").strip().lower()


def parse_revenue_vnd(raw: Any) -> tuple[float | None, str | None]:
    """Return (value, error_reason). error_reason is set when the cell is unusable."""
    if raw is None:
        return None, "missing_revenue"
    if isinstance(raw, bool):
        return None, "unparseable_revenue"
    if isinstance(raw, (int, float)):
        value = float(raw)
        if value != value:  # NaN
            return None, "unparseable_revenue"
        return value, None
    text = str(raw).strip()
    if not text:
        return None, "missing_revenue"
    try:
        value = float(text.replace("_", ""))
    except ValueError:
        return None, "unparseable_revenue"
    if value != value:
        return None, "unparseable_revenue"
    return value, None


def estimate_online_revenue(
    *,
    revenue_vnd: Any = None,
    online_revenue_share_bin: Any = None,
) -> RevenueEstimate:
    """Estimate online revenue as revenue × bin midpoint.

    Inputs are the survey cells only — no file I/O, no seed financials.
    """
    bin_norm = normalize_bin(online_revenue_share_bin)
    revenue, revenue_err = parse_revenue_vnd(revenue_vnd)

    if revenue_err:
        return RevenueEstimate(
            bin_normalized=bin_norm or None,
            midpoint=None,
            estimated_online_revenue=None,
            skipped_reason=revenue_err,
            caveat=None,
        )
    assert revenue is not None
    if revenue <= 0:
        return RevenueEstimate(
            bin_normalized=bin_norm or None,
            midpoint=None,
            estimated_online_revenue=None,
            skipped_reason="non_positive_revenue",
            caveat=None,
        )

    if not bin_norm:
        return RevenueEstimate(
            bin_normalized=None,
            midpoint=None,
            estimated_online_revenue=None,
            skipped_reason="bin_missing",
            caveat=None,
        )
    if bin_norm == "unknown":
        return RevenueEstimate(
            bin_normalized=bin_norm,
            midpoint=None,
            estimated_online_revenue=None,
            skipped_reason="bin_unknown",
            caveat=None,
        )
    if bin_norm == "refuse":
        return RevenueEstimate(
            bin_normalized=bin_norm,
            midpoint=None,
            estimated_online_revenue=None,
            skipped_reason="bin_refuse",
            caveat=None,
        )
    if bin_norm not in BIN_MIDPOINTS:
        return RevenueEstimate(
            bin_normalized=bin_norm,
            midpoint=None,
            estimated_online_revenue=None,
            skipped_reason="invalid_bin",
            caveat=None,
        )

    midpoint = BIN_MIDPOINTS[bin_norm]
    caveat = GT50_CAVEAT if bin_norm == "gt50" else None
    return RevenueEstimate(
        bin_normalized=bin_norm,
        midpoint=midpoint,
        estimated_online_revenue=revenue * midpoint,
        skipped_reason=None,
        caveat=caveat,
    )
