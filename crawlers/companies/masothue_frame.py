"""Parse & harvest masothue.com industry listings for Evol-1 T02 pilot frame.

Public tax-directory pages only. Does not invent firms; empty/blocked pages
yield fewer rows and must be recorded in PROVENANCE.
"""

from __future__ import annotations

import csv
import logging
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.masothue.com"
INDUSTRY_INDEX = f"{BASE_URL}/tra-cuu-ma-so-thue-theo-nganh-nghe/"
USER_AGENT = (
    "Mozilla/5.0 (compatible; MfgDataEconomy/1.0; +research; "
    "pilot-frame; contact=lab)"
)
DEFAULT_DIVISIONS = frozenset({"10", "22", "25"})
TAX_RE = re.compile(r"^(\d{10})(-\d{3})?$")
INDUSTRY_HREF_RE = re.compile(
    r"/tra-cuu-ma-so-thue-theo-nganh-nghe/([a-z0-9-]+)-(\d{4,5})(?:[/?#]|$)",
    re.IGNORECASE,
)
PROVINCE_RE = re.compile(
    r"(?:Tỉnh|Thành phố)\s+([^,]+?)(?:,\s*Việt Nam)?\s*$",
    re.IGNORECASE,
)

CSV_FIELDS = (
    "company_name",
    "tax_code",
    "vsic_4digit",
    "vsic_division",
    "address",
    "province",
    "founded_year",
    "source_url",
    "listing_url",
    "retrieved_at",
)


@dataclass(frozen=True)
class IndustryLink:
    vsic_code: str
    slug: str
    path: str
    name: str = ""

    @property
    def url(self) -> str:
        return urljoin(BASE_URL, self.path)


@dataclass
class FirmRow:
    company_name: str
    tax_code: str
    vsic_4digit: str
    vsic_division: str
    address: str
    province: str
    founded_year: str
    source_url: str
    listing_url: str
    retrieved_at: str

    def completeness(self) -> int:
        return sum(
            1
            for v in (
                self.company_name,
                self.tax_code,
                self.vsic_4digit,
                self.address,
                self.province,
                self.founded_year,
            )
            if v
        )


