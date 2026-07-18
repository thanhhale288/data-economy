"""CafeF BCTC HTML adapter for HOSE/HNX listed tickers.

Source page: ``https://s.cafef.vn/{TICKER}/bao-cao-tai-chinh.chn``

Parses the consolidated quarterly statement table (KQKD + balance sheet).
CafeF labels amounts as ``(1.000 VNĐ)`` — we scale ×1000 to VND.
Missing fields stay ``null`` (never invented).
"""

from __future__ import annotations

import logging
import re
from calendar import monthrange
from datetime import date
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CAFEF_BCTC_URL = "https://s.cafef.vn/{ticker}/bao-cao-tai-chinh.chn"

# CafeF table unit: "Kết quả kinh doanh (1.000 VNĐ)" / "Tài sản (1.000 VNĐ)"
UNIT_SCALE = 1_000

# Map CafeF row labels (substring match, first hit wins) → FINANCIAL_FIELDS
LABEL_ALIASES: tuple[tuple[str, str], ...] = (
    ("doanh thu bán hàng", "revenue"),
    ("doanh thu thuần", "revenue"),
    ("giá vốn hàng bán", "cost_of_goods"),
    ("tổng lợi nhuận trước thuế", "profit_before_tax"),
    ("lợi nhuận trước thuế", "profit_before_tax"),
    ("lợi nhuận sau thuế của công ty mẹ", "net_profit"),
    ("lợi nhuận sau thuế", "net_profit"),
    ("tổng tài sản lưu động ngắn hạn", "current_assets"),
    ("tài sản ngắn hạn", "current_assets"),
    ("tổng tài sản", "total_assets"),
    ("nợ ngắn hạn", "current_liabilities"),
    ("vốn chủ sở hữu", "total_equity"),
)

_QUARTER_RE = re.compile(
    r"Quý\s*([1-4])\s*[-–]?\s*(20\d{2})",
    re.IGNORECASE,
)


def cafef_bctc_url(ticker: str) -> str:
    return CAFEF_BCTC_URL.format(ticker=ticker.strip().upper())


