"""NSO PX-Web client for manufacturing shipment and inventory indices.

Official tables (host renamed gso.gov.vn → nso.gov.vn):
- E07.03.px — Index of industrial shipment of manufacturing (annual)
- E07.04.px — Index of industrial inventory as of 31 Dec (annual)

API root: https://pxweb.nso.gov.vn/api/v1/en/Industry

These series are published annually only (not monthly). We step-hold each annual
value across Jan–Dec so they join monthly IIP_C without inventing intra-year
dynamics (same policy as OECD INDIGO).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PXWEB_API_BASE = "https://pxweb.nso.gov.vn/api/v1/en/Industry"
WHOLE_MANUFACTURING_CODE = "0"  # Section C aggregate in these tables
REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"

LIVE_SOURCE = "GSO"
FALLBACK_SOURCE = "GSO_FALLBACK"
HTTP_TIMEOUT = 45.0

# Table specs: PX-Web id → our indicator mapping + offline fixture.
PXWEB_TABLES: dict[str, dict[str, str]] = {
    "E07.03.px": {
        "indicator_code": "SHIPMENT_C",
        "indicator_name": "Chỉ số tiêu thụ CN chế biến chế tạo",
        "fallback_fixture": "gso_pxweb_shipment_fallback.json",
        "unit": "index_prev_year=100",
    },
    "E07.04.px": {
        "indicator_code": "INVENTORY_C",
        "indicator_name": "Chỉ số tồn kho CN chế biến chế tạo (31/12)",
        "fallback_fixture": "gso_pxweb_inventory_fallback.json",
        "unit": "index_prev_year=100",
    },
}


class PxwebError(Exception):
    """Base PX-Web error."""


class PxwebNetworkError(PxwebError):
    pass


class PxwebHttpError(PxwebError):
    def __init__(self, status_code: int, url: str, body_preview: str = "") -> None:
        self.status_code = status_code
        self.url = url
        self.body_preview = body_preview
        super().__init__(f"HTTP {status_code} from {url}")


class PxwebParseError(PxwebError):
    pass


@dataclass
class PxwebFetchResult:
    records: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # ok | fallback | error
    detail: str = ""
    source_urls: list[str] = field(default_factory=list)


def _parse_year_label(label: str) -> int | None:
    """Extract calendar year from PX valueTexts like '2023' or 'Prel. 2024'."""
    text = (label or "").strip()
    match = re.search(r"(20\d{2}|19\d{2})", text)
    if not match:
        return None
    return int(match.group(1))


def _parse_obs_value(raw: str) -> float | None:
    text = (raw or "").strip().replace(",", "")
    if not text or text in {".", "..", "-", "…", "NA", "N/A"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def expand_annual_to_monthly_step(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Step-hold annual rows to 12 monthly periods (Jan–Dec)."""
    out: list[dict[str, Any]] = []
    for record in records:
        year = record["period"].year
        for month in range(1, 13):
            row = dict(record)
            row["period"] = date(year, month, 1)
            out.append(row)
    return out


def build_year_map(meta: dict[str, Any]) -> dict[str, int]:
    """Map PX Year dimension codes → calendar years from valueTexts."""
    variables = meta.get("variables") or []
    year_var = next((v for v in variables if v.get("code") == "Year"), None)
    if not year_var:
        raise PxwebParseError("PX-Web metadata missing Year variable")
    mapping: dict[str, int] = {}
    for code, label in zip(year_var.get("values") or [], year_var.get("valueTexts") or []):
        year = _parse_year_label(str(label))
        if year is not None:
            mapping[str(code)] = year
    if not mapping:
        raise PxwebParseError("Could not parse any Year labels from PX-Web metadata")
    return mapping


def parse_pxweb_table(
    meta: dict[str, Any],
    data_payload: dict[str, Any],
    *,
    indicator_code: str,
    indicator_name: str,
    unit: str,
    source: str = LIVE_SOURCE,
    activity_code: str = WHOLE_MANUFACTURING_CODE,
    step_hold_monthly: bool = True,
) -> list[dict[str, Any]]:
    """Parse a PX-Web JSON-stat-like response into GsoMacro-ready records."""
    year_map = build_year_map(meta)
    rows = data_payload.get("data") or []
    annual: list[dict[str, Any]] = []
    skipped = 0

    for row in rows:
        if not isinstance(row, dict):
            skipped += 1
            continue
        key = row.get("key") or []
        values = row.get("values") or []
        if len(key) < 2 or not values:
            skipped += 1
            continue
        act_code, year_code = str(key[0]), str(key[1])
        if act_code != activity_code:
            continue
        year = year_map.get(year_code)
        if year is None:
            skipped += 1
            continue
        value = _parse_obs_value(str(values[0]))
        if value is None:
            skipped += 1
            continue
        annual.append(
            {
                "vsic_code": "C",
                "indicator_code": indicator_code,
                "indicator_name": indicator_name,
                "period": date(year, 1, 1),
                "value": value,
                "unit": unit,
                "source": source,
            }
        )

    if not annual:
        raise PxwebParseError(
            f"No usable observations for {indicator_code} "
            f"(activity={activity_code}, skipped={skipped})"
        )

    annual.sort(key=lambda r: r["period"])
    if step_hold_monthly:
        return expand_annual_to_monthly_step(annual)
    return annual


def _pxweb_query_body() -> dict[str, Any]:
    return {
        "query": [
            {
                "code": "Industrial activity",
                "selection": {"filter": "item", "values": [WHOLE_MANUFACTURING_CODE]},
            },
            {
                "code": "Year",
                "selection": {"filter": "all", "values": ["*"]},
            },
        ],
        "response": {"format": "json"},
    }


