"""Google Form export → locked 18-column survey CSV. Never invent answers."""

from __future__ import annotations

import csv
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from crawlers.survey_join.paths import SURVEY_COLUMNS

logger = logging.getLogger(__name__)

KNOWN_BINS = frozenset(
    {"zero", "lt5", "5to10", "10to25", "25to50", "gt50", "unknown", "refuse"}
)
PAYMENT_ORDER = ("vnpay", "momo", "cod", "other", "none")
MARKETPLACE_ORDER = ("Shopee", "TikTok Shop", "Lazada", "khác")

# Exact Google Form titles from docs/lab/KHAO-SAT-DOANH-NGHIEP.md §5.
FORM_TITLES: tuple[tuple[str, str], ...] = (
    ("Tên doanh nghiệp", "company_name"),
    ("Mã số thuế (giữ hậu tố chi nhánh nếu có)", "mst"),
    ("Mã VSIC 4 số (nếu biết)", "vsic_4digit"),
    ("Mã chứng khoán (nếu có)", "ticker"),
    ("Doanh nghiệp có website riêng không?", "has_website"),
    ("Địa chỉ website", "website_url_self_report"),
    ("Website có danh mục sản phẩm để xem không?", "has_product_catalog"),
    ("Có giỏ / đặt hàng trên chính website không? (không tính chỉ nút ra sàn)", "has_order_cart"),
    ("Phương thức thanh toán hiển thị trên website", "payment_methods"),
    ("Doanh nghiệp có kênh mạng xã hội chính thức không?", "has_social_links"),
    ("Doanh nghiệp có gian hàng trên sàn không?", "has_marketplace_links"),
    ("Tên sàn (nếu có)", "marketplace_names"),
    ("Khoảng % doanh thu trực tuyến (năm tài chính gần nhất)", "online_revenue_share_bin"),
    ("Năm tài chính vừa khai", "revenue_year"),
    ("Doanh thu năm đó (VND, số nguyên)", "revenue_vnd"),
    ("Vai trò người trả lời", "respondent_role"),
    ("Email (không bắt buộc)", "respondent_email"),
    ("Ghi chú", "notes"),
)

# Distinctive substrings (Vietnamese + English locked ids). Longer needles win.
COLUMN_NEEDLES: dict[str, tuple[str, ...]] = {
    "mst": (
        "mã số thuế",
        "ma so thue",
        "giữ hậu tố chi nhánh",
        "giu hau to chi nhanh",
        "tax code",
        "mst",
    ),
    "company_name": (
        "company_name",
        "tên doanh nghiệp",
        "ten doanh nghiep",
        "company name",
    ),
    "vsic_4digit": (
        "vsic_4digit",
        "mã vsic",
        "ma vsic",
        "vsic 4",
        "vsic",
    ),
    "ticker": (
        "ticker",
        "mã chứng khoán",
        "ma chung khoan",
        "mã cổ phiếu",
        "ma co phieu",
    ),
    "website_url_self_report": (
        "website_url_self_report",
        "địa chỉ website",
        "dia chi website",
        "website url",
    ),
    "has_website": (
        "has_website",
        "website riêng không",
        "website rieng khong",
        "có website riêng",
        "co website rieng",
        "website riêng",
        "website rieng",
    ),
    "has_product_catalog": (
        "has_product_catalog",
        "danh mục sản phẩm",
        "danh muc san pham",
        "product catalog",
    ),
    "has_order_cart": (
        "has_order_cart",
        "đặt hàng trên chính website",
        "dat hang tren chinh website",
        "giỏ / đặt hàng",
        "gio / dat hang",
        "giỏ hàng",
        "gio hang",
        "order cart",
    ),
    "payment_methods": (
        "payment_methods",
        "phương thức thanh toán",
        "phuong thuc thanh toan",
        "thanh toán hiển thị",
        "thanh toan hien thi",
    ),
    "has_social_links": (
        "has_social_links",
        "mạng xã hội",
        "mang xa hoi",
        "social links",
    ),
    "has_marketplace_links": (
        "has_marketplace_links",
        "gian hàng trên sàn không",
        "gian hang tren san khong",
        "có gian hàng trên sàn",
        "co gian hang tren san",
        "gian hàng trên sàn",
        "gian hang tren san",
    ),
    "marketplace_names": (
        "marketplace_names",
        "tên sàn",
        "ten san",
    ),
    "online_revenue_share_bin": (
        "online_revenue_share_bin",
        "khoảng % doanh thu",
        "khoang % doanh thu",
        "khoảng tỷ trọng",
        "khoang ty trong",
        "doanh thu trực tuyến",
        "doanh thu truc tuyen",
    ),
    "revenue_year": (
        "revenue_year",
        "năm tài chính vừa khai",
        "nam tai chinh vua khai",
        "vừa khai",
        "vua khai",
    ),
    "revenue_vnd": (
        "revenue_vnd",
        "doanh thu năm đó",
        "doanh thu nam do",
        "vnd, số nguyên",
        "vnd, so nguyen",
        "số nguyên",
        "so nguyen",
    ),
    "respondent_role": (
        "respondent_role",
        "vai trò người trả lời",
        "vai tro nguoi tra loi",
        "vai trò",
        "vai tro",
    ),
    "respondent_email": (
        "respondent_email",
        "email",
    ),
    "notes": (
        "notes",
        "ghi chú",
        "ghi chu",
    ),
}

