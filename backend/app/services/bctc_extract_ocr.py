"""OCR fallback for scanned BCTC PDF / images (Task #53).

Uses optional PaddleOCR (``requirements-ocr.txt``). Rasterizes PDF pages via
pypdfium2 (already pulled in by pdfplumber) then OCRs images. Reuses
:func:`backend.app.services.bctc_extract.extract_fields_from_lines` for VN
number normalize + label map — no duplicate mapper logic.
"""

from __future__ import annotations

import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

from PIL import Image

from backend.app.services.bctc_extract import (
    EXTRACT_FIELDS,
    MAX_BCTC_PAGES,
    BctcExtractResult,
    _norm_ws,
    _pages_capped_warning,
    extract_fields_from_lines,
)

# Down-weight OCR field confidence vs digital-text path.
_OCR_CONFIDENCE_SCALE = 0.85
_OCR_MEAN_SCORE_FLOOR = 0.55
_PDF_RENDER_SCALE = 2.0  # ~144 DPI


def paddleocr_available() -> bool:
    try:
        import paddleocr  # noqa: F401

        return True
    except ImportError:
        return False


@lru_cache(maxsize=1)
def _ocr_engine():
    """Lazy singleton; models download to ~/.paddlex on first use."""
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    from paddleocr import PaddleOCR

    return PaddleOCR(
        lang="vi",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )


def _parse_predict_payload(res: object) -> tuple[list[str], list[float]]:
    payload = getattr(res, "json", None)
    if callable(payload):
        payload = payload()
    if not isinstance(payload, dict):
        return [], []
    data = payload.get("res", payload) if "res" in payload else payload
    if not isinstance(data, dict):
        return [], []
    texts = list(data.get("rec_texts") or [])
    scores_raw = data.get("rec_scores") or []
    scores = [float(s) for s in scores_raw]
    return [str(t) for t in texts], scores


def ocr_image_to_lines(image: str | Path | Image.Image | bytes) -> tuple[list[str], list[float]]:
    """Run PaddleOCR → (text lines, per-line scores)."""
    engine = _ocr_engine()
    tmp_path: str | None = None
    try:
        if isinstance(image, Image.Image):
            fd, tmp_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            image.save(tmp_path)
            target: str | Path = tmp_path
        elif isinstance(image, (bytes, bytearray)):
            fd, tmp_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            Path(tmp_path).write_bytes(bytes(image))
            target = tmp_path
        else:
            target = image

        result = engine.predict(str(target))
        lines: list[str] = []
        scores: list[float] = []
        for res in result or []:
            texts, confs = _parse_predict_payload(res)
            for idx, text in enumerate(texts):
                line = _norm_ws(text)
                if not line:
                    continue
                lines.append(line)
                scores.append(float(confs[idx]) if idx < len(confs) else 0.0)
        return lines, scores
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def pdf_bytes_to_images(
    pdf_bytes: bytes,
    *,
    scale: float = _PDF_RENDER_SCALE,
    max_pages: int = MAX_BCTC_PAGES,
) -> tuple[list[Image.Image], int]:
    """Rasterize PDF pages with pypdfium2 (no poppler / pdf2image).

    Returns ``(images, total_page_count)``. Only the first ``max_pages`` are
    rendered; callers should surface ``pages_capped:N`` when total exceeds N.
    """
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(pdf_bytes)
    images: list[Image.Image] = []
    try:
        total = len(doc)
        for i in range(min(total, max_pages)):
            page = doc[i]
            bitmap = page.render(scale=scale)
            images.append(bitmap.to_pil())
    finally:
        doc.close()
    return images, total


def _unavailable_result(source_type: str) -> BctcExtractResult:
    return BctcExtractResult(
        fields={k: None for k in EXTRACT_FIELDS},
        confidence={k: 0.0 for k in EXTRACT_FIELDS},
        warnings=["ocr_unavailable", "no_extractable_fields"],
        source_type=source_type,
    )


