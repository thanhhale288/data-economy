"""OECD SDMX ingestion for manufacturing / digital-economy indicators.

Uses raw httpx against the current OECD Data Explorer REST API
(https://sdmx.oecd.org/public/rest/) rather than the sdmx1 client:

- OECD agency/dataflow IDs (e.g. OECD.SDD.STES,DSD_STES@DF_INDSERV) are awkward
  in sdmx1 source registries without custom wiring.
- httpx is trivial to mock in unit tests and matches the verified endpoints.
- We parse SDMX-JSON v2 directly so period / frequency / indicator come from
  response metadata, not guessed constants.

Vietnam-first policy (see docs/adr/0001-oecd-vietnam-macro-policy.md):
- Persist real VNM series only (today: INDIGO). Never invent MEI_IP / BCI / ICT for VNM.
- Fetch MEI_IP for peer area EA20 as an external leading indicator (country=EA20,
  source=OECD_PEER) for IIP forecasting — not as a Vietnam substitute.
- Primary VN manufacturing target remains GSO IIP.

Frequency harmonization to monthly:
- Quarterly → monthly: linear interpolation between quarter-start anchors.
- Annual → monthly: step-hold (same annual value for Jan–Dec of that year).
  Linear annual interpolation is intentionally avoided (would invent false
  intra-year dynamics for a structural annual index like INDIGO).
- Monthly series: unchanged.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from backend.app.models import OecdIndicator

logger = logging.getLogger(__name__)

OECD_REST_BASE = "https://sdmx.oecd.org/public/rest"
REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_FIXTURE_DIR = REPO_ROOT / "data" / "raw"

LIVE_SOURCE = "OECD"
FALLBACK_SOURCE = "OECD_FALLBACK"
PEER_SOURCE = "OECD_PEER"

# Euro-area manufacturing IP — verified live leading peer (not Vietnam).
PEER_MEI_IP_COUNTRY = "EA20"

FREQ_LABELS = {
    "M": "monthly",
    "Q": "quarterly",
    "A": "annual",
    "monthly": "monthly",
    "quarterly": "quarterly",
    "annual": "annual",
}


class OecdSdmxError(Exception):
    """Base error for OECD SDMX ingestion."""


class NetworkError(OecdSdmxError):
    """Transport / connection failure talking to OECD."""


class HttpError(OecdSdmxError):
    """Non-success HTTP response that is not an empty-series signal."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class ParseError(OecdSdmxError):
    """SDMX payload could not be parsed into observations."""


class SeriesUnavailableError(OecdSdmxError):
    """Requested series has no records for the target country."""


@dataclass(frozen=True)
class IndicatorSpec:
    """One OECD series to ingest (dataflows differ per indicator)."""

    indicator_code: str
    indicator_name: str
    agency: str
    dataflow: str
    # SDMX key without time; `{country}` is substituted at fetch time.
    series_key_template: str
    isic_code: str | None = None
    # When set, keep only observations whose ACTIVITY dimension matches.
    activity_filter: str | None = None
    # Local fixture used only when the live endpoint is unreachable (network).
    fallback_fixture: str | None = None


# Verified against https://sdmx.oecd.org/public/rest/ (2026-07-17 / 2026-07-18).
INDICATOR_SPECS: tuple[IndicatorSpec, ...] = (
    IndicatorSpec(
        indicator_code="MEI_IP",
        indicator_name="Industrial Production Index",
        agency="OECD.SDD.STES",
        dataflow="DSD_STES@DF_INDSERV",
        series_key_template="{country}.M.PRVM.IX.C.Y.......",
        isic_code="C",
        activity_filter="C",
    ),
    IndicatorSpec(
        indicator_code="MEI_BCI",
        indicator_name="Business Confidence Index",
        agency="OECD.SDD.STES",
        dataflow="DSD_STES@DF_BTS",
        series_key_template="{country}.M.BCICP.PB.C.Y.......",
        isic_code="C",
        activity_filter="C",
    ),
    IndicatorSpec(
        indicator_code="INDIGO",
        indicator_name="Digital Trade Openness Index",
        agency="OECD.TAD.TPD",
        dataflow="DSD_INDIGO@DF_INDIGO",
        series_key_template="A.{country}.INDIGO.INDIGO_I_UNW.IX._Z",
        isic_code=None,
        fallback_fixture="oecd_indigo_vnm.json",
    ),
    IndicatorSpec(
        indicator_code="ICT_INVEST",
        indicator_name="ICT Investment (GFCF ICT equipment)",
        agency="OECD.SDD.NAD",
        dataflow="DSD_NAMAIN10@DF_TABLE1_EXPENDITURE_GFCF_ASSET",
        series_key_template="A.{country}.S1.S1.P51G.N1132G._T._Z.USD_EXC.VQ.N.T0102",
        isic_code="C",
    ),
)

