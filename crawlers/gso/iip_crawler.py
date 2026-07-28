"""GSO/NSO macro crawler (VSIC Section C).

- IIP: monthly NSDP SDMX (`nsdp.nso.gov.vn` IIPVNM.xml), series by INDICATOR key.
- Manufacturing VA: National Accounts SDMX (`GDPVNM.xml`) — quarterly preferred,
  step-held to monthly (no invented intra-period path).
- Shipment / inventory: annual PX-Web (`pxweb.nso.gov.vn` E07.03 / E07.04),
  step-held to monthly via `pxweb_client` (same policy as OECD INDIGO).

Province-by-industry GRDP remains deferred/NO-GO (Task #47 biên bản; no confirmed table ID).
Sourced fallbacks only when live fetches fail — never random values.
"""

from __future__ import annotations

import csv
import logging
import re
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

GSO_GDP_VA_URLS: tuple[str, ...] = (
    "https://nsdp.nso.gov.vn/GSO-chung/SDMXFiles/GSO/GDPVNM.xml",
    "http://nsdp.nso.gov.vn/GSO-chung/SDMXFiles/GSO/GDPVNM.xml",
)


@dataclass(frozen=True)
class SdmxIndicatorSpec:
    """Map one SDMX INDICATOR key to a `gso_macro` series."""

    vsic_code: str
    indicator_code: str
    indicator_name: str
    unit: str | None = None  # None → index_{BASE_PER}=100 (IIP-style)
    prefer_freq: str | None = None  # e.g. "Q" over "A" when both exist
    expand_to_monthly: bool = False


# AIP_ISIC4_C_IX = Manufacturing IIP (ISIC/VSIC Section C).
# NGDPVA_*_ISIC4_C_XDC = National-accounts manufacturing value added (not GRDP).
INDICATOR_BY_SDMX_KEY: dict[str, SdmxIndicatorSpec] = {
    "AIP_ISIC4_C_IX": SdmxIndicatorSpec(
        "C",
        "IIP_C",
        "Chỉ số SXCN - Chế biến chế tạo",
    ),
    "NGDPVA_R_ISIC4_C_XDC": SdmxIndicatorSpec(
        "C",
        "VA_C",
        "Giá trị gia tăng CBCT (giá so sánh 2010)",
        unit="billion_vnd_constant_2010",
        prefer_freq="Q",
        expand_to_monthly=True,
    ),
    "NGDPVA_ISIC4_C_XDC": SdmxIndicatorSpec(
        "C",
        "VA_C_NOMINAL",
        "Giá trị gia tăng CBCT (giá hiện hành)",
        unit="billion_vnd_current",
        prefer_freq="Q",
        expand_to_monthly=True,
    ),
}

IIP_INDICATOR_CODES: frozenset[str] = frozenset({"IIP_C"})
PXWEB_INDICATOR_CODES: frozenset[str] = frozenset({"SHIPMENT_C", "INVENTORY_C"})
GDP_VA_INDICATOR_CODES: frozenset[str] = frozenset({"VA_C", "VA_C_NOMINAL"})

# Target Section C series this crawler is responsible for.
TARGET_INDICATOR_CODES: frozenset[str] = (
    IIP_INDICATOR_CODES | PXWEB_INDICATOR_CODES | GDP_VA_INDICATOR_CODES
)

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
FALLBACK_CSV = RAW_DIR / "gso_iip_fallback.csv"
VA_FALLBACK_CSV = RAW_DIR / "gso_va_fallback.csv"
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
    quarterly = re.fullmatch(r"(\d{4})-Q([1-4])", text, flags=re.IGNORECASE)
    if quarterly:
        year = int(quarterly.group(1))
        quarter = int(quarterly.group(2))
        return date(year, (quarter - 1) * 3 + 1, 1)
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


def _expand_step_hold_to_monthly(
    records: list[dict[str, Any]], *, freq: str
) -> list[dict[str, Any]]:
    """Expand annual/quarterly levels to monthly via step-hold (no invented path)."""
    freq_norm = (freq or "M").upper()
    if freq_norm in {"M", "MONTHLY", ""}:
        return list(records)

    out: list[dict[str, Any]] = []
    for record in records:
        year = record["period"].year
        start_month = record["period"].month
        if freq_norm in {"A", "ANNUAL"}:
            months = range(1, 13)
        elif freq_norm in {"Q", "QUARTERLY"}:
            months = range(start_month, start_month + 3)
        else:
            out.append(dict(record))
            continue
        for month in months:
            row = dict(record)
            row["period"] = date(year, month, 1)
            out.append(row)
    return out