def normalize_tax_code(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = re.sub(r"\s+", "", str(raw).strip())
    match = TAX_RE.match(text)
    return match.group(0) if match else None


def normalize_vsic_code(raw: str | None) -> str | None:
    if raw is None:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if len(digits) < 4:
        return None
    code = digits[:4]
    div = int(code[:2])
    if div < 10 or div > 33:
        return None
    return code


def extract_province(address: str) -> str:
    if not address:
        return ""
    match = PROVINCE_RE.search(address.strip())
    if match:
        return match.group(1).strip()
    # Fallback: last comma segment before "Việt Nam"
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if not parts:
        return ""
    if parts[-1].lower() in {"việt nam", "viet nam"}:
        parts = parts[:-1]
    return parts[-1] if parts else ""


def clean_address(addr_tag) -> str:
    if addr_tag is None:
        return ""
    clone = BeautifulSoup(str(addr_tag), "html.parser").address
    if clone is None:
        return ""
    for junk in clone.select("div, script, style, svg"):
        junk.decompose()
    text = clone.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    # Drop leading map-marker noise if any
    return text


def parse_industry_index(html: str, *, divisions: Iterable[str] = DEFAULT_DIVISIONS) -> list[IndustryLink]:
    wanted = {str(d).zfill(2) for d in divisions}
    soup = BeautifulSoup(html, "html.parser")
    found: dict[str, IndustryLink] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        match = INDUSTRY_HREF_RE.search(href)
        if not match:
            continue
        slug, code = match.group(1), match.group(2)
        vsic = normalize_vsic_code(code)
        if vsic is None or vsic[:2] not in wanted:
            continue
        path = f"/tra-cuu-ma-so-thue-theo-nganh-nghe/{slug}-{code}"
        name = a.get_text(" ", strip=True)
        if name.isdigit():
            # Prefer sibling text link when this anchor is only the code.
            name = slug.replace("-", " ")
        if vsic not in found or (name and not found[vsic].name):
            found[vsic] = IndustryLink(vsic_code=vsic, slug=slug, path=path, name=name)
    return sorted(found.values(), key=lambda x: x.vsic_code)


def parse_listing_page(
    html: str,
    *,
    vsic_4digit: str,
    listing_url: str,
    retrieved_at: str | None = None,
) -> list[FirmRow]:
    vsic = normalize_vsic_code(vsic_4digit)
    if vsic is None:
        return []
    retrieved = retrieved_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(".tax-listing > div[data-prefetch]")
    rows: list[FirmRow] = []
    for card in cards:
        name_a = card.select_one("h3 a")
        company_name = name_a.get_text(" ", strip=True) if name_a else ""
        tax_code = None
        source_url = ""
        for a in card.find_all("a", href=True):
            maybe = normalize_tax_code(a.get_text(" ", strip=True))
            if maybe:
                tax_code = maybe
                source_url = urljoin(BASE_URL, a["href"])
                break
        if not tax_code:
            prefetch = card.get("data-prefetch") or ""
            m = re.match(r"/(\d{10}(?:-\d{3})?)-", prefetch)
            if m:
                tax_code = normalize_tax_code(m.group(1))
                source_url = urljoin(BASE_URL, prefetch)
        if not tax_code or not company_name:
            continue
        address = clean_address(card.find("address"))
        rows.append(
            FirmRow(
                company_name=company_name,
                tax_code=tax_code,
                vsic_4digit=vsic,
                vsic_division=vsic[:2],
                address=address,
                province=extract_province(address),
                founded_year="",
                source_url=source_url,
                listing_url=listing_url,
                retrieved_at=retrieved,
            )
        )
    return rows


def max_page_from_listing(html: str) -> int:
    pages = {1}
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        m = re.search(r"[?&]page=(\d{1,4})(?:[&#]|$)", href)
        if m:
            pages.add(int(m.group(1)))
            continue
        text = a.get_text(strip=True)
        if text.isdigit() and len(text) <= 4:
            pages.add(int(text))
    return max(pages)


def merge_prefer_richer(existing: FirmRow, new: FirmRow) -> FirmRow:
    return new if new.completeness() > existing.completeness() else existing


def dedupe_by_tax(rows: Iterable[FirmRow]) -> list[FirmRow]:
    by_tax: dict[str, FirmRow] = {}
    for row in rows:
        key = row.tax_code
        if key not in by_tax:
            by_tax[key] = row
        else:
            by_tax[key] = merge_prefer_richer(by_tax[key], row)
    return sorted(by_tax.values(), key=lambda r: (r.vsic_division, r.vsic_4digit, r.tax_code))


def summarize_division_province(rows: Iterable[FirmRow]) -> list[dict[str, str | int]]:
    counter: Counter[tuple[str, str]] = Counter()
    for row in rows:
        province = row.province or "(unknown)"
        counter[(row.vsic_division, province)] += 1
    out: list[dict[str, str | int]] = []
    for (division, province), n in sorted(counter.items()):
        out.append({"vsic_division": division, "province": province, "n_firms": n})
    return out


class MasothueClient:
    def __init__(
        self,
        *,
        delay_seconds: float = 1.2,
        timeout: float = 30.0,
        max_retries: int = 3,
        client: httpx.Client | None = None,
    ) -> None:
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self._owns = client is None
        self.client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
            },
            trust_env=False,
        )
        self._last_host_at = 0.0

    def close(self) -> None:
        if self._owns:
            self.client.close()

    def __enter__(self) -> MasothueClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_host_at
        wait = self.delay_seconds - elapsed
        if wait > 0:
            time.sleep(wait)

    def get_text(self, url: str) -> str:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self._throttle()
            try:
                response = self.client.get(url)
                self._last_host_at = time.monotonic()
                if response.status_code in {429, 500, 502, 503, 504}:
                    raise httpx.HTTPStatusError(
                        f"retryable status {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                return response.text
            except Exception as exc:  # noqa: BLE001 — network; retry then surface
                last_exc = exc
                logger.warning("GET fail attempt=%s url=%s err=%s", attempt, url, exc)
                time.sleep(min(8.0, self.delay_seconds * attempt * 2))
        assert last_exc is not None
        raise last_exc

    def discover_industries(
        self,
        *,
        divisions: Iterable[str] = DEFAULT_DIVISIONS,
        max_index_pages: int = 40,
    ) -> list[IndustryLink]:
        merged: dict[str, IndustryLink] = {}
        empty_streak = 0
        for page in range(1, max_index_pages + 1):
            url = INDUSTRY_INDEX if page == 1 else f"{INDUSTRY_INDEX}?page={page}"
            html = self.get_text(url)
            batch = parse_industry_index(html, divisions=divisions)
            new = 0
            for link in batch:
                if link.vsic_code not in merged:
                    merged[link.vsic_code] = link
                    new += 1
            logger.info("index page=%s new=%s total=%s", page, new, len(merged))
            if new == 0:
                empty_streak += 1
            else:
                empty_streak = 0
            if empty_streak >= 3 and page >= 5:
                break
        return sorted(merged.values(), key=lambda x: x.vsic_code)

    def harvest_industry(
        self,
        industry: IndustryLink,
        *,
        max_pages: int = 80,
        stop_at: int | None = None,
        seen_taxes: set[str] | None = None,
    ) -> list[FirmRow]:
        seen = seen_taxes if seen_taxes is not None else set()
        rows: list[FirmRow] = []
        first_html = self.get_text(industry.url)
        last_page = min(max_page_from_listing(first_html), max_pages)
        pages_html = {1: first_html}
        for page in range(1, last_page + 1):
            if page == 1:
                html = pages_html[1]
                listing_url = industry.url
            else:
                listing_url = f"{industry.url}?page={page}"
                html = self.get_text(listing_url)
            page_rows = parse_listing_page(
                html,
                vsic_4digit=industry.vsic_code,
                listing_url=listing_url,
            )
            if not page_rows:
                break
            for row in page_rows:
                if row.tax_code in seen:
                    continue
                seen.add(row.tax_code)
                rows.append(row)
                if stop_at is not None and len(seen) >= stop_at:
                    return rows
            logger.info(
                "industry=%s page=%s/%s got=%s unique_total=%s",
                industry.vsic_code,
                page,
                last_page,
                len(page_rows),
                len(seen),
            )
        return rows


def write_frame_csv(path: Path, rows: Iterable[FirmRow]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    materialised = list(rows)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in materialised:
            writer.writerow(asdict(row))
    return len(materialised)


def write_summary_csv(path: Path, rows: Iterable[FirmRow]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = summarize_division_province(rows)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["vsic_division", "province", "n_firms"]
        )
        writer.writeheader()
        writer.writerows(summary)
    return len(summary)


def host_of(url: str) -> str:
    return urlparse(url).netloc
