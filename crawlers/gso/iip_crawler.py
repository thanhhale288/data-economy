"""GSO/NSO macro crawler (VSIC Section C).

- IIP: monthly NSDP SDMX (`nsdp.nso.gov.vn`), series by INDICATOR key.
- Shipment / inventory: annual PX-Web (`pxweb.nso.gov.vn` E07.03 / E07.04),
  step-held to monthly via `pxweb_client` (same policy as OECD INDIGO).

Sourced fallbacks only when live fetches fail — never random values.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import httpx
import xmltodict
from sqlalchemy.orm import Session

from backend.app.models import GsoMacro

logger = logging.getLogger(__name__)

# Official NSDP endpoints (preferred order).
# Host renamed GSO → NSO: nsdp.nso.gov.vn (nsdp.gso.gov.vn no longer resolves usefully).
GSO_IIP_URLS: tuple[str, ...] = (
    "https://nsdp.nso.gov.vn/GSO-chung/SDMXFiles/GSO/IIPVNM.xml",
    "http://nsdp.nso.gov.vn/GSO-chung/SDMXFiles/GSO/IIPVNM.xml",
    # Internet Archive snapshot of the former official file (failover).
    "https://web.archive.org/web/20230325152851id_/"
    "https://nsdp.gso.gov.vn/GSO-chung/SDMXFiles/GSO/IIPVNM.xml",
)

# Map SDMX INDICATOR concept id → (vsic_code, indicator_code, indicator_name).
# AIP_ISIC4_C_IX = Manufacturing / chế biến chế tạo (ISIC/VSIC Section C).
INDICATOR_BY_SDMX_KEY: dict[str, tuple[str, str, str]] = {
    "AIP_ISIC4_C_IX": (
        "C",
        "IIP_C",
        "Chỉ số SXCN - Chế biến chế tạo",
    ),
}

# Target Section C series this crawler is responsible for.
TARGET_INDICATOR_CODES: frozenset[str] = frozenset(
    {"IIP_C", "SHIPMENT_C", "INVENTORY_C"}
)

FALLBACK_CSV = (
    Path(__file__).resolve().parents[2] / "data" / "raw" / "gso_iip_fallback.csv"
)
FALLBACK_SOURCE = "GSO_FALLBACK"
LIVE_SOURCE = "GSO"

HTTP_TIMEOUT = 30.0


@dataclass
class ParseResult:
    """Outcome of parsing an SDMX StructureSpecificData document."""

    records: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    series_found: list[str] = field(default_factory=list)
    series_unmapped: list[str] = field(default_factory=list)


@dataclass
class FetchResult:
    """Top-level fetch outcome with explicit failure classification."""

    records: list[dict[str, Any]]
    status: str
    detail: str
    source_url: str | None = None
    parse: ParseResult | None = None

    @property
    def used_fallback(self) -> bool:
        return self.status == "fallback"


class GsoNetworkError(Exception):
    """Transport / connection failure talking to GSO."""


class GsoHttpError(Exception):
    """Non-success HTTP response from GSO."""

    def __init__(self, status_code: int, url: str, body_preview: str = "") -> None:
        self.status_code = status_code
        self.url = url
        self.body_preview = body_preview
        super().__init__(f"HTTP {status_code} from {url}")


class GsoParseError(Exception):
    """SDMX XML could not be parsed into series/observations."""


class GsoEmptySeriesError(Exception):
    """Parsed successfully but no mapped Section C observations were found."""


def _attr(node: dict[str, Any], name: str, default: str = "") -> str:
    """Read an XML attribute whether xmltodict kept the @ prefix or not."""
    if name in node and node[name] is not None:
        return str(node[name])
    at_name = f"@{name}"
    if at_name in node and node[at_name] is not None:
        return str(node[at_name])
    return default


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _find_dataset_series(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """Locate Series nodes under StructureSpecificData / DataSet."""
    root = parsed.get("message:StructureSpecificData") or parsed.get(
        "StructureSpecificData"
    )
    if not isinstance(root, dict):
        raise GsoParseError("Missing message:StructureSpecificData root")

    dataset = root.get("message:DataSet") or root.get("DataSet")
    if not isinstance(dataset, dict):
        raise GsoParseError("Missing message:DataSet")

    series = dataset.get("Series")
    if series is None:
        raise GsoParseError("DataSet contains no Series")
    return [s for s in _as_list(series) if isinstance(s, dict)]


def _parse_period(period_str: str) -> date | None:
    text = (period_str or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            dt = datetime.strptime(text, fmt)
            return date(dt.year, dt.month, 1)
        except ValueError:
            continue
    return None


def _parse_obs_value(value_str: str) -> float | None:
    text = (value_str or "").strip()
    if not text or text.upper() in {"NA", "N/A", "NULL", ".", ".."}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_sdmx_series(xml_text: str) -> ParseResult:
    """Parse GSO StructureSpecificData SDMX XML into GsoMacro-ready records.

    Identifies series via the INDICATOR dimension (e.g. AIP_ISIC4_C_IX).
    Skips missing/invalid observations with reasons; does not raise on bad obs.
    """
    if not xml_text or not xml_text.strip():
        raise GsoParseError("Empty SDMX document")

    try:
        parsed = xmltodict.parse(xml_text)
    except Exception as exc:  # xmltodict / expat errors
        raise GsoParseError(f"XML parse failed: {exc}") from exc

    result = ParseResult()
    try:
        series_list = _find_dataset_series(parsed)
    except GsoParseError:
        raise
    except Exception as exc:
        raise GsoParseError(f"Unexpected SDMX structure: {exc}") from exc

    for series in series_list:
        indicator_key = _attr(series, "INDICATOR")
        result.series_found.append(indicator_key or "<missing>")
        mapping = INDICATOR_BY_SDMX_KEY.get(indicator_key)
        if not mapping:
            if indicator_key:
                result.series_unmapped.append(indicator_key)
            else:
                result.skipped.append("series_missing_INDICATOR")
            continue

        vsic_code, indicator_code, indicator_name = mapping
        base_per = _attr(series, "BASE_PER") or "2015"
        unit = f"index_{base_per}=100"
        observations = _as_list(series.get("Obs"))

        if not observations:
            result.skipped.append(f"empty_observations:{indicator_key}")
            continue

        for obs in observations:
            if not isinstance(obs, dict):
                result.skipped.append(f"non_dict_obs:{indicator_key}")
                continue
            period_str = _attr(obs, "TIME_PERIOD")
            value_str = _attr(obs, "OBS_VALUE")
            if not period_str:
                result.skipped.append(f"missing_TIME_PERIOD:{indicator_key}")
                continue
            period = _parse_period(period_str)
            if period is None:
                result.skipped.append(
                    f"invalid_TIME_PERIOD:{indicator_key}:{period_str}"
                )
                continue
            if not value_str:
                result.skipped.append(
                    f"missing_OBS_VALUE:{indicator_key}:{period_str}"
                )
                continue
            value = _parse_obs_value(value_str)
            if value is None:
                result.skipped.append(
                    f"invalid_OBS_VALUE:{indicator_key}:{period_str}:{value_str}"
                )
                continue

            result.records.append(
                {
                    "vsic_code": vsic_code,
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "period": period,
                    "value": value,
                    "unit": unit,
                    "source": LIVE_SOURCE,
                }
            )

    return result


def load_fallback_records(path: Path | None = None) -> list[dict[str, Any]]:
    """Load deterministic, sourced fallback rows from CSV (no random values)."""
    csv_path = path or FALLBACK_CSV
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"Fallback fixture missing: {csv_path}. "
            "Expected a committed CSV under data/raw/ with documented provenance."
        )

    records: list[dict[str, Any]] = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        # Skip provenance comment lines (# ...)
        lines = [ln for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]
    reader = csv.DictReader(lines)
    for row in reader:
        period = _parse_period(row.get("period", ""))
        value = _parse_obs_value(row.get("value", ""))
        if period is None or value is None:
            continue
        records.append(
            {
                "vsic_code": row.get("vsic_code", "C").strip(),
                "indicator_code": row["indicator_code"].strip(),
                "indicator_name": row.get(
                    "indicator_name", "Chỉ số SXCN - Chế biến chế tạo"
                ).strip(),
                "period": period,
                "value": value,
                "unit": (row.get("unit") or "index_2015=100").strip(),
                "source": (row.get("source") or FALLBACK_SOURCE).strip(),
            }
        )
    if not records:
        raise GsoEmptySeriesError(f"Fallback CSV produced no records: {csv_path}")
    return records


def _download_xml(url: str, client: httpx.Client) -> str:
    try:
        response = client.get(url)
    except httpx.TimeoutException as exc:
        raise GsoNetworkError(f"Timeout fetching {url}: {exc}") from exc
    except httpx.TransportError as exc:
        raise GsoNetworkError(f"Network error fetching {url}: {exc}") from exc

    if response.status_code != 200:
        raise GsoHttpError(
            response.status_code,
            str(response.url),
            body_preview=response.text[:200],
        )
    text = response.text
    if not text.strip():
        raise GsoEmptySeriesError(f"Empty body from {url}")
    return text


def _unavailable_targets(records: list[dict[str, Any]]) -> list[str]:
    present = {r["indicator_code"] for r in records}
    return sorted(TARGET_INDICATOR_CODES - present)


def fetch_gso_iip(
    *,
    urls: tuple[str, ...] | None = None,
    client: httpx.Client | None = None,
    use_fallback: bool = True,
) -> FetchResult:
    """Fetch and parse GSO IIP SDMX; fall back to sourced CSV on failure.

    Failure modes are distinguished (network / HTTP / parse / empty) and always
    recorded on the returned FetchResult — never swallowed silently.
    """
    candidate_urls = urls or GSO_IIP_URLS
    errors: list[str] = []
    owns_client = client is None
    http_client = client or httpx.Client(
        timeout=HTTP_TIMEOUT, follow_redirects=True
    )

    try:
        for url in candidate_urls:
            try:
                logger.info("Fetching GSO SDMX from %s", url)
                xml_text = _download_xml(url, http_client)
                parse = parse_sdmx_series(xml_text)
                if not parse.records:
                    raise GsoEmptySeriesError(
                        "No mapped Section C observations "
                        f"(found={parse.series_found}, unmapped={parse.series_unmapped})"
                    )
                missing = _unavailable_targets(parse.records)
                detail = (
                    f"Parsed {len(parse.records)} records from {url}; "
                    f"skipped={len(parse.skipped)}"
                )
                if missing:
                    detail += f"; series_unavailable={missing}"
                    # Shipment/inventory live in PX-Web, not this SDMX file — expected.
                    if set(missing) <= {"SHIPMENT_C", "INVENTORY_C"}:
                        logger.info(
                            "SDMX IIP omits %s (fetched separately via PX-Web)",
                            missing,
                        )
                    else:
                        logger.warning(
                            "GSO SDMX missing target series %s",
                            missing,
                        )
                logger.info(detail)
                return FetchResult(
                    records=parse.records,
                    status="ok",
                    detail=detail,
                    source_url=url,
                    parse=parse,
                )
            except GsoNetworkError as exc:
                msg = f"network_error:{url}:{exc}"
                logger.warning(msg)
                errors.append(msg)
            except GsoHttpError as exc:
                msg = f"http_error:{exc.status_code}:{url}:{exc.body_preview!r}"
                logger.warning(msg)
                errors.append(msg)
            except GsoParseError as exc:
                msg = f"parse_error:{url}:{exc}"
                logger.error(msg)
                errors.append(msg)
            except GsoEmptySeriesError as exc:
                msg = f"empty_or_unavailable:{url}:{exc}"
                logger.warning(msg)
                errors.append(msg)
    finally:
        if owns_client:
            http_client.close()

    failure_summary = " | ".join(errors) if errors else "no_urls_attempted"
    if not use_fallback:
        return FetchResult(
            records=[],
            status="error",
            detail=failure_summary,
            source_url=None,
        )

    logger.warning(
        "All live GSO fetches failed (%s); loading deterministic fallback %s",
        failure_summary,
        FALLBACK_CSV,
    )
    try:
        records = load_fallback_records()
    except (OSError, GsoEmptySeriesError) as exc:
        logger.error("Fallback load failed: %s", exc)
        return FetchResult(
            records=[],
            status="error",
            detail=f"{failure_summary} | fallback_error:{exc}",
            source_url=str(FALLBACK_CSV),
        )

    missing = _unavailable_targets(records)
    detail = (
        f"fallback_after: {failure_summary}; "
        f"loaded {len(records)} records from {FALLBACK_CSV}"
    )
    if missing:
        detail += f"; series_unavailable={missing}"
    return FetchResult(
        records=records,
        status="fallback",
        detail=detail,
        source_url=str(FALLBACK_CSV),
    )


def save_gso_records(db: Session, records: list[dict[str, Any]]) -> int:
    """Upsert GsoMacro rows on (vsic_code, indicator_code, period). Idempotent."""
    inserted = 0
    for r in records:
        existing = (
            db.query(GsoMacro)
            .filter(
                GsoMacro.vsic_code == r["vsic_code"],
                GsoMacro.indicator_code == r["indicator_code"],
                GsoMacro.period == r["period"],
            )
            .first()
        )
        if existing:
            existing.value = r["value"]
            existing.unit = r.get("unit", existing.unit)
            existing.indicator_name = r.get("indicator_name", existing.indicator_name)
            existing.source = r.get("source", existing.source)
        else:
            payload = {
                "vsic_code": r["vsic_code"],
                "indicator_code": r["indicator_code"],
                "indicator_name": r["indicator_name"],
                "period": r["period"],
                "value": r["value"],
                "unit": r.get("unit", "index"),
                "source": r.get("source", LIVE_SOURCE),
            }
            db.add(GsoMacro(**payload))
            inserted += 1
    db.commit()
    return inserted


def fetch_gso_macro(
    *,
    urls: tuple[str, ...] | None = None,
    client: httpx.Client | None = None,
    use_fallback: bool = True,
) -> FetchResult:
    """Fetch IIP (SDMX) + shipment/inventory (PX-Web) for Section C."""
    from crawlers.gso.pxweb_client import fetch_pxweb_section_c

    owns = client is None
    http = client or httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True)
    try:
        iip = fetch_gso_iip(urls=urls, client=http, use_fallback=use_fallback)
        px = fetch_pxweb_section_c(client=http, use_fallback=use_fallback)

        # IIP-only SDMX naturally lacks shipment/inventory — drop that noise once PX-Web runs.
        iip_detail = iip.detail
        if "series_unavailable=" in iip_detail:
            iip_detail = iip_detail.split("; series_unavailable=")[0]

        records = list(iip.records) + list(px.records)
        missing = _unavailable_targets(records)
        parts = [f"iip:{iip.status}:{iip_detail}", f"pxweb:{px.status}:{px.detail}"]
        if missing:
            parts.append(f"series_unavailable={missing}")
        detail = " | ".join(parts)

        if not records:
            status = "error"
        elif iip.status == "error" and px.status == "error":
            status = "error"
        elif iip.status == "fallback" or px.status == "fallback":
            status = "fallback"
        else:
            status = "ok"

        source_url = iip.source_url
        if px.source_urls:
            source_url = f"{source_url or ''};{','.join(px.source_urls)}"

        return FetchResult(
            records=records,
            status=status,
            detail=detail,
            source_url=source_url,
            parse=iip.parse,
        )
    finally:
        if owns:
            http.close()


def run_gso_crawl(db: Session) -> int:
    """Fetch GSO/NSO macro series and persist them. Returns rows inserted (not updates)."""
    result = fetch_gso_macro()
    logger.info("GSO crawl status=%s detail=%s", result.status, result.detail)
    if not result.records:
        logger.error("GSO crawl produced no records: %s", result.detail)
        return 0
    return save_gso_records(db, result.records)
