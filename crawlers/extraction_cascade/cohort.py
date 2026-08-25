"""Build the T05 cohort: 28 listed websites + optional frame_pilot URLs."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from crawlers.companies.listed_companies import load_seed_companies
from crawlers.extraction_cascade.paths import COHORT_PATH, RAW_DIR, ROOT

CohortSource = Literal["listed28", "frame_pilot"]


@dataclass(frozen=True)
class CohortFirm:
    firm_id: str
    source_cohort: CohortSource
    website_url: str
    name: str = ""
    vsic_code: str | None = None
    tax_code: str | None = None
    notes: str = ""


def listed28_cohort() -> list[CohortFirm]:
    rows: list[CohortFirm] = []
    for company in load_seed_companies():
        url = (company.get("website_url") or "").strip()
        ticker = str(company.get("stock_code") or "").strip().upper()
        if not ticker or not url:
            continue
        rows.append(
            CohortFirm(
                firm_id=ticker,
                source_cohort="listed28",
                website_url=url,
                name=str(company.get("name") or ""),
                vsic_code=str(company.get("vsic_code") or "") or None,
            )
        )
    return rows


def load_frame_urls_file(path: Path) -> list[CohortFirm]:
    """Optional JSON list produced after URL-finder on frame_pilot."""
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"frame urls must be a JSON list: {path}")
    out: list[CohortFirm] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        url = str(row.get("website_url") or row.get("url") or "").strip()
        firm_id = str(row.get("firm_id") or row.get("tax_code") or "").strip()
        if not url or not firm_id:
            continue
        out.append(
            CohortFirm(
                firm_id=firm_id,
                source_cohort="frame_pilot",
                website_url=url,
                name=str(row.get("name") or row.get("company_name") or ""),
                vsic_code=str(row.get("vsic_code") or row.get("vsic_4digit") or "") or None,
                tax_code=str(row.get("tax_code") or "") or None,
                notes=str(row.get("notes") or ""),
            )
        )
    return out


def sample_frame_for_url_finder(
    *,
    frame_csv: Path | None = None,
    per_division: int = 40,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Stratified sample from T02 frame (identity only — no website column)."""
    path = frame_csv or (ROOT / "data" / "raw" / "frame_pilot" / "frame_pilot.csv")
    if not path.exists():
        return []
    by_div: dict[str, list[dict[str, Any]]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            div = str(row.get("vsic_division") or "").strip()
            by_div.setdefault(div, []).append(row)
    sample: list[dict[str, Any]] = []
    for div in sorted(by_div):
        rows = by_div[div]
        start = max(0, offset)
        sample.extend(rows[start : start + per_division])
    return sample


def build_cohort(
    *,
    frame_urls_path: Path | None = None,
    include_listed: bool = True,
) -> list[CohortFirm]:
    firms: list[CohortFirm] = []
    if include_listed:
        firms.extend(listed28_cohort())
    frame_path = frame_urls_path or (RAW_DIR / "frame_urls.json")
    firms.extend(load_frame_urls_file(frame_path))
    # Dedupe by firm_id preferring listed28
    seen: set[str] = set()
    out: list[CohortFirm] = []
    for firm in firms:
        key = firm.firm_id.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(firm)
    return out


def cohort_sha256(firms: list[CohortFirm]) -> str:
    blob = json.dumps([asdict(f) for f in firms], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def write_cohort(firms: list[CohortFirm], path: Path | None = None) -> Path:
    target = path or COHORT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "n": len(firms),
        "listed28": sum(1 for f in firms if f.source_cohort == "listed28"),
        "frame_pilot": sum(1 for f in firms if f.source_cohort == "frame_pilot"),
        "sha256": cohort_sha256(firms),
        "firms": [asdict(f) for f in firms],
    }
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target
