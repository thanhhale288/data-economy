"""BCTC extract → BenchmarkInput-compatible fields (Tasks #52/#53).

Rules-first mapper over digital-text PDF (pdfplumber) with OCR fallback for
scan/image inputs (PaddleOCR, optional). Missing / ambiguous values stay
``null`` with warnings — never invent numbers. No DB writes, no API.

Number conventions (same as #52):
- VN thousands: ``.`` (e.g. ``5.200.000``); western ``,`` also accepted
- Unit markers ``nghìn`` / ``1.000 VND`` → ×1_000; ``triệu`` → ×1_000_000
- Default: full VND (CafeF prefill parity); ``employees`` never scaled
"""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO

import pdfplumber

# BenchmarkInput keys this spike targets (plan "equity" → schema ``total_equity``).
EXTRACT_FIELDS: tuple[str, ...] = (
    "operating_revenue",
    "profit_before_tax",
    "employees",
    "total_assets",
    "total_equity",
)

# Longer / more specific aliases first (substring match on folded labels).
# Folded = lowercased + Vietnamese diacritics stripped.
_LABEL_ALIASES: tuple[tuple[str, str], ...] = (
    ("tong loi nhuan truoc thue", "profit_before_tax"),
    ("loi nhuan truoc thue", "profit_before_tax"),
    ("doanh thu ban hang va cung cap dich vu", "operating_revenue"),
    ("doanh thu ban hang va ccdv", "operating_revenue"),
    ("doanh thu ban hang", "operating_revenue"),
    ("doanh thu thuan", "operating_revenue"),
    ("doanh thu hoat dong", "operating_revenue"),
    ("tong tai san luu dong ngan han", "current_assets"),  # avoid stealing total_assets
    ("tai san ngan han", "current_assets"),
    ("tong tai san", "total_assets"),
    ("von chu so huu", "total_equity"),
    ("so lao dong binh quan", "employees"),
    ("lao dong binh quan", "employees"),
    ("so lao dong", "employees"),
    ("so nhan vien", "employees"),
    ("nhan vien", "employees"),
)

_UNIT_NGHIN_RE = re.compile(
    r"(1\.000\s*vn[đd]|ngh[iì]n\s*(vn[đd]|dong)|ngan\s*(vn[đd]|dong))",
    re.IGNORECASE,
)
_UNIT_TRIEU_RE = re.compile(r"tri[eệ]u\s*(vn[đd]|dong)", re.IGNORECASE)

# Trailing amount on a line: VN dots, western commas, plain digits, optional parens.
_AMOUNT_RE = re.compile(
    r"(?<![\w.])"  # not mid-word
    r"(\(?-?(?:\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,]\d+)?\)?)"
    r"(?![\w.])"
)

# PDF text below this → treat as scan and fall back to OCR (router only).
MIN_PDF_TEXT_CHARS = 50

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
_PDF_SUFFIXES = {".pdf"}


@dataclass
class BctcExtractResult:
    """Extract payload for future ``POST /api/benchmark/extract`` (#54)."""

    fields: dict[str, float | int | None]
    confidence: dict[str, float]
    warnings: list[str] = field(default_factory=list)
    source_type: str = "pdf_text"

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": dict(self.fields),
            "confidence": dict(self.confidence),
            "warnings": list(self.warnings),
            "source_type": self.source_type,
        }


def _fold(text: str) -> str:
    """Lowercase + strip Vietnamese diacritics for alias matching."""
    norm = unicodedata.normalize("NFD", (text or "").strip().lower())
    return "".join(c for c in norm if unicodedata.category(c) != "Mn")


