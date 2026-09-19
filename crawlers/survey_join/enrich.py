"""Plan next steps for survey MSTs not already in the cascade. No invented URLs."""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlparse

from crawlers.survey_join.join import (
    index_cascade,
    match_cascade,
    normalize_mst,
    normalize_ticker,
)

ACTION_CASCADE_SELF_REPORT = "cascade_self_report"
ACTION_NEEDS_URL_FINDER = "needs_url_finder"
ACTION_UNACTIONABLE = "unactionable"

_HTTP_SCHEMES = frozenset({"http", "https"})


def _self_report_http_url(raw: Any) -> str | None:
    """Return the stripped http(s) URL, or None. Never invent a host."""
    text = str(raw or "").strip()
    if not text:
        return None
    parsed = urlparse(text)
    if parsed.scheme.lower() not in _HTTP_SCHEMES:
        return None
    if not parsed.netloc:
        return None
    return text


def _normalize_frame_tax_codes(frame_tax_codes: Any) -> set[str]:
    if not frame_tax_codes:
        return set()
    out: set[str] = set()
    for raw in frame_tax_codes:
        mst = normalize_mst(raw)
        if mst:
            out.add(mst)
    return out


def _normalize_listed_map(
    listed_tax_to_ticker: Mapping[str, Any] | None,
) -> dict[str, str]:
    if not listed_tax_to_ticker:
        return {}
    out: dict[str, str] = {}
    for raw_mst, raw_ticker in listed_tax_to_ticker.items():
        mst = normalize_mst(raw_mst)
        ticker = normalize_ticker(raw_ticker)
        if mst and ticker:
            out[mst] = ticker
    return out


def _matches_cascade(
    *,
    mst: str,
    ticker: str,
    cascade_by_id: dict[str, dict[str, Any]],
    frame_tax_codes: set[str],
    listed_tax_to_ticker: Mapping[str, str] | None = None,
) -> bool:
    rec, _via = match_cascade(
        mst=mst,
        ticker=ticker,
        cascade_by_id=cascade_by_id,
        frame_tax_codes=frame_tax_codes,
        tax_id_to_ticker=dict(listed_tax_to_ticker) if listed_tax_to_ticker else None,
    )
    return rec is not None


def _tickers_to_try(survey_ticker: str, listed_ticker: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in (survey_ticker, listed_ticker, ""):
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _unactionable_reason(*, mst: str, company_name: str) -> str:
    missing: list[str] = []
    if not mst:
        missing.append("mst")
    if not company_name:
        missing.append("company_name")
    if not missing:
        missing.append("website_url_self_report")
    return "missing_fields: " + ", ".join(missing)


def plan_unmatched(
    survey_rows: list[dict[str, Any]],
    cascade_records: list[dict[str, Any]],
    *,
    frame_tax_codes: set[str] | None = None,
    listed_tax_to_ticker: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """For each unmatched survey row, emit a next-step plan — no fabricated URLs."""
    cascade_by_id = index_cascade(cascade_records)
    frame = _normalize_frame_tax_codes(frame_tax_codes)
    listed_map = _normalize_listed_map(listed_tax_to_ticker)
    plan: list[dict[str, Any]] = []

    for row in survey_rows:
        mst = normalize_mst(row.get("mst"))
        survey_ticker = normalize_ticker(row.get("ticker"))
        listed_ticker = listed_map.get(mst, "")
        company_name = str(row.get("company_name") or "").strip()
        self_report = _self_report_http_url(row.get("website_url_self_report"))

        matched = False
        for ticker in _tickers_to_try(survey_ticker, listed_ticker):
            if _matches_cascade(
                mst=mst,
                ticker=ticker,
                cascade_by_id=cascade_by_id,
                frame_tax_codes=frame,
                listed_tax_to_ticker=listed_map or None,
            ):
                matched = True
                break
        if matched:
            continue

        if self_report:
            plan.append(
                {
                    "mst": mst or None,
                    "company_name": company_name or None,
                    "ticker": survey_ticker or None,
                    "action": ACTION_CASCADE_SELF_REPORT,
                    "website_url": self_report,
                    "reason": None,
                }
            )
            continue
        if company_name and mst:
            plan.append(
                {
                    "mst": mst,
                    "company_name": company_name,
                    "ticker": survey_ticker or None,
                    "action": ACTION_NEEDS_URL_FINDER,
                    "website_url": None,
                    "reason": None,
                }
            )
            continue
        plan.append(
            {
                "mst": mst or None,
                "company_name": company_name or None,
                "ticker": survey_ticker or None,
                "action": ACTION_UNACTIONABLE,
                "website_url": None,
                "reason": _unactionable_reason(mst=mst, company_name=company_name),
            }
        )
    return plan


def cohort_from_self_report(plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Frame-url list for cascade ``--frame-urls`` from self-reported http(s) URLs only."""
    out: list[dict[str, Any]] = []
    for row in plan:
        if row.get("action") != ACTION_CASCADE_SELF_REPORT:
            continue
        mst = normalize_mst(row.get("mst"))
        url = _self_report_http_url(row.get("website_url"))
        if not mst or not url:
            continue
        out.append(
            {
                "firm_id": mst,
                "tax_code": mst,
                "website_url": url,
                "name": str(row.get("company_name") or "").strip(),
                "notes": "survey website_url_self_report",
            }
        )
    return out
