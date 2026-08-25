"""Download and parse 国税庁法人番号公表サイト prefecture CSVs (no token)."""

from __future__ import annotations

import csv
import io
import logging
import re
import zipfile
from pathlib import Path
from typing import Any, Iterable

import httpx
from bs4 import BeautifulSoup

from crawlers.jp_calibration.paths import (
    DEFAULT_PREFECTURES,
    NTA_CSV_DIR,
    NTA_INDEX_FILE,
    NTA_ZIP_DIR,
)
from crawlers.url_finder.identity import utcnow_iso, write_json
from crawlers.url_finder.search import BROWSER_UA

logger = logging.getLogger(__name__)

ZENKEN_URL = "https://www.houjin-bangou.nta.go.jp/download/zenken/index.html"
TOKEN_NAME = (
    "jp.go.nta.houjin_bangou.framework.web.common.CNSFWTokenProcessor.request.token"
)
KIND_COMPANY = frozenset({"301", "302", "305"})  # KK / YK / GK

# Resource definition (no header). Indices are 0-based.
COL_CORPORATE_NUMBER = 1
COL_NAME = 6
COL_KIND = 8
COL_PREFECTURE = 9
COL_CITY = 10
COL_STREET = 11
COL_PREFECTURE_CODE = 13
COL_CLOSE_DATE = 18
COL_LATEST = 23
COL_EN_NAME = 24
COL_FURIGANA = 28
COL_HIHYOJI = 29


def parse_zenken_index(html: str) -> list[dict[str, str]]:
    """Unicode CSV file numbers keyed by prefecture (ids change every month)."""
    soup = BeautifulSoup(html or "", "html.parser")
    current = ""
    rows: list[dict[str, str]] = []
    for el in soup.find_all(["h2", "h3", "a"]):
        if el.name in {"h2", "h3"}:
            current = el.get_text(" ", strip=True)
            continue
        onclick = el.get("onclick") or ""
        if "doDownload" not in onclick or "Unicode" not in current or "CSV" not in current:
            continue
        if "XML" in current:
            continue
        match = re.search(r"doDownload\((\d+)\)", onclick)
        if not match:
            continue
        dd = el.find_parent("dd")
        dt = dd.find_previous("dt") if dd else None
        pref = dt.get_text(" ", strip=True) if dt else ""
        rows.append(
            {
                "section": current,
                "prefecture": pref,
                "file_no": match.group(1),
                "label": el.get_text(" ", strip=True),
            }
        )
    return rows


def download_prefecture_zips(
    prefectures: Iterable[str] = DEFAULT_PREFECTURES,
    *,
    client: httpx.Client | None = None,
) -> list[Path]:
    NTA_ZIP_DIR.mkdir(parents=True, exist_ok=True)
    owns = client is None
    http = client or httpx.Client(
        timeout=120.0,
        follow_redirects=True,
        headers={"User-Agent": BROWSER_UA},
        trust_env=False,
    )
    try:
        page = http.get(ZENKEN_URL)
        page.raise_for_status()
        index = parse_zenken_index(page.text)
        write_json(NTA_INDEX_FILE, [{**row, "retrieved_at": utcnow_iso()} for row in index])
        wanted = {p.strip() for p in prefectures}
        chosen = [row for row in index if row["prefecture"] in wanted]
        if not chosen:
            raise RuntimeError(
                f"NTA zenken index had no Unicode CSV for {sorted(wanted)}. "
                "The monthly file numbers may have moved; inspect nta_index.json."
            )
        soup = BeautifulSoup(page.text, "html.parser")
        token_el = soup.find("input", attrs={"name": TOKEN_NAME})
        token = token_el.get("value") if token_el else ""
        paths: list[Path] = []
        for row in chosen:
            dest = NTA_ZIP_DIR / f"{row['file_no']}_{row['prefecture']}.zip"
            if dest.exists() and dest.stat().st_size > 1000:
                logger.info("NTA zip cached %s", dest.name)
                paths.append(dest)
                continue
            logger.info("Downloading NTA %s file_no=%s", row["prefecture"], row["file_no"])
            response = http.post(
                ZENKEN_URL,
                data={
                    TOKEN_NAME: token,
                    "event": "download",
                    "selDlFileNo": row["file_no"],
                },
            )
            response.raise_for_status()
            ctype = response.headers.get("content-type", "")
            if "zip" not in ctype.lower() and not response.content.startswith(b"PK"):
                raise RuntimeError(
                    f"NTA download for {row['prefecture']} did not return a zip "
                    f"(content-type={ctype!r}, {len(response.content)} bytes)"
                )
            dest.write_bytes(response.content)
            paths.append(dest)
        return paths
    finally:
        if owns:
            http.close()


def extract_csvs(zip_paths: Iterable[Path]) -> list[Path]:
    NTA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for zpath in zip_paths:
        with zipfile.ZipFile(zpath) as zf:
            for info in zf.infolist():
                if not info.filename.lower().endswith(".csv"):
                    continue
                dest = NTA_CSV_DIR / Path(info.filename).name
                dest.write_bytes(zf.read(info))
                out.append(dest)
    return out


def parse_nta_csv(path: Path) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    rows: list[dict[str, Any]] = []
    reader = csv.reader(io.StringIO(text))
    for cells in reader:
        if len(cells) <= COL_LATEST:
            continue
        if cells[COL_LATEST] != "1":
            continue
        if (cells[COL_CLOSE_DATE] or "").strip():
            continue
        if len(cells) > COL_HIHYOJI and cells[COL_HIHYOJI] == "1":
            continue
        kind = (cells[COL_KIND] or "").strip()
        if kind not in KIND_COMPANY:
            continue
        number = (cells[COL_CORPORATE_NUMBER] or "").strip()
        if len(number) != 13 or not number.isdigit():
            continue
        name = (cells[COL_NAME] or "").strip()
        pref = (cells[COL_PREFECTURE] or "").strip()
        city = (cells[COL_CITY] or "").strip()
        street = (cells[COL_STREET] or "").strip()
        rows.append(
            {
                "corporate_number": number,
                "legal_name": name,
                "kind": kind,
                "prefecture": pref,
                "city": city,
                "address": f"{pref}{city}{street}",
                "prefecture_code": (cells[COL_PREFECTURE_CODE] or "").strip(),
                "en_name": (cells[COL_EN_NAME] or "").strip()
                if len(cells) > COL_EN_NAME
                else "",
                "furigana": (cells[COL_FURIGANA] or "").strip()
                if len(cells) > COL_FURIGANA
                else "",
                "source_dataset": "nta_houjin_bangou",
            }
        )
    return rows


def load_nta_frame(csv_paths: Iterable[Path] | None = None) -> dict[str, dict[str, Any]]:
    paths = list(csv_paths) if csv_paths is not None else sorted(NTA_CSV_DIR.glob("*.csv"))
    out: dict[str, dict[str, Any]] = {}
    for path in paths:
        for row in parse_nta_csv(path):
            out[row["corporate_number"]] = row
    return out