# Peer leading series for VN IIP forecast (country ≠ VNM).
PEER_SPECS: tuple[tuple[IndicatorSpec, str], ...] = (
    (INDICATOR_SPECS[0], PEER_MEI_IP_COUNTRY),  # MEI_IP @ EA20
)


@dataclass
class IndicatorStatus:
    indicator_code: str
    status: str  # ok | unavailable | network_error | http_error | parse_error | fixture
    detail: str = ""
    records: int = 0
    country: str = "VNM"


@dataclass
class CrawlResult:
    records: list[dict[str, Any]] = field(default_factory=list)
    statuses: list[IndicatorStatus] = field(default_factory=list)

    @property
    def detail_summary(self) -> str:
        parts = [
            f"{s.indicator_code}@{s.country}:{s.status}({s.records})"
            for s in self.statuses
        ]
        return "; ".join(parts)


def build_data_url(
    spec: IndicatorSpec,
    country: str = "VNM",
    *,
    start_period: str = "2010",
) -> str:
    key = spec.series_key_template.format(country=country)
    return (
        f"{OECD_REST_BASE}/data/{spec.agency},{spec.dataflow}/{key}"
        f"?startPeriod={start_period}&dimensionAtObservation=AllDimensions"
        f"&format=jsondata"
    )


def parse_period(period_id: str) -> date:
    """Parse SDMX TIME_PERIOD ids into a month-start date."""
    text = period_id.strip()
    if len(text) == 4 and text.isdigit():
        return date(int(text), 1, 1)
    if "-Q" in text:
        year_s, q_s = text.split("-Q", 1)
        quarter = int(q_s)
        if quarter not in (1, 2, 3, 4):
            raise ParseError(f"Invalid quarter period: {period_id}")
        return date(int(year_s), (quarter - 1) * 3 + 1, 1)
    if len(text) >= 7 and text[4] == "-":
        year = int(text[0:4])
        month = int(text[5:7])
        return date(year, month, 1)
    raise ParseError(f"Unrecognized TIME_PERIOD: {period_id}")


def _dim_values(structure: dict[str, Any]) -> list[tuple[str, list[dict[str, Any]]]]:
    """Return ordered (dimension_id, values) for observation keys."""
    dimensions = structure.get("dimensions") or {}
    ordered: list[tuple[str, list[dict[str, Any]]]] = []
    for section in ("dataSet", "series", "observation"):
        for dim in dimensions.get(section) or []:
            ordered.append((dim["id"], dim.get("values") or []))
    return ordered