_BIN_LABELS: tuple[tuple[str, str], ...] = (
    ("tren 0% den duoi 5%", "lt5"),
    ("5% den duoi 10%", "5to10"),
    ("10% den duoi 25%", "10to25"),
    ("25% den duoi 50%", "25to50"),
    ("50% tro len", "gt50"),
    ("0%", "zero"),
    ("khong tien tra loi", "refuse"),
    ("khong biet", "unknown"),
    ("refuse", "refuse"),
    ("unknown", "unknown"),
)

_REVENUE_REFUSE = frozenset(
    {
        "khong tien tra loi",
        "khong biet",
        "khong muon tra loi",
        "refuse",
        "unknown",
        "n/a",
        "na",
        "null",
    }
)

_TRI_TRUE = frozenset({"co", "true", "yes", "y", "1"})
_TRI_FALSE = frozenset({"khong", "false", "no", "n", "0"})
_TRI_UNKNOWN = frozenset({"khong biet", "unknown", "na", "n/a", "null", "k biet"})

_HAS_WEBSITE_BOOLS = ("has_product_catalog", "has_order_cart", "has_social_links", "has_marketplace_links")


class RecodeError(ValueError):
    """Missing/empty file or no mappable MST header — never invent rows."""


@dataclass
class RecodeResult:
    rows: list[dict[str, str]]
    skipped: list[dict[str, str]] = field(default_factory=list)
    header_map: dict[str, str] = field(default_factory=dict)
    source: Path | None = None
    dest: Path | None = None


