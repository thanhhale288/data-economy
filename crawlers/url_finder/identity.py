"""Identity / gold-label IO with an explicit no-leak fence."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from crawlers.companies.masothue_frame import extract_province, normalize_tax_code
from crawlers.url_finder.domain import registrable_domain
from crawlers.url_finder.paths import (
    IDENTITY_FILE,
    LABELS_FILE,
    SEED_FILE,
)

FORBIDDEN_IDENTITY_KEYS = frozenset(
    {
        "website",
        "website_url",
        "url",
        "gold_url",
        "gold_domain",
        "official_url",
        "homepage",
    }
)
TAX_IN_H1_RE = re.compile(r"^(\d{10})(?:-\d{3})?\s*[-–]\s*(.+)$")


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _as_object_list(payload: Any, *, label: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError(f"{label} must be a JSON list")
    rows: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(f"{label} rows must be objects")
        rows.append(item)
    return rows


def assert_no_url_fields(row: dict[str, Any], *, context: str) -> None:
    leaked = sorted(k for k in row if k.lower() in FORBIDDEN_IDENTITY_KEYS)
    if leaked:
        raise ValueError(
            f"{context}: identity must not contain URL/gold fields {leaked} "
            "(blind eval fence; see Evol-1 T03 / T08)"
        )


def load_identity(path: Path | None = None) -> list[dict[str, Any]]:
    target = path or IDENTITY_FILE
    payload = json.loads(target.read_text(encoding="utf-8"))
    rows = _as_object_list(payload, label=str(target))
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        assert_no_url_fields(row, context=str(target))
        ticker = str(row.get("ticker") or "").strip().upper()
        if not ticker:
            raise ValueError(f"{target}: missing ticker")
        if ticker in seen:
            raise ValueError(f"{target}: duplicate ticker {ticker}")
        seen.add(ticker)
        tax = normalize_tax_code(str(row.get("tax_id") or ""))
        if not tax or "-" in tax:
            raise ValueError(f"{target}: {ticker} needs a 10-digit HQ tax_id")
        out.append(
            {
                **row,
                "ticker": ticker,
                "legal_name": str(row.get("legal_name") or "").strip(),
                "tax_id": tax,
                "address": str(row.get("address") or "").strip(),
                "province": str(row.get("province") or "").strip(),
                "aliases": [
                    str(a).strip()
                    for a in (row.get("aliases") or [])
                    if str(a).strip()
                ],
            }
        )
    return out


def load_labels(path: Path | None = None) -> dict[str, dict[str, Any]]:
    target = path or LABELS_FILE
    payload = json.loads(target.read_text(encoding="utf-8"))
    rows = _as_object_list(payload, label=str(target))
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        ticker = str(row.get("ticker") or "").strip().upper()
        gold = str(row.get("gold_url") or "").strip()
        if not ticker or not gold:
            raise ValueError(f"{target}: each label needs ticker + gold_url")
        out[ticker] = {
            "ticker": ticker,
            "gold_url": gold,
            "gold_domain": registrable_domain(gold),
            "note": str(row.get("note") or ""),
        }
    return out


def load_seed_gold(path: Path | None = None) -> list[dict[str, Any]]:
    """Corporate website_url from seed — never digital_presence shop URLs."""
    target = path or SEED_FILE
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"seed must be a JSON list: {target}")
    rows: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        ticker = str(item.get("stock_code") or "").strip().upper()
        name = str(item.get("name") or "").strip()
        gold = str(item.get("website_url") or "").strip()
        if not ticker or not gold:
            continue
        rows.append(
            {
                "ticker": ticker,
                "legal_name": name,
                "gold_url": gold,
                "gold_domain": registrable_domain(gold),
                "note": (
                    "corporate website_url from data/seeds/companies.json; "
                    "not digital_presence shop URL (e.g. FPT fpt.com.vn not fptshop.com.vn)"
                ),
            }
        )
    return rows


def parse_masothue_hq(html: str, page_url: str) -> dict[str, Any] | None:
    """Extract HQ tax identity from a masothue company page. Branches return None."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html or "", "html.parser")
    h1 = soup.find("h1")
    heading = h1.get_text(" ", strip=True) if h1 else ""
    parsed = urlparse(page_url)
    path = parsed.path or ""
    if re.search(r"/\d{10}-\d{3}-", path):
        return None
    name = heading
    match = TAX_IN_H1_RE.match(heading)
    if match:
        name = match.group(2).strip()
    if name.upper().startswith("CHI NHÁNH") or name.upper().startswith("CHI NHANH"):
        return None

    fields: dict[str, str] = {}
    for tr in soup.select("table.table-taxinfo tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if len(cells) >= 2:
            fields[cells[0].strip().lower()] = cells[1].strip()
        elif len(cells) == 1 and not fields.get("_title"):
            fields["_title"] = cells[0].strip()

    tax = normalize_tax_code(fields.get("mã số thuế") or (match.group(1) if match else ""))
    if not tax or "-" in tax:
        return None
    legal = fields.get("_title") or name
    address = fields.get("địa chỉ") or fields.get("địa chỉ thuế") or ""
    aliases: list[str] = []
    for key in ("tên viết tắt", "tên quốc tế"):
        value = fields.get(key)
        if value:
            aliases.append(value)
    return {
        "legal_name": legal,
        "tax_id": tax,
        "address": address,
        "province": extract_province(address),
        "aliases": aliases,
        "source_url": page_url,
        "source_dataset": "masothue.com",
    }


def write_json(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = list(rows)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
