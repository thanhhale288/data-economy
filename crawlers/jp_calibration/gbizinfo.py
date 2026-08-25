"""Public gBizINFO search + profile pages (silver URL / JSIC / employees)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any, Iterable

import httpx
from bs4 import BeautifulSoup

from crawlers.jp_calibration.jsic import is_manufacturing, jsic_division
from crawlers.jp_calibration.paths import (
    DEFAULT_PREFECTURE_CODES,
    PROFILE_CACHE_DIR,
    SEARCH_CACHE_DIR,
)
from crawlers.url_finder.search import BROWSER_UA

logger = logging.getLogger(__name__)

HOME = "https://info.gbiz.go.jp/"
SEARCH = "https://info.gbiz.go.jp/hojin/Search"
PROFILE = "https://info.gbiz.go.jp/hojin/ichiran"

# gBizINFO UI dropdown (Meti.env.js). Align T08 strata with these bands.
STRATA: tuple[dict[str, Any], ...] = (
    {"id": "0-20", "from": 0, "to": 20},
    {"id": "21-50", "from": 21, "to": 50},
    {"id": "51-300", "from": 51, "to": 300},
    {"id": "301+", "from": 301, "to": None},
)

_PROFILE_RE = re.compile(r"submitProfile\('(\d{13})'\)")
_EMP_RE = re.compile(r"従業員数\s*([\d,]+)\s*人")
_INDUSTRY_RE = re.compile(r"業種\s*([^\n（(]{1,40})")
_ADDR_RE = re.compile(r"所在地\s*([^\n（(]{1,80})")
_HOME_RE = re.compile(
    r"(?:企業ホームページ|ホームページ)\s*(https?://[^\s）)]+)",
    re.I,
)
_NAME_RE = re.compile(r"商号または名称\s*([^\n（(]{1,80})")


def _form_fields(html: str) -> dict[str, str]:
    """Map gBizINFO ``return_screen`` hidden state onto the Search POST names."""
    soup = BeautifulSoup(html or "", "html.parser")
    form = soup.find("form", id="return_screen")
    raw: dict[str, str] = {}
    if form is None:
        return raw
    for el in form.find_all("input"):
        name = el.get("name")
        if name:
            raw[name] = el.get("value") or ""
    mapped = {
        "activeSearchTab": raw.get("activeSearchTab") or "detail",
        "gamenSeniFlg": raw.get("gamenSeniFlg") or "false",
        "gamen": raw.get("gamen") or "2",
        "hojinShubetsu": raw.get("hojinShubetsu") or "301",
        "ShozaichiTodofuken": raw.get("shozaichiTodofuken") or "",
        "gyoshu": raw.get("gyoshu") or "E",
        "gyoShuCodeHidden": raw.get("gyoShuCodeHidden") or raw.get("gyoshu") or "E",
        "JugyoinsuFrom": raw.get("jugyoinsuFrom") or "",
        "pageKensuHidden": raw.get("pageKensuHidden") or "50",
        "sortKeyHidden": raw.get("sortKeyHidden") or "corporateName",
        "sortTypeHidden": raw.get("sortTypeHidden") or "up",
        "searchTypeHidden": "changePage",
    }
    if raw.get("jugyoinsuTo"):
        mapped["JugyoinsuTo"] = raw["jugyoinsuTo"]
    return mapped


def employee_stratum(n: int | None) -> str:
    if n is None:
        return "unknown"
    if n <= 20:
        return "0-20"
    if n <= 50:
        return "21-50"
    if n <= 300:
        return "51-300"
    return "301+"


def parse_employee_count(raw: str | None) -> int | None:
    digits = re.sub(r"[^\d]", "", raw or "")
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


class GbizInfoClient:
    def __init__(
        self,
        *,
        delay_seconds: float = 0.4,
        client: httpx.Client | None = None,
    ) -> None:
        self.delay_seconds = delay_seconds
        self._owns = client is None
        self.client = client or httpx.Client(
            timeout=60.0,
            follow_redirects=True,
            headers={"User-Agent": BROWSER_UA, "Accept-Language": "ja,en;q=0.8"},
            trust_env=False,
        )
        self._last_at = 0.0
        self._homed = False

    def close(self) -> None:
        if self._owns:
            self.client.close()

    def __enter__(self) -> GbizInfoClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _throttle(self) -> None:
        wait = self.delay_seconds - (time.monotonic() - self._last_at)
        if wait > 0:
            time.sleep(wait)

    def _home(self) -> None:
        if self._homed:
            return
        self._throttle()
        response = self.client.get(HOME)
        self._last_at = time.monotonic()
        response.raise_for_status()
        self._homed = True

    def search_cell(
        self,
        *,
        prefecture: str,
        prefecture_code: str,
        stratum: dict[str, Any],
        max_pages: int = 20,
    ) -> list[dict[str, str]]:
        """One prefecture × employee band × JSIC E × 株式会社. Public search UI."""
        cache_key = f"{prefecture_code}-{stratum['id']}"
        cache_path = SEARCH_CACHE_DIR / f"{cache_key}.json"
        if cache_path.exists():
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return payload
        self._home()
        data = {
            "activeSearchTab": "detail",
            "gamenSeniFlg": "false",
            "gamen": "1",
            "hojinShubetsu": "301",
            "ShozaichiTodofuken": prefecture_code,
            "ShozaichiTodofukenTextHidden": prefecture,
            "gyoshu": "E",
            "gyoShuCodeHidden": "E",
            "gyoShuTextHidden": "製造業",
            "JugyoinsuFrom": str(stratum["from"]),
            "pageHidden": "1",
            "pageKensuHidden": "50",
        }
        if stratum["to"] is not None:
            data["JugyoinsuTo"] = str(stratum["to"])
        rows: list[dict[str, str]] = []
        seen: set[str] = set()
        html = ""
        for page in range(1, max_pages + 1):
            self._throttle()
            if page == 1:
                response = self.client.post(SEARCH, data=data)
            else:
                page_data = _form_fields(html)
                page_data["pageHidden"] = str(page)
                page_data["searchTypeHidden"] = "changePage"
                page_data["gamenSeniFlg"] = "false"
                response = self.client.post(SEARCH, data=page_data)
            self._last_at = time.monotonic()
            response.raise_for_status()
            html = response.text
            page_rows = parse_search_results(html, prefecture=prefecture, stratum=stratum["id"])
            new = 0
            for row in page_rows:
                number = row["corporate_number"]
                if number in seen:
                    continue
                seen.add(number)
                rows.append(row)
                new += 1
            logger.info(
                "gBizINFO search %s %s page=%s +%s (total %s)",
                prefecture,
                stratum["id"],
                page,
                new,
                len(rows),
            )
            if new == 0 or len(page_rows) < 50:
                break
        SEARCH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return rows

    def fetch_profile(self, corporate_number: str) -> dict[str, Any]:
        number = corporate_number.strip()
        cache_path = PROFILE_CACHE_DIR / f"{number}.html"
        if cache_path.exists():
            html = cache_path.read_text(encoding="utf-8", errors="replace")
            parsed = parse_profile(html, corporate_number=number)
            parsed["profile_cache"] = "disk"
            return parsed
        self._home()
        self._throttle()
        response = self.client.get(PROFILE, params={"hojinBango": number})
        self._last_at = time.monotonic()
        response.raise_for_status()
        PROFILE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(response.text, encoding="utf-8", errors="replace")
        parsed = parse_profile(response.text, corporate_number=number)
        parsed["profile_cache"] = "live"
        return parsed


def parse_search_results(
    html: str, *, prefecture: str, stratum: str
) -> list[dict[str, str]]:
    soup = BeautifulSoup(html or "", "html.parser")
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href") or ""
        match = _PROFILE_RE.search(href)
        if not match:
            continue
        number = match.group(1)
        if number in seen:
            continue
        seen.add(number)
        out.append(
            {
                "corporate_number": number,
                "legal_name": a.get_text(" ", strip=True),
                "prefecture": prefecture,
                "search_stratum": stratum,
            }
        )
    return out


def parse_profile(html: str, *, corporate_number: str) -> dict[str, Any]:
    soup = BeautifulSoup(html or "", "html.parser")
    text = soup.get_text("\n", strip=True)
    url = ""
    home = _HOME_RE.search(text)
    if home:
        url = home.group(1).rstrip("。、,")
    if not url:
        for a in soup.find_all("a", href=True):
            href = a.get("href") or ""
            if href.startswith("http") and "gbiz.go.jp" not in href and "nta.go.jp" not in href:
                label = a.get_text(" ", strip=True)
                if href.startswith("http") and (
                    "http" in (label or href) or "www." in href
                ):
                    if any(
                        skip in href
                        for skip in (
                            "houjin-bangou",
                            "edinet",
                            "shokuba.mhlw",
                            "p-portal.go.jp",
                            "nenkin.go.jp",
                            "meti.go.jp",
                            "wikipedia",
                        )
                    ):
                        continue
                    url = href
                    break
    industry = ""
    ind = _INDUSTRY_RE.search(text)
    if ind:
        industry = ind.group(1).strip()
    employees = None
    emp = _EMP_RE.search(text)
    if emp:
        employees = parse_employee_count(emp.group(1))
    address = ""
    addr = _ADDR_RE.search(text)
    if addr:
        address = addr.group(1).strip()
    name = ""
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if "|" in title:
        name = title.split("|", 1)[0].strip()
    named = _NAME_RE.search(text)
    if named:
        name = named.group(1).strip() or name
    return {
        "corporate_number": corporate_number,
        "legal_name": name,
        "address": address,
        "jsic_raw": industry,
        "jsic_division": jsic_division(industry),
        "is_manufacturing": is_manufacturing(industry),
        "employee_number": employees,
        "employee_stratum": employee_stratum(employees),
        "company_url": url,
        "source_dataset": "gbizinfo_profile",
    }


def search_pool(
    prefectures: Iterable[str] = DEFAULT_PREFECTURE_CODES.keys(),
    *,
    client: GbizInfoClient | None = None,
) -> list[dict[str, str]]:
    owns = client is None
    gbiz = client or GbizInfoClient()
    try:
        rows: list[dict[str, str]] = []
        for pref in prefectures:
            code = DEFAULT_PREFECTURE_CODES[pref]
            for stratum in STRATA:
                rows.extend(
                    gbiz.search_cell(
                        prefecture=pref, prefecture_code=code, stratum=stratum
                    )
                )
        return rows
    finally:
        if owns:
            gbiz.close()


def cache_fingerprint(rows: list[dict[str, Any]]) -> str:
    raw = json.dumps(rows, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