def _get_json(client: httpx.Client, url: str) -> dict[str, Any]:
    try:
        response = client.get(url)
    except httpx.TimeoutException as exc:
        raise PxwebNetworkError(f"Timeout GET {url}: {exc}") from exc
    except httpx.TransportError as exc:
        raise PxwebNetworkError(f"Network error GET {url}: {exc}") from exc
    if response.status_code != 200:
        raise PxwebHttpError(response.status_code, url, response.text[:200])
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise PxwebParseError(f"Non-JSON GET response from {url}: {exc}") from exc


def _post_json(client: httpx.Client, url: str, body: dict[str, Any]) -> dict[str, Any]:
    try:
        response = client.post(url, json=body)
    except httpx.TimeoutException as exc:
        raise PxwebNetworkError(f"Timeout POST {url}: {exc}") from exc
    except httpx.TransportError as exc:
        raise PxwebNetworkError(f"Network error POST {url}: {exc}") from exc
    if response.status_code != 200:
        raise PxwebHttpError(response.status_code, url, response.text[:200])
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise PxwebParseError(f"Non-JSON POST response from {url}: {exc}") from exc


def load_pxweb_fallback(table_id: str) -> list[dict[str, Any]]:
    """Load sourced offline fixture for one PX-Web table."""
    spec = PXWEB_TABLES[table_id]
    path = RAW_DIR / spec["fallback_fixture"]
    if not path.is_file():
        raise FileNotFoundError(path)
    wrapper = json.loads(path.read_text(encoding="utf-8"))
    meta = wrapper.get("meta") or {}
    # Fixtures store variables under meta; rebuild shape expected by parser.
    meta_for_parse = {"variables": meta.get("variables") or [], "title": meta.get("title")}
    data_payload = wrapper.get("data") or {}
    return parse_pxweb_table(
        meta_for_parse,
        data_payload,
        indicator_code=spec["indicator_code"],
        indicator_name=spec["indicator_name"],
        unit=spec["unit"],
        source=FALLBACK_SOURCE,
    )


def fetch_pxweb_table(
    table_id: str,
    *,
    client: httpx.Client | None = None,
    use_fallback: bool = True,
    api_base: str = PXWEB_API_BASE,
) -> PxwebFetchResult:
    """Fetch one PX-Web table (shipment or inventory) for whole manufacturing."""
    if table_id not in PXWEB_TABLES:
        raise ValueError(f"Unknown PX-Web table_id: {table_id}")
    spec = PXWEB_TABLES[table_id]
    url = f"{api_base.rstrip('/')}/{table_id}"
    owns = client is None
    http = client or httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True)
    try:
        try:
            meta = _get_json(http, url)
            data_payload = _post_json(http, url, _pxweb_query_body())
            records = parse_pxweb_table(
                meta,
                data_payload,
                indicator_code=spec["indicator_code"],
                indicator_name=spec["indicator_name"],
                unit=spec["unit"],
                source=LIVE_SOURCE,
            )
            detail = (
                f"{spec['indicator_code']}:ok n={len(records)} from {url} "
                f"(annual→monthly step-hold)"
            )
            return PxwebFetchResult(
                records=records, status="ok", detail=detail, source_urls=[url]
            )
        except (PxwebNetworkError, PxwebHttpError, PxwebParseError) as exc:
            logger.warning("PX-Web %s failed: %s", table_id, exc)
            if not use_fallback:
                return PxwebFetchResult(
                    records=[],
                    status="error",
                    detail=f"{spec['indicator_code']}:error:{exc}",
                    source_urls=[url],
                )
            try:
                records = load_pxweb_fallback(table_id)
            except (OSError, PxwebParseError, FileNotFoundError) as fb_exc:
                return PxwebFetchResult(
                    records=[],
                    status="error",
                    detail=f"{spec['indicator_code']}:error:{exc}|fallback_failed:{fb_exc}",
                    source_urls=[url],
                )
            return PxwebFetchResult(
                records=records,
                status="fallback",
                detail=(
                    f"{spec['indicator_code']}:fallback after {exc}; "
                    f"n={len(records)} from {spec['fallback_fixture']}"
                ),
                source_urls=[url, str(RAW_DIR / spec["fallback_fixture"])],
            )
    finally:
        if owns:
            http.close()


def fetch_pxweb_section_c(
    *,
    client: httpx.Client | None = None,
    use_fallback: bool = True,
    api_base: str = PXWEB_API_BASE,
) -> PxwebFetchResult:
    """Fetch SHIPMENT_C + INVENTORY_C from NSO PX-Web."""
    owns = client is None
    http = client or httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True)
    combined = PxwebFetchResult()
    try:
        statuses: list[str] = []
        for table_id in PXWEB_TABLES:
            part = fetch_pxweb_table(
                table_id, client=http, use_fallback=use_fallback, api_base=api_base
            )
            combined.records.extend(part.records)
            combined.source_urls.extend(part.source_urls)
            statuses.append(part.detail)
            if part.status == "error":
                # Keep going for the other table; mark overall as partial/error later.
                pass
        if not combined.records:
            combined.status = "error"
        elif any("fallback" in s for s in statuses) and all(
            ":ok" in s or "fallback" in s for s in statuses
        ):
            combined.status = "fallback"
        elif any(":error" in s for s in statuses):
            combined.status = "ok" if combined.records else "error"
        else:
            combined.status = "ok"
        combined.detail = "; ".join(statuses)
        return combined
    finally:
        if owns:
            http.close()