def _norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def parse_vn_number(raw: str) -> float | None:
    """Parse VN/western formatted amounts; parentheses → negative. No invent."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text in {"-", "—", "–", "n/a", "N/A"}:
        return None
    neg = text.startswith("(") and text.endswith(")")
    cleaned = text.replace(" ", "").replace("(", "").replace(")", "")
    if not cleaned or cleaned in {"-", "—", "–"}:
        return None
    # VN thousands use '.'; western use ','. If both, assume '.' thousands + ',' decimal.
    if "." in cleaned and "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")
    elif cleaned.count(",") > 1:
        cleaned = cleaned.replace(",", "")
    elif cleaned.count(",") == 1 and cleaned.count(".") == 0:
        # Ambiguous single comma: treat as thousands if 3 digits after, else decimal.
        left, right = cleaned.split(",")
        cleaned = left + right if len(right) == 3 else f"{left}.{right}"
    elif cleaned.count(".") == 1 and cleaned.count(",") == 0:
        left, right = cleaned.split(".")
        if len(right) == 3 and left.isdigit():
            cleaned = left + right  # 1.234 → thousands
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if neg:
        return -abs(value)
    return value


def _map_label(label: str) -> str | None:
    folded = _fold(_norm_ws(label))
    if not folded:
        return None
    for alias, field_name in _LABEL_ALIASES:
        if alias in folded:
            return field_name
    return None


def _detect_unit_scale(full_text: str) -> tuple[int, str | None]:
    """Return (scale_to_vnd, warning_or_none). Default 1 = already VND."""
    folded = _fold(full_text)
    if _UNIT_TRIEU_RE.search(full_text) or "trieu vnd" in folded or "trieu dong" in folded:
        return 1_000_000, "unit_detected_million_vnd"
    if _UNIT_NGHIN_RE.search(full_text) or "1.000 vnd" in folded:
        return 1_000, "unit_detected_thousand_vnd"
    return 1, None


def _extract_amount_from_line(line: str) -> float | None:
    """Pick the rightmost plausible amount on a label+value line."""
    matches = list(_AMOUNT_RE.finditer(line))
    if not matches:
        return None
    # Skip tiny integers that look like row indices (1–99) when a larger amount exists.
    candidates: list[float] = []
    for m in matches:
        val = parse_vn_number(m.group(1))
        if val is None:
            continue
        candidates.append(val)
    if not candidates:
        return None
    large = [c for c in candidates if abs(c) >= 100]
    if large:
        return large[-1]
    return candidates[-1]


def _lines_from_pdf(pdf: pdfplumber.PDF) -> tuple[list[str], str]:
    lines: list[str] = []
    chunks: list[str] = []
    for page in pdf.pages:
        text = page.extract_text() or ""
        chunks.append(text)
        for raw in text.splitlines():
            line = _norm_ws(raw)
            if line:
                lines.append(line)
        tables = page.extract_tables() or []
        for table in tables:
            for row in table:
                if not row:
                    continue
                cells = [_norm_ws(str(c)) for c in row if c is not None and str(c).strip()]
                if cells:
                    lines.append(" ".join(cells))
    return lines, "\n".join(chunks)


def _apply_scale(value: float, field_name: str, scale: int) -> float | int:
    if field_name == "employees":
        return int(round(value))
    return float(value * scale)


def extract_fields_from_lines(
    lines: list[str],
    full_text: str,
    *,
    source_type: str = "pdf_text",
    confidence_scale: float = 1.0,
    empty_text_warning: str | None = "pdf_text_empty",
) -> BctcExtractResult:
    """Shared rules-first mapper over label+amount lines (text PDF or OCR).

    ``confidence_scale`` down-weights OCR-derived fields (e.g. 0.85). Ambiguous
    or missing values stay ``null`` — never invent.
    """
    warnings: list[str] = []
    fields: dict[str, float | int | None] = {k: None for k in EXTRACT_FIELDS}
    confidence: dict[str, float] = {k: 0.0 for k in EXTRACT_FIELDS}

    if not _norm_ws(full_text):
        if empty_text_warning:
            warnings.append(empty_text_warning)
        warnings.append("no_extractable_fields")
        return BctcExtractResult(
            fields=fields,
            confidence=confidence,
            warnings=warnings,
            source_type=source_type,
        )

    scale, unit_warning = _detect_unit_scale(full_text)
    if unit_warning:
        warnings.append(unit_warning)

    hits: dict[str, list[tuple[float | int, float, str]]] = {k: [] for k in EXTRACT_FIELDS}

    for line in lines:
        mapped = _map_label(line)
        if mapped is None or mapped not in EXTRACT_FIELDS:
            continue
        raw_val = _extract_amount_from_line(line)
        if raw_val is None:
            warnings.append(f"label_without_amount:{mapped}")
            continue
        if mapped == "employees" and (raw_val < 0 or raw_val != int(raw_val)):
            if raw_val < 0 or abs(raw_val - round(raw_val)) > 0.01:
                warnings.append(f"employees_unparseable:{line[:80]}")
                continue
        value = _apply_scale(raw_val, mapped, scale if mapped != "employees" else 1)
        base_conf = 0.9 if abs(float(raw_val)) >= 100 or mapped == "employees" else 0.7
        conf = max(0.0, min(1.0, base_conf * confidence_scale))
        hits[mapped].append((value, conf, line))

    for key in EXTRACT_FIELDS:
        found = hits[key]
        if not found:
            warnings.append(f"missing_field:{key}")
            continue
        values = {v for v, _, _ in found}
        if len(values) > 1:
            warnings.append(f"ambiguous_field:{key}")
            fields[key] = None
            confidence[key] = 0.0
            continue
        value, conf, _ = found[0]
        fields[key] = value
        confidence[key] = conf

    if all(fields[k] is None for k in EXTRACT_FIELDS):
        if "no_extractable_fields" not in warnings:
            warnings.append("no_extractable_fields")

    return BctcExtractResult(
        fields=fields,
        confidence=confidence,
        warnings=warnings,
        source_type=source_type,
    )


def _open_pdf(source: str | Path | bytes | BinaryIO):
    if isinstance(source, (str, Path)):
        return pdfplumber.open(str(source))
    if isinstance(source, (bytes, bytearray)):
        return pdfplumber.open(io.BytesIO(source))
    return pdfplumber.open(source)


def extract_bctc_pdf(
    source: str | Path | bytes | BinaryIO,
) -> BctcExtractResult:
    """Extract BenchmarkInput subset from a digital-text PDF.

    ``source`` may be a filesystem path, raw bytes, or a binary file object.
    Does **not** run OCR — use :func:`extract_bctc` for scan fallback.
    """
    with _open_pdf(source) as pdf:
        if not pdf.pages:
            return BctcExtractResult(
                fields={k: None for k in EXTRACT_FIELDS},
                confidence={k: 0.0 for k in EXTRACT_FIELDS},
                warnings=["pdf_has_no_pages"],
                source_type="pdf_text",
            )
        lines, full_text = _lines_from_pdf(pdf)

    return extract_fields_from_lines(lines, full_text, source_type="pdf_text")


def extract_bctc_pdf_dict(source: str | Path | bytes | BinaryIO) -> dict[str, Any]:
    """Dict form of :func:`extract_bctc_pdf` (API-ready)."""
    return extract_bctc_pdf(source).to_dict()


def _sniff_kind(
    source: str | Path | bytes | BinaryIO,
    *,
    filename: str | None = None,
) -> str:
    """Return ``image``, ``pdf``, or ``unknown``."""
    name = filename or ""
    if isinstance(source, (str, Path)):
        name = name or str(source)
    suffix = Path(name).suffix.lower()
    if suffix in _IMAGE_SUFFIXES:
        return "image"
    if suffix in _PDF_SUFFIXES:
        return "pdf"

    head = b""
    if isinstance(source, (bytes, bytearray)):
        head = bytes(source[:16])
    elif hasattr(source, "read") and hasattr(source, "seek"):
        pos = source.tell()
        head = source.read(16) or b""
        source.seek(pos)
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"\x89PNG") or head[:2] == b"\xff\xd8":
        return "image"
    if suffix:
        return "unknown"
    return "pdf"  # legacy default for pathless bytes used as PDF in #52


def _pdf_text_sufficient(full_text: str) -> bool:
    return len(_norm_ws(full_text)) >= MIN_PDF_TEXT_CHARS


def extract_bctc(
    source: str | Path | bytes | BinaryIO,
    *,
    filename: str | None = None,
) -> BctcExtractResult:
    """Route digital-text PDF vs OCR fallback (scan PDF / image).

    - Image → ``source_type=image_ocr``
    - PDF with enough extractable text → ``pdf_text`` (pdfplumber, no OCR)
    - PDF with little/no text → rasterize + OCR → ``pdf_ocr``
    """
    kind = _sniff_kind(source, filename=filename)

    if kind == "image":
        from backend.app.services.bctc_extract_ocr import extract_bctc_image_ocr

        return extract_bctc_image_ocr(source)

    # PDF (or unknown treated as PDF)
    with _open_pdf(source) as pdf:
        if not pdf.pages:
            return BctcExtractResult(
                fields={k: None for k in EXTRACT_FIELDS},
                confidence={k: 0.0 for k in EXTRACT_FIELDS},
                warnings=["pdf_has_no_pages"],
                source_type="pdf_text",
            )
        lines, full_text = _lines_from_pdf(pdf)
        page_count = len(pdf.pages)

    if _pdf_text_sufficient(full_text):
        return extract_fields_from_lines(lines, full_text, source_type="pdf_text")

    # Sparse / empty text → OCR fallback (need bytes for rasterize).
    from backend.app.services.bctc_extract_ocr import extract_bctc_pdf_ocr

    if isinstance(source, (str, Path)):
        pdf_bytes = Path(source).read_bytes()
    elif isinstance(source, (bytes, bytearray)):
        pdf_bytes = bytes(source)
    else:
        pos = source.tell()
        pdf_bytes = source.read()
        source.seek(pos)

    if page_count == 0:
        return BctcExtractResult(
            fields={k: None for k in EXTRACT_FIELDS},
            confidence={k: 0.0 for k in EXTRACT_FIELDS},
            warnings=["pdf_has_no_pages"],
            source_type="pdf_text",
        )

    result = extract_bctc_pdf_ocr(pdf_bytes)
    # Preserve probe signal that digital text was insufficient.
    if "pdf_text_sparse" not in result.warnings and not _norm_ws(full_text):
        result.warnings.insert(0, "pdf_text_empty")
    elif "pdf_text_sparse" not in result.warnings:
        result.warnings.insert(0, "pdf_text_sparse")
    return result


def extract_bctc_dict(
    source: str | Path | bytes | BinaryIO,
    *,
    filename: str | None = None,
) -> dict[str, Any]:
    """Dict form of :func:`extract_bctc` (API-ready)."""
    return extract_bctc(source, filename=filename).to_dict()
