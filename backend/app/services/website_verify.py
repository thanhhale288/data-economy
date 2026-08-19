"""Website verification honesty — stored provenance, not live HTTP.

Task #40 audit (2026-07-27): 27/28 official websites fetched OK with SSL
verify ON. GEE ``https://gelex-electric.com`` failed certificate issuer
(``CERTIFICATE_VERIFY_FAILED``). Checkout on that fetch stayed unknown;
seed ``has_checkout=false`` is a storage default, not “no ecommerce”.

This module never invents HTTP status codes and never disables SSL verify.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

WEBSITE_VERIFY_OK = "ok"
WEBSITE_VERIFY_FAIL = "fail"
WEBSITE_VERIFY_UNKNOWN = "unknown"
VALID_STATUSES = frozenset(
    {WEBSITE_VERIFY_OK, WEBSITE_VERIFY_FAIL, WEBSITE_VERIFY_UNKNOWN}
)

# Documented Task #40 audit — not a live probe, not an HTTP 500.
_TASK40_GEE_URL = "https://gelex-electric.com"
_TASK40_AUDIT: dict[str, dict[str, str]] = {
    "GEE": {
        "status": WEBSITE_VERIFY_FAIL,
        "reason": "ssl_unverified",
        "source": "epic3_task40_audit",
        "url": _TASK40_GEE_URL,
    }
}

FAIL_NOTE = (
    "Website URL chưa verify được (ssl_unverified; audit Task #40). "
    "Không suy TMĐT hay checkout từ fail."
)
UNKNOWN_NOTE = (
    "Website URL chưa được đo (unknown; không có fetch xác minh). "
    "Không suy TMĐT hay checkout."
)


@dataclass(frozen=True)
class WebsiteVerify:
    """Optional honesty record for a company website URL."""

    status: str | None = None
    reason: str | None = None
    source: str | None = None

    @property
    def shows_chip(self) -> bool:
        return self.status in {WEBSITE_VERIFY_FAIL, WEBSITE_VERIFY_UNKNOWN}


def normalize_website_url(url: str | None) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = (parsed.netloc or parsed.path).lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    return f"{host}{path}"


def _as_status(value: Any) -> str | None:
    if value is None:
        return None
    status = str(value).strip().lower()
    return status if status in VALID_STATUSES else None


def _as_reason(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def extract_stored_website_verify(digital_channels: dict | None) -> WebsiteVerify:
    """Read nested ``digital_channels.website_verify`` seed provenance."""
    if not isinstance(digital_channels, dict):
        return WebsiteVerify()
    nested = digital_channels.get("website_verify")
    if not isinstance(nested, dict):
        # Also accept sibling string keys if a seed stored them flat.
        status = _as_status(digital_channels.get("website_verify_status"))
        reason = _as_reason(digital_channels.get("website_verify_reason"))
        if status:
            return WebsiteVerify(status=status, reason=reason, source="seed")
        return WebsiteVerify()
    return WebsiteVerify(
        status=_as_status(nested.get("status")),
        reason=_as_reason(nested.get("reason")),
        source=_as_reason(nested.get("source")) or "seed",
    )


def merge_website_verify_into_channels(seed_row: dict) -> dict | None:
    """Persist top-level seed verify fields into ``digital_channels`` JSON."""
    channels = dict(seed_row.get("digital_channels") or {})
    stored = extract_stored_website_verify(channels)
    status = _as_status(seed_row.get("website_verify_status")) or stored.status
    reason = _as_reason(seed_row.get("website_verify_reason")) or stored.reason
    top_nested = seed_row.get("website_verify")
    source = stored.source
    if isinstance(top_nested, dict):
        status = _as_status(top_nested.get("status")) or status
        reason = _as_reason(top_nested.get("reason")) or reason
        source = _as_reason(top_nested.get("source")) or source
    if status:
        payload: dict[str, str] = {
            "status": status,
            "source": source or "epic3_task40_audit",
        }
        if reason:
            payload["reason"] = reason
        channels["website_verify"] = payload
    return channels or None


def resolve_website_verify(
    *,
    stock_code: str | None = None,
    website_url: str | None = None,
    digital_channels: dict | None = None,
) -> WebsiteVerify:
    """Derive fail/ok/unknown from stored provenance, then documented audit.

    Missing provenance on an OK ticker is not fail — no invented HTTP.
    """
    stored = extract_stored_website_verify(digital_channels)
    if stored.status:
        return stored

    code = (stock_code or "").strip().upper()
    documented = _TASK40_AUDIT.get(code)
    if documented:
        expected = normalize_website_url(documented.get("url"))
        actual = normalize_website_url(website_url)
        if not actual or actual == expected:
            return WebsiteVerify(
                status=documented["status"],
                reason=documented.get("reason"),
                source=documented.get("source"),
            )

    return WebsiteVerify()