def parse_sdmx_json(
    payload: dict[str, Any],
    *,
    indicator_code: str,
    indicator_name: str,
    isic_code: str | None = None,
    country_filter: str | None = "VNM",
    activity_filter: str | None = None,
    source: str = LIVE_SOURCE,
) -> list[dict[str, Any]]:
    """Parse an SDMX-JSON v2 data message into OecdIndicator-shaped dicts."""
    try:
        data = payload["data"]
        datasets = data.get("dataSets") or []
        structures = data.get("structures") or []
        if not datasets or not structures:
            return []
        structure = structures[datasets[0].get("structure", 0)]
        dims = _dim_values(structure)
        if not dims:
            raise ParseError("SDMX structure has no dimensions")
        observations = datasets[0].get("observations") or {}
    except (KeyError, IndexError, TypeError) as exc:
        raise ParseError(f"Invalid SDMX-JSON layout: {exc}") from exc

    records: list[dict[str, Any]] = []
    for obs_key, obs_values in observations.items():
        try:
            indexes = [int(part) for part in str(obs_key).split(":")]
        except ValueError as exc:
            raise ParseError(f"Bad observation key {obs_key!r}") from exc
        if len(indexes) != len(dims):
            raise ParseError(
                f"Observation key arity {len(indexes)} != dimensions {len(dims)}"
            )

        dim_map: dict[str, str] = {}
        for (dim_id, values), idx in zip(dims, indexes):
            if idx < 0 or idx >= len(values):
                raise ParseError(f"Dimension index out of range for {dim_id}")
            value_id = values[idx].get("id")
            if value_id is None:
                raise ParseError(f"Missing id for dimension {dim_id}")
            dim_map[dim_id] = str(value_id)

        if country_filter and dim_map.get("REF_AREA") not in (None, country_filter):
            continue
        if activity_filter and dim_map.get("ACTIVITY") not in (None, activity_filter):
            continue

        raw_value = obs_values[0] if obs_values else None
        if raw_value is None:
            continue

        freq_code = dim_map.get("FREQ", "M")
        frequency = FREQ_LABELS.get(freq_code, freq_code)
        unit = dim_map.get("UNIT_MEASURE", "index")

        period_id = dim_map.get("TIME_PERIOD")
        if not period_id:
            raise ParseError("Observation missing TIME_PERIOD")

        records.append(
            {
                "indicator_code": indicator_code,
                "indicator_name": indicator_name,
                "country": dim_map.get("REF_AREA") or country_filter or "VNM",
                "isic_code": isic_code,
                "period": parse_period(period_id),
                "value": float(raw_value),
                "unit": unit,
                "frequency": frequency,
                "source": source,
            }
        )

    records.sort(key=lambda r: (r["indicator_code"], r["country"], r["period"]))
    return records