def _result_from_ocr_lines(
    lines: list[str],
    scores: list[float],
    *,
    source_type: str,
) -> BctcExtractResult:
    full_text = "\n".join(lines)
    result = extract_fields_from_lines(
        lines,
        full_text,
        source_type=source_type,
        confidence_scale=_OCR_CONFIDENCE_SCALE,
        empty_text_warning="ocr_text_empty",
    )
    if scores:
        mean_score = sum(scores) / len(scores)
        if mean_score < _OCR_MEAN_SCORE_FLOOR:
            result.warnings.insert(0, f"ocr_low_confidence:{mean_score:.2f}")
            # Low overall OCR → do not invent; null all fields.
            result.fields = {k: None for k in EXTRACT_FIELDS}
            result.confidence = {k: 0.0 for k in EXTRACT_FIELDS}
            if "no_extractable_fields" not in result.warnings:
                result.warnings.append("no_extractable_fields")
    return result


def extract_bctc_image_ocr(source: str | Path | bytes | BinaryIO) -> BctcExtractResult:
    """OCR a PNG/JPEG (etc.) → same contract as text-PDF extract."""
    if not paddleocr_available():
        return _unavailable_result("image_ocr")

    if isinstance(source, (str, Path)):
        image: str | Path | Image.Image | bytes = source
    elif isinstance(source, (bytes, bytearray)):
        image = bytes(source)
    else:
        image = source.read()

    try:
        lines, scores = ocr_image_to_lines(image)
    except Exception as exc:  # noqa: BLE001 — surface as warning, never invent
        return BctcExtractResult(
            fields={k: None for k in EXTRACT_FIELDS},
            confidence={k: 0.0 for k in EXTRACT_FIELDS},
            warnings=[f"ocr_failed:{type(exc).__name__}", "no_extractable_fields"],
            source_type="image_ocr",
        )
    return _result_from_ocr_lines(lines, scores, source_type="image_ocr")


def extract_bctc_pdf_ocr(source: str | Path | bytes | BinaryIO) -> BctcExtractResult:
    """Rasterize PDF pages + OCR → ``source_type=pdf_ocr``."""
    if not paddleocr_available():
        return _unavailable_result("pdf_ocr")

    if isinstance(source, (str, Path)):
        pdf_bytes = Path(source).read_bytes()
    elif isinstance(source, (bytes, bytearray)):
        pdf_bytes = bytes(source)
    else:
        pdf_bytes = source.read()

    try:
        pages, total_pages = pdf_bytes_to_images(pdf_bytes)
    except Exception as exc:  # noqa: BLE001
        return BctcExtractResult(
            fields={k: None for k in EXTRACT_FIELDS},
            confidence={k: 0.0 for k in EXTRACT_FIELDS},
            warnings=[f"pdf_rasterize_failed:{type(exc).__name__}", "no_extractable_fields"],
            source_type="pdf_ocr",
        )

    if not pages:
        return BctcExtractResult(
            fields={k: None for k in EXTRACT_FIELDS},
            confidence={k: 0.0 for k in EXTRACT_FIELDS},
            warnings=["pdf_has_no_pages", "no_extractable_fields"],
            source_type="pdf_ocr",
        )

    all_lines: list[str] = []
    all_scores: list[float] = []
    try:
        for page_img in pages:
            lines, scores = ocr_image_to_lines(page_img)
            all_lines.extend(lines)
            all_scores.extend(scores)
    except Exception as exc:  # noqa: BLE001
        return BctcExtractResult(
            fields={k: None for k in EXTRACT_FIELDS},
            confidence={k: 0.0 for k in EXTRACT_FIELDS},
            warnings=[f"ocr_failed:{type(exc).__name__}", "no_extractable_fields"],
            source_type="pdf_ocr",
        )

    result = _result_from_ocr_lines(all_lines, all_scores, source_type="pdf_ocr")
    capped = _pages_capped_warning(total_pages)
    if capped:
        result.warnings.insert(0, capped)
    return result