def _norm_label(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _parse_cafef_number(raw: str) -> float | None:
    """Parse CafeF cell like ``1.333.355.632`` or ``-12.524.946`` → float (pre-scale)."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text in {"-", "—", "", "Xem đầy đủ"}:
        return None
    neg = text.startswith("(") and text.endswith(")")
    cleaned = text.replace(".", "").replace(",", "").replace(" ", "")
    cleaned = cleaned.replace("(", "").replace(")", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if not cleaned or cleaned == "-":
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if neg or text.startswith("-"):
        # already negative if starts with -
        if text.startswith("-"):
            return value  # float already negative from cleaned? "-12" → cleaned "-12" works
        return -abs(value)
    return value


def _quarter_end(year: int, quarter: int) -> date:
    month = quarter * 3
    return date(year, month, monthrange(year, month)[1])


def _parse_quarter_headers(cells: list[str]) -> list[tuple[int, date] | None]:
    """Return list aligned to value columns: (col_index_in_cells, period_end) or None."""
    out: list[tuple[int, date] | None] = []
    for idx, cell in enumerate(cells):
        m = _QUARTER_RE.search(cell.replace(" ", ""))
        if not m:
            # try with spaces: Quý 2- 2025
            m = _QUARTER_RE.search(cell)
        if not m:
            out.append(None)
            continue
        q, y = int(m.group(1)), int(m.group(2))
        out.append((idx, _quarter_end(y, q)))
    return out


def _map_field(label: str) -> str | None:
    norm = _norm_label(label)
    if not norm:
        return None
    # Avoid matching section headers as total_assets too early
    for alias, field in LABEL_ALIASES:
        if alias in norm:
            # "tổng tài sản lưu động" must win before bare "tổng tài sản"
            return field
    return None


def _pick_column(
    headers: list[tuple[int, date] | None],
    rows: dict[str, list[float | None]],
) -> tuple[int, date] | None:
    """Prefer latest quarter with non-null revenue; else latest with any value."""
    candidates: list[tuple[date, int]] = []
    for item in headers:
        if item is None:
            continue
        col_idx, period = item
        candidates.append((period, col_idx))
    if not candidates:
        return None
    candidates.sort(reverse=True)  # latest period first

    revenue_row = rows.get("revenue")
    if revenue_row is not None:
        for period, col_idx in candidates:
            if col_idx < len(revenue_row) and revenue_row[col_idx] is not None:
                return col_idx, period

    for period, col_idx in candidates:
        for vals in rows.values():
            if col_idx < len(vals) and vals[col_idx] is not None:
                return col_idx, period
    return None


def parse_cafef_bctc_html(
    html: str,
    *,
    stock_code: str,
    source_url: str | None = None,
) -> dict[str, Any]:
    """Parse CafeF BCTC HTML into a financial_reports-shaped dict (VND)."""
    soup = BeautifulSoup(html, "html.parser")
    target = None
    for table in soup.find_all("table"):
        text = table.get_text(" ", strip=True)
        if "Doanh thu bán hàng" in text and "Giá vốn hàng bán" in text:
            target = table
            break
    if target is None:
        raise ValueError("CafeF HTML has no KQKD table")

    header_cells: list[str] | None = None
    field_rows: dict[str, list[float | None]] = {}
    gross_profit_row: list[float | None] | None = None

    for tr in target.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if not cells:
            continue
        label = cells[0]
        if header_cells is None and _QUARTER_RE.search(label.replace(" ", "") + " ".join(cells)):
            # Header row often starts with "Chỉ tiêu..."
            if any(_QUARTER_RE.search(c) for c in cells):
                header_cells = cells
                continue
        if any(_QUARTER_RE.search(c) for c in cells[1:]):
            header_cells = cells
            continue

        norm = _norm_label(label)
        if "lợi nhuận gộp" in norm:
            gross_profit_row = [_parse_cafef_number(c) for c in cells]
            continue

        field = _map_field(label)
        if not field:
            continue
        # First alias wins — skip if already captured (more specific labels come first)
        if field in field_rows:
            continue
        field_rows[field] = [_parse_cafef_number(c) for c in cells]

    if not header_cells:
        raise ValueError("CafeF table missing quarter headers")

    headers = _parse_quarter_headers(header_cells)
    picked = _pick_column(headers, field_rows)
    if picked is None:
        raise ValueError("CafeF table has no usable quarter column")

    col_idx, period = picked
    report: dict[str, Any] = {
        "stock_code": stock_code.upper(),
        "period": period,
        "report_type": "quarterly",
        "source_url": source_url or cafef_bctc_url(stock_code),
        "revenue": None,
        "profit_before_tax": None,
        "net_profit": None,
        "total_assets": None,
        "total_equity": None,
        "current_assets": None,
        "current_liabilities": None,
        "operating_expenses": None,
        "cost_of_goods": None,
        "rental_cost": None,
        "remuneration": None,
        "employees": None,
        "gross_margin": None,
    }

    for field, vals in field_rows.items():
        if col_idx >= len(vals) or vals[col_idx] is None:
            continue
        report[field] = vals[col_idx] * UNIT_SCALE

    # Gross margin from gộp / revenue when both present
    if (
        gross_profit_row
        and col_idx < len(gross_profit_row)
        and gross_profit_row[col_idx] is not None
        and report["revenue"]
    ):
        gp = gross_profit_row[col_idx] * UNIT_SCALE
        report["gross_margin"] = round(gp / report["revenue"], 4)

    if report["revenue"] is None and report["total_assets"] is None:
        raise ValueError("CafeF parse produced no revenue or assets")

    return report


def fetch_cafef_bctc(
    ticker: str,
    *,
    client=None,
    timeout: float = 25.0,
) -> dict[str, Any]:
    """HTTP GET CafeF BCTC page and parse. Raises on failure."""
    import httpx

    url = cafef_bctc_url(ticker)
    owns_client = client is None
    http = client or httpx.Client(timeout=timeout, follow_redirects=True)
    try:
        response = http.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; MfgDataEconomy/1.0; +local-research)"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "vi-VN,vi;q=0.9",
            },
        )
        if response.status_code != 200:
            raise ValueError(f"cafef http {response.status_code}")
        return parse_cafef_bctc_html(
            response.text, stock_code=ticker, source_url=str(response.url)
        )
    finally:
        if owns_client:
            http.close()