def expand_annual_to_monthly_step(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand annual series to monthly via step-hold (same value Jan–Dec).

    Linear annual→monthly is intentionally not used: INDIGO is a structural
    annual openness index; inventing a monthly path would fake dynamics.
    """
    monthly: list[dict[str, Any]] = []
    annual: list[dict[str, Any]] = []
    other: list[dict[str, Any]] = []

    for record in records:
        freq = record.get("frequency")
        if freq == "annual":
            annual.append(record)
        elif freq == "monthly":
            monthly.append(dict(record))
        else:
            other.append(dict(record))

    expanded: list[dict[str, Any]] = []
    for record in annual:
        year = record["period"].year
        for month in range(1, 13):
            row = dict(record)
            row["period"] = date(year, month, 1)
            row["frequency"] = "monthly"
            expanded.append(row)

    result = monthly + expanded + other
    result.sort(key=lambda r: (r["indicator_code"], r["country"], r["period"]))
    return result


def interpolate_quarterly_to_monthly(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand quarterly series to monthly via linear interpolation; leave others as-is."""
    monthly: list[dict[str, Any]] = []
    quarterly: list[dict[str, Any]] = []
    other: list[dict[str, Any]] = []

    for record in records:
        freq = record.get("frequency")
        if freq == "quarterly":
            quarterly.append(record)
        elif freq == "monthly":
            monthly.append(dict(record))
        else:
            other.append(dict(record))

    if not quarterly:
        return monthly + other

    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for record in quarterly:
        key = (
            record["indicator_code"],
            record["country"],
            record.get("isic_code"),
            record.get("unit"),
            record.get("source"),
        )
        groups.setdefault(key, []).append(record)

    expanded: list[dict[str, Any]] = []
    for series in groups.values():
        series = sorted(series, key=lambda r: r["period"])
        if len(series) == 1:
            expanded.extend(_flat_quarter_months(series[0]))
            continue
        for i, left in enumerate(series[:-1]):
            right = series[i + 1]
            expanded.extend(_linear_months_between(left, right, include_right=False))
        expanded.extend(_flat_quarter_months(series[-1]))

    result = monthly + expanded + other
    result.sort(key=lambda r: (r["indicator_code"], r["country"], r["period"]))
    return result


def harmonize_to_monthly(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply annual step-hold then quarterly linear expansion."""
    return interpolate_quarterly_to_monthly(expand_annual_to_monthly_step(records))


def _flat_quarter_months(record: dict[str, Any]) -> list[dict[str, Any]]:
    start = record["period"]
    out: list[dict[str, Any]] = []
    for offset in range(3):
        month = start.month + offset
        year = start.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        row = dict(record)
        row["period"] = date(year, month, 1)
        row["frequency"] = "monthly"
        out.append(row)
    return out


def _linear_months_between(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    include_right: bool,
) -> list[dict[str, Any]]:
    start = left["period"]
    end = right["period"]
    start_idx = start.year * 12 + (start.month - 1)
    end_idx = end.year * 12 + (end.month - 1)
    span = end_idx - start_idx
    if span <= 0:
        return [dict(left)] if not include_right else [dict(left), dict(right)]

    out: list[dict[str, Any]] = []
    stop = end_idx + 1 if include_right else end_idx
    for idx in range(start_idx, stop):
        t = (idx - start_idx) / span
        year, month0 = divmod(idx, 12)
        row = dict(left)
        row["period"] = date(year, month0 + 1, 1)
        row["value"] = float(left["value"]) + t * (
            float(right["value"]) - float(left["value"])
        )
        row["frequency"] = "monthly"
        out.append(row)
    return out


def _is_empty_series_response(status_code: int, body: str) -> bool:
    if status_code not in (404, 400):
        return False
    text = (body or "").strip().lower()
    return text in {
        "norecordsfound",
        "noresultsfound",
        "no results found",
        "no records found",
    } or "norecordsfound" in text or "noresultsfound" in text


def fetch_sdmx_json(
    url: str,
    *,
    client: httpx.Client | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """GET an SDMX-JSON data URL; raise typed errors on failure."""
    owns_client = client is None
    http = client or httpx.Client(timeout=timeout, follow_redirects=True)
    try:
        try:
            response = http.get(
                url,
                headers={
                    "Accept": "application/vnd.sdmx.data+json;version=2.0.0,application/json"
                },
            )
        except httpx.HTTPError as exc:
            raise NetworkError(str(exc)) from exc

        body = response.text or ""
        if _is_empty_series_response(response.status_code, body):
            raise SeriesUnavailableError(
                f"No OECD records for URL (HTTP {response.status_code}): {url}"
            )
        if response.status_code >= 400:
            raise HttpError(response.status_code, body[:500] or response.reason_phrase)

        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise ParseError(f"Response is not JSON: {exc}") from exc
    finally:
        if owns_client:
            http.close()


def load_fixture_payload(filename: str) -> dict[str, Any]:
    path = RAW_FIXTURE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open() as fh:
        wrapper = json.load(fh)
    if "sdmx" in wrapper:
        return wrapper["sdmx"]
    return wrapper


def fetch_indicator(
    spec: IndicatorSpec,
    *,
    country: str = "VNM",
    client: httpx.Client | None = None,
    allow_fixture_fallback: bool = True,
    source: str | None = None,
) -> tuple[list[dict[str, Any]], IndicatorStatus]:
    """Fetch one indicator; never fabricates values for missing VN series."""
    record_source = source or (PEER_SOURCE if country != "VNM" else LIVE_SOURCE)
    url = build_data_url(spec, country=country)
    try:
        payload = fetch_sdmx_json(url, client=client)
        records = parse_sdmx_json(
            payload,
            indicator_code=spec.indicator_code,
            indicator_name=spec.indicator_name,
            isic_code=spec.isic_code,
            country_filter=country,
            activity_filter=spec.activity_filter,
            source=record_source,
        )
        if not records:
            status = IndicatorStatus(
                spec.indicator_code,
                "unavailable",
                f"Empty parse for {country} at {spec.agency},{spec.dataflow}",
                country=country,
            )
            logger.warning(
                "OECD %s UNAVAILABLE for %s", spec.indicator_code, country
            )
            return [], status
        records = harmonize_to_monthly(records)
        return records, IndicatorStatus(
            spec.indicator_code,
            "ok",
            url,
            records=len(records),
            country=country,
        )
    except SeriesUnavailableError as exc:
        logger.warning("OECD %s UNAVAILABLE: %s", spec.indicator_code, exc)
        return [], IndicatorStatus(
            spec.indicator_code, "unavailable", str(exc), country=country
        )
    except NetworkError as exc:
        if allow_fixture_fallback and spec.fallback_fixture and country == "VNM":
            try:
                payload = load_fixture_payload(spec.fallback_fixture)
                records = parse_sdmx_json(
                    payload,
                    indicator_code=spec.indicator_code,
                    indicator_name=spec.indicator_name,
                    isic_code=spec.isic_code,
                    country_filter=country,
                    activity_filter=spec.activity_filter,
                    source=FALLBACK_SOURCE,
                )
                records = harmonize_to_monthly(records)
                detail = (
                    f"network_error={exc}; used fixture data/raw/{spec.fallback_fixture}"
                )
                logger.error(
                    "OECD %s network error; using fixture. %s",
                    spec.indicator_code,
                    detail,
                )
                return records, IndicatorStatus(
                    spec.indicator_code,
                    "fixture",
                    detail,
                    records=len(records),
                    country=country,
                )
            except Exception as fixture_exc:  # noqa: BLE001 - surface both failures
                detail = f"network_error={exc}; fixture_failed={fixture_exc}"
                logger.error(
                    "OECD %s network+fixture failure: %s",
                    spec.indicator_code,
                    detail,
                )
                return [], IndicatorStatus(
                    spec.indicator_code, "network_error", detail, country=country
                )
        logger.error("OECD %s network error: %s", spec.indicator_code, exc)
        return [], IndicatorStatus(
            spec.indicator_code, "network_error", str(exc), country=country
        )
    except HttpError as exc:
        logger.error("OECD %s HTTP error: %s", spec.indicator_code, exc)
        return [], IndicatorStatus(
            spec.indicator_code, "http_error", str(exc), country=country
        )
    except ParseError as exc:
        logger.error("OECD %s parse error: %s", spec.indicator_code, exc)
        return [], IndicatorStatus(
            spec.indicator_code, "parse_error", str(exc), country=country
        )


def fetch_oecd_indicators(
    *,
    country: str = "VNM",
    client: httpx.Client | None = None,
    specs: tuple[IndicatorSpec, ...] | None = None,
    allow_fixture_fallback: bool = True,
    include_peers: bool = True,
) -> CrawlResult:
    """Fetch configured OECD indicators for ``country`` plus optional peers."""
    result = CrawlResult()
    for spec in specs or INDICATOR_SPECS:
        records, status = fetch_indicator(
            spec,
            country=country,
            client=client,
            allow_fixture_fallback=allow_fixture_fallback,
        )
        result.statuses.append(status)
        result.records.extend(records)

    if include_peers and country == "VNM":
        for peer_spec, peer_country in PEER_SPECS:
            records, status = fetch_indicator(
                peer_spec,
                country=peer_country,
                client=client,
                allow_fixture_fallback=False,
                source=PEER_SOURCE,
            )
            result.statuses.append(status)
            result.records.extend(records)
    return result


def save_oecd_records(db: Session, records: list[dict[str, Any]]) -> int:
    """Upsert by (indicator_code, country, period). Idempotent on re-run."""
    upserted = 0
    for raw in records:
        r = {
            "indicator_code": raw["indicator_code"],
            "indicator_name": raw["indicator_name"],
            "country": raw.get("country") or "VNM",
            "isic_code": raw.get("isic_code"),
            "period": raw["period"],
            "value": float(raw["value"]),
            "unit": raw.get("unit") or "index",
            "frequency": raw.get("frequency") or "monthly",
            "source": raw.get("source") or LIVE_SOURCE,
        }
        existing = (
            db.query(OecdIndicator)
            .filter(
                OecdIndicator.indicator_code == r["indicator_code"],
                OecdIndicator.country == r["country"],
                OecdIndicator.period == r["period"],
            )
            .first()
        )
        if existing:
            existing.indicator_name = r["indicator_name"]
            existing.isic_code = r["isic_code"]
            existing.value = r["value"]
            existing.unit = r["unit"]
            existing.frequency = r["frequency"]
            existing.source = r["source"]
        else:
            db.add(OecdIndicator(**r))
        upserted += 1
    db.commit()
    return upserted


def run_oecd_crawl(db: Session, *, country: str = "VNM") -> int:
    """Crawl OECD indicators and persist; returns number of upserted rows."""
    result = fetch_oecd_indicators(country=country)
    for status in result.statuses:
        logger.info(
            "OECD crawl %s@%s -> %s (%s records) %s",
            status.indicator_code,
            status.country,
            status.status,
            status.records,
            status.detail[:200],
        )
    return save_oecd_records(db, result.records)