def _fold(text: Any) -> str:
    raw = str(text or "").strip().replace("đ", "d").replace("Đ", "d")
    raw = unicodedata.normalize("NFD", raw)
    raw = "".join(ch for ch in raw if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", raw).lower()


def _is_dropped_header(folded: str) -> bool:
    if not folded:
        return True
    if folded == "timestamp" or folded.startswith("timestamp"):
        return True
    if "dong y" in folded:
        return True
    if "consent" in folded:
        return True
    return False


def normalize_mst(raw: Any) -> str:
    """Strip all whitespace; keep hyphen branch suffix and leading zeros as text."""
    if raw is None:
        return ""
    return "".join(str(raw).split())


def recode_tri_state(raw: Any) -> str:
    """Có/Không/Không biết → true/false/unknown. Empty if unrecognized."""
    folded = _fold(raw)
    if not folded:
        return ""
    if folded in _TRI_TRUE:
        return "true"
    if folded in _TRI_UNKNOWN:
        return "unknown"
    if folded in _TRI_FALSE:
        return "false"
    return ""


def recode_bin(raw: Any) -> str:
    """Câu 13 labels → locked bin codes; already-coded bins pass through."""
    folded = _fold(raw)
    if not folded:
        return ""
    compact = folded.replace(" ", "")
    if folded in KNOWN_BINS or compact in KNOWN_BINS:
        return folded if folded in KNOWN_BINS else compact
    for label, code in _BIN_LABELS:
        label_compact = label.replace(" ", "")
        if folded == label or compact == label_compact:
            return code
        if folded.startswith(label) or compact.startswith(label_compact):
            return code
    return ""


def recode_payment_methods(raw: Any) -> str:
    """VNPay/MoMo/COD/Cổng/Không nhận thanh toán → comma-joined tokens."""
    text = str(raw or "").strip()
    if not text:
        return ""
    found: set[str] = set()
    has_none = False
    for part in re.split(r"[,;]", text):
        folded = _fold(part)
        if not folded:
            continue
        if "khong nhan thanh toan" in folded or folded == "none":
            has_none = True
            continue
        if "vnpay" in folded:
            found.add("vnpay")
        elif "momo" in folded:
            found.add("momo")
        elif folded == "cod" or folded.startswith("cod ") or "thanh toan khi nhan hang" in folded:
            found.add("cod")
        elif "cach khac" in folded or folded == "other" or "cong" in folded:
            found.add("other")
    if has_none:
        return "none"
    return ",".join(token for token in PAYMENT_ORDER if token in found)


def recode_marketplace_names(raw: Any) -> str:
    """Keep Shopee / TikTok Shop / Lazada / khác (comma-joined, no extra spaces)."""
    text = str(raw or "").strip()
    if not text:
        return ""
    found: set[str] = set()
    for part in re.split(r"[,;]", text):
        folded = _fold(part)
        if not folded:
            continue
        if "shopee" in folded:
            found.add("Shopee")
        elif "tiktok" in folded:
            found.add("TikTok Shop")
        elif "lazada" in folded:
            found.add("Lazada")
        elif folded in {"khac", "other"} or folded.startswith("khac"):
            found.add("khác")
    return ",".join(name for name in MARKETPLACE_ORDER if name in found)


def recode_revenue_vnd(raw: Any) -> str:
    """Digits only; empty if refuse/unknown text; write 0 only when the cell is 0."""
    text = str(raw or "").strip()
    if not text:
        return ""
    folded = _fold(text)
    if folded in _REVENUE_REFUSE or "khong tien tra loi" in folded:
        return ""
    if folded in {"khong biet", "unknown", "refuse"}:
        return ""
    compact = re.sub(r"\s+", "", text)
    if compact in {"0", "0.0", "0,0"}:
        return "0"
    digits = re.sub(r"\D", "", text)
    if not digits:
        return ""
    if set(digits) <= {"0"}:
        return "0"
    return digits.lstrip("0") or "0"


def _needle_hits(folded_header: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for column, needles in COLUMN_NEEDLES.items():
        best = 0
        for needle in needles:
            folded_needle = _fold(needle)
            if not folded_needle:
                continue
            if folded_needle in folded_header or folded_header == folded_needle:
                best = max(best, len(folded_needle))
        if best:
            hits.append((best, column))
    hits.sort(reverse=True)
    return hits


def map_headers(fieldnames: Sequence[str | None]) -> dict[str, str]:
    """Map locked column id → original source header.

    Extra Timestamp / Đồng ý columns are dropped. Raises if ``mst`` cannot be mapped.
    """
    originals = [h for h in fieldnames if h is not None and str(h).strip()]
    stripped = [str(h).strip() for h in originals]
    locked_set = set(SURVEY_COLUMNS)
    if locked_set <= set(stripped):
        by_stripped = {str(h).strip(): h for h in originals}
        return {col: by_stripped[col] for col in SURVEY_COLUMNS}

    folded_titles = {_fold(title): col for title, col in FORM_TITLES}
    claimed_sources: set[str] = set()
    mapping: dict[str, str] = {}
    scored: list[tuple[int, str, str]] = []  # score, column, source header

    for original in originals:
        folded = _fold(original)
        if _is_dropped_header(folded):
            continue
        exact_locked = str(original).strip()
        if exact_locked in locked_set and exact_locked not in mapping:
            mapping[exact_locked] = original
            claimed_sources.add(original)
            continue
        title_col = folded_titles.get(folded)
        if title_col and title_col not in mapping:
            mapping[title_col] = original
            claimed_sources.add(original)
            continue
        hits = _needle_hits(folded)
        if hits:
            scored.append((hits[0][0], hits[0][1], original))

    scored.sort(key=lambda item: (-item[0], SURVEY_COLUMNS.index(item[1]) if item[1] in SURVEY_COLUMNS else 99))
    for _score, column, original in scored:
        if column in mapping or original in claimed_sources:
            continue
        mapping[column] = original
        claimed_sources.add(original)

    if "mst" not in mapping:
        raise RecodeError(
            "no mappable header for mst (need MST / 'Mã số thuế' column); "
            f"got: {', '.join(stripped) or '(none)'}"
        )
    return mapping


def recode_row(raw_values: dict[str, Any]) -> tuple[dict[str, str] | None, str | None]:
    """Recode one already-mapped row (locked ids → raw cells).

    Returns ``(row, None)`` or ``(None, recode_error reason)``. Missing/invalid
    ``has_website`` skips the row rather than inventing true/false.
    """
    mst = normalize_mst(raw_values.get("mst"))
    has_website = recode_tri_state(raw_values.get("has_website"))
    if has_website not in {"true", "false"}:
        if not str(raw_values.get("has_website") or "").strip():
            return None, "missing_has_website"
        return None, "invalid_has_website"
    if not mst:
        return None, "missing_mst"

    ticker_raw = str(raw_values.get("ticker") or "").strip()
    vsic_raw = str(raw_values.get("vsic_4digit") or "").strip()
    year_raw = str(raw_values.get("revenue_year") or "").strip()

    row = {col: "" for col in SURVEY_COLUMNS}
    row["mst"] = mst
    row["company_name"] = str(raw_values.get("company_name") or "").strip()
    row["vsic_4digit"] = vsic_raw
    row["ticker"] = ticker_raw.upper()
    row["website_url_self_report"] = str(raw_values.get("website_url_self_report") or "").strip()
    row["has_website"] = has_website
    for col in _HAS_WEBSITE_BOOLS:
        row[col] = recode_tri_state(raw_values.get(col))
    row["payment_methods"] = recode_payment_methods(raw_values.get("payment_methods"))
    row["marketplace_names"] = recode_marketplace_names(raw_values.get("marketplace_names"))
    row["online_revenue_share_bin"] = recode_bin(raw_values.get("online_revenue_share_bin"))
    row["revenue_vnd"] = recode_revenue_vnd(raw_values.get("revenue_vnd"))
    row["revenue_year"] = year_raw
    row["respondent_role"] = str(raw_values.get("respondent_role") or "").strip()
    row["respondent_email"] = str(raw_values.get("respondent_email") or "").strip()
    row["notes"] = str(raw_values.get("notes") or "").strip()
    return row, None


def _mapped_values(record: dict[str, Any], header_map: dict[str, str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for col in SURVEY_COLUMNS:
        source = header_map.get(col)
        if source is None:
            values[col] = ""
        else:
            values[col] = record.get(source, "")
    return values


def recode_records(
    fieldnames: Sequence[str | None],
    records: Iterable[dict[str, Any]],
) -> RecodeResult:
    """Recode in-memory rows. File-level MST header errors still raise."""
    header_map = map_headers(fieldnames)
    rows: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for index, record in enumerate(records, start=2):
        mapped = _mapped_values(record, header_map)
        recoded, error = recode_row(mapped)
        if error is not None:
            mst = normalize_mst(mapped.get("mst"))
            skipped.append(
                {
                    "row_number": str(index),
                    "mst": mst,
                    "recode_error": error,
                }
            )
            logger.warning(
                "recode_error skip row_number=%s mst=%s reason=%s",
                index,
                mst or "(empty)",
                error,
            )
            continue
        assert recoded is not None
        rows.append(recoded)
    return RecodeResult(rows=rows, skipped=skipped, header_map=header_map)


def _write_locked_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SURVEY_COLUMNS), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in SURVEY_COLUMNS})


def recode_survey_csv(source: Path, dest: Path | None = None) -> RecodeResult:
    """Read a Google Form export (or already-locked CSV) and recode to SURVEY_COLUMNS.

    Writes ``dest`` when given. Does not create ``data/processed/survey/`` unless
    that path is passed in as ``dest``.
    """
    source = Path(source)
    if not source.exists():
        raise RecodeError(f"survey file not found: {source}")
    raw = source.read_text(encoding="utf-8")
    if not raw.strip():
        raise RecodeError(f"survey file is empty: {source}")
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise RecodeError(f"survey file has no header: {source}")
        result = recode_records(reader.fieldnames, reader)
    result.source = source
    if dest is not None:
        dest = Path(dest)
        _write_locked_csv(dest, result.rows)
        result.dest = dest
    return result