def _resolve_unit(spec: SdmxIndicatorSpec, series: dict[str, Any]) -> str:
    if spec.unit:
        return spec.unit
    base_per = _attr(series, "BASE_PER") or "2015"
    if base_per in {"", "_Z"}:
        base_per = "2015"
    return f"index_{base_per}=100"


def _emit_series_observations(
    *,
    series: dict[str, Any],
    spec: SdmxIndicatorSpec,
    indicator_key: str,
    result: ParseResult,
) -> list[dict[str, Any]]:
    unit = _resolve_unit(spec, series)
    freq = (_attr(series, "FREQ") or "M").upper()
    observations = _as_list(series.get("Obs"))
    if not observations:
        result.skipped.append(f"empty_observations:{indicator_key}")
        return []

    raw: list[dict[str, Any]] = []
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
        raw.append(
            {
                "vsic_code": spec.vsic_code,
                "indicator_code": spec.indicator_code,
                "indicator_name": spec.indicator_name,
                "period": period,
                "value": value,
                "unit": unit,
                "source": LIVE_SOURCE,
            }
        )

    if spec.expand_to_monthly:
        return _expand_step_hold_to_monthly(raw, freq=freq)
    return raw


def parse_sdmx_series(xml_text: str) -> ParseResult:
    """Parse GSO StructureSpecificData SDMX XML into GsoMacro-ready records.

    Identifies series via the INDICATOR dimension (e.g. AIP_ISIC4_C_IX).
    Skips missing/invalid observations with reasons; does not raise on bad obs.
    When a mapped indicator prefers FREQ=Q and quarterly series exist, annual
    series for that indicator are ignored (avoids colliding monthly expansions).
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

    grouped: dict[str, list[dict[str, Any]]] = {}
    for series in series_list:
        indicator_key = _attr(series, "INDICATOR")
        result.series_found.append(indicator_key or "<missing>")
        if not indicator_key:
            result.skipped.append("series_missing_INDICATOR")
            continue
        if indicator_key not in INDICATOR_BY_SDMX_KEY:
            result.series_unmapped.append(indicator_key)
            continue
        grouped.setdefault(indicator_key, []).append(series)

    for indicator_key, series_group in grouped.items():
        spec = INDICATOR_BY_SDMX_KEY[indicator_key]
        selected = series_group
        if spec.prefer_freq:
            preferred = [
                s
                for s in series_group
                if (_attr(s, "FREQ") or "").upper() == spec.prefer_freq.upper()
            ]
            if preferred:
                selected = preferred
            else:
                result.skipped.append(
                    f"prefer_freq_missing:{indicator_key}:{spec.prefer_freq}"
                )

        for series in selected:
            result.records.extend(
                _emit_series_observations(
                    series=series,
                    spec=spec,
                    indicator_key=indicator_key,
                    result=result,
                )
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
                    # Shipment/inventory/VA live in other endpoints — expected here.
                    expected_elsewhere = PXWEB_INDICATOR_CODES | GDP_VA_INDICATOR_CODES
                    if set(missing) <= expected_elsewhere:
                        logger.info(
                            "SDMX IIP omits %s (fetched separately)",
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


def fetch_gso_va(
    *,
    urls: tuple[str, ...] | None = None,
    client: httpx.Client | None = None,
    use_fallback: bool = True,
) -> FetchResult:
    """Fetch manufacturing VA from GDPVNM.xml; sourced CSV fallback on failure.

    Maps national-accounts Section C value added (`NGDPVA_*_ISIC4_C_XDC`) only.
    Does not invent province GRDP or treat IIP as VA.
    """
    candidate_urls = urls or GSO_GDP_VA_URLS
    errors: list[str] = []
    owns_client = client is None
    http_client = client or httpx.Client(
        timeout=HTTP_TIMEOUT, follow_redirects=True
    )

    try:
        for url in candidate_urls:
            try:
                logger.info("Fetching GSO GDP/VA SDMX from %s", url)
                xml_text = _download_xml(url, http_client)
                parse = parse_sdmx_series(xml_text)
                va_records = [
                    r
                    for r in parse.records
                    if r["indicator_code"] in GDP_VA_INDICATOR_CODES
                ]
                if not va_records:
                    raise GsoEmptySeriesError(
                        "No mapped Section C VA observations "
                        f"(found={parse.series_found}, unmapped={parse.series_unmapped})"
                    )
                missing_va = sorted(GDP_VA_INDICATOR_CODES - {r["indicator_code"] for r in va_records})
                detail = (
                    f"Parsed {len(va_records)} VA records from {url}; "
                    f"skipped={len(parse.skipped)}"
                )
                if missing_va:
                    detail += f"; series_unavailable={missing_va}"
                    logger.warning("GSO GDP SDMX missing VA series %s", missing_va)
                logger.info(detail)
                return FetchResult(
                    records=va_records,
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
        "All live GSO VA fetches failed (%s); loading deterministic fallback %s",
        failure_summary,
        VA_FALLBACK_CSV,
    )
    try:
        records = [
            r
            for r in load_fallback_records(VA_FALLBACK_CSV)
            if r["indicator_code"] in GDP_VA_INDICATOR_CODES
        ]
        if not records:
            raise GsoEmptySeriesError(
                f"VA fallback CSV produced no VA records: {VA_FALLBACK_CSV}"
            )
    except (OSError, GsoEmptySeriesError) as exc:
        logger.error("VA fallback load failed: %s", exc)
        return FetchResult(
            records=[],
            status="error",
            detail=f"{failure_summary} | fallback_error:{exc}",
            source_url=str(VA_FALLBACK_CSV),
        )

    missing = sorted(GDP_VA_INDICATOR_CODES - {r["indicator_code"] for r in records})
    detail = (
        f"fallback_after: {failure_summary}; "
        f"loaded {len(records)} VA records from {VA_FALLBACK_CSV}"
    )
    if missing:
        detail += f"; series_unavailable={missing}"
    return FetchResult(
        records=records,
        status="fallback",
        detail=detail,
        source_url=str(VA_FALLBACK_CSV),
    )


def save_gso_records(db: Session, records: list[dict[str, Any]]) -> int:
    """Upsert GsoMacro rows on (vsic_code, indicator_code, period). Idempotent.

    Dedupes within the incoming batch first so duplicate keys in one fetch
    (e.g. overlapping VA expansions) do not hit UNIQUE on flush.
    """
    # Last-wins within the batch — pending inserts are invisible to later SELECTs.
    deduped: dict[tuple[str, str, Any], dict[str, Any]] = {}
    for r in records:
        key = (r["vsic_code"], r["indicator_code"], r["period"])
        deduped[key] = r

    inserted = 0
    pending: dict[tuple[str, str, Any], GsoMacro] = {}
    for key, r in deduped.items():
        existing = (
            db.query(GsoMacro)
            .filter(
                GsoMacro.vsic_code == r["vsic_code"],
                GsoMacro.indicator_code == r["indicator_code"],
                GsoMacro.period == r["period"],
            )
            .first()
        )
        if existing is None:
            existing = pending.get(key)
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
            row = GsoMacro(**payload)
            db.add(row)
            pending[key] = row
            inserted += 1
    db.commit()
    return inserted


def fetch_gso_macro(
    *,
    urls: tuple[str, ...] | None = None,
    client: httpx.Client | None = None,
    use_fallback: bool = True,
) -> FetchResult:
    """Fetch IIP (SDMX) + VA (GDP SDMX) + shipment/inventory (PX-Web) for Section C."""
    from crawlers.gso.pxweb_client import fetch_pxweb_section_c

    owns = client is None
    http = client or httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True)
    try:
        iip = fetch_gso_iip(urls=urls, client=http, use_fallback=use_fallback)
        va = fetch_gso_va(client=http, use_fallback=use_fallback)
        px = fetch_pxweb_section_c(client=http, use_fallback=use_fallback)

        # IIP-only SDMX naturally lacks shipment/inventory/VA — drop that noise once
        # the dedicated fetches run.
        iip_detail = iip.detail
        if "series_unavailable=" in iip_detail:
            iip_detail = iip_detail.split("; series_unavailable=")[0]

        records = list(iip.records) + list(va.records) + list(px.records)
        missing = _unavailable_targets(records)
        parts = [
            f"iip:{iip.status}:{iip_detail}",
            f"va:{va.status}:{va.detail}",
            f"pxweb:{px.status}:{px.detail}",
        ]
        if missing:
            parts.append(f"series_unavailable={missing}")
        detail = " | ".join(parts)

        statuses = {iip.status, va.status, px.status}
        if not records:
            status = "error"
        elif statuses <= {"error"}:
            status = "error"
        elif "fallback" in statuses:
            status = "fallback"
        else:
            status = "ok"

        source_parts = [p for p in (iip.source_url, va.source_url) if p]
        if px.source_urls:
            source_parts.append(",".join(px.source_urls))
        source_url = ";".join(source_parts) if source_parts else None

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
