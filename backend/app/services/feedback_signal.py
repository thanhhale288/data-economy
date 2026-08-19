"""Feedback-to-training loop (Task #64 / #78).

Persist user edits after DocAI extract, CafeF prefill, or manual Benchmark
entry as safe training signals: field diffs + optional ticker + source_type
+ timestamp. ``source_type`` is caller-chosen (``docai_extract`` /
``cafef_prefill`` / ``manual``); this service does not classify origin.

Never persists raw PDF/bytes, filenames with binary payloads, or API keys.
Default store: ``data/feedback/training_signals.jsonl`` (JSONL append).
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.schemas.feedback_signal import (
    ALLOWED_SIGNAL_FIELDS,
    FeedbackSignalCountOut,
    FeedbackSignalIn,
    FeedbackSignalOut,
    FeedbackSignalRecord,
    FieldDiff,
)

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STORE_PATH = REPO_ROOT / "data" / "feedback" / "training_signals.jsonl"

# Keys that must never appear in a persisted signal payload.
FORBIDDEN_PAYLOAD_KEYS: frozenset[str] = frozenset(
    {
        "raw",
        "raw_pdf",
        "pdf",
        "file",
        "file_bytes",
        "bytes",
        "content",
        "binary",
        "data_uri",
        "base64",
        "api_key",
        "apikey",
        "authorization",
        "password",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "filename",  # path leakage; use source_type only
        "filepath",
        "path",
        "upload",
    }
)

_SECRETISH_KEY = re.compile(
    r"(api[_-]?key|secret|password|token|authorization|bearer)",
    re.IGNORECASE,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_forbidden_key(key: str) -> bool:
    lowered = key.strip().lower()
    if lowered in FORBIDDEN_PAYLOAD_KEYS:
        return True
    return bool(_SECRETISH_KEY.search(lowered))


def _value_looks_like_binary_or_secret(value: Any) -> bool:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return True
    if isinstance(value, str):
        # Huge base64-ish blobs are not field diffs.
        if len(value) > 512 and re.fullmatch(r"[A-Za-z0-9+/=\s]+", value or ""):
            return True
        if value.startswith("data:") and ";base64," in value:
            return True
    return False


def sanitize_field_map(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Keep allowlisted scalar fields only; drop secrets / binary."""
    out: dict[str, Any] = {}
    if not isinstance(raw, dict):
        return out
    for key, value in raw.items():
        name = str(key).strip()
        if _is_forbidden_key(name):
            continue
        if name not in ALLOWED_SIGNAL_FIELDS:
            continue
        if _value_looks_like_binary_or_secret(value):
            continue
        if isinstance(value, (dict, list)):
            continue
        out[name] = value
    return out


def compute_field_diffs(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> list[FieldDiff]:
    """Diff allowlisted fields; equal values are omitted."""
    left = sanitize_field_map(before)
    right = sanitize_field_map(after)
    keys = sorted(set(left) | set(right))
    diffs: list[FieldDiff] = []
    for key in keys:
        b = left.get(key)
        a = right.get(key)
        if b == a:
            continue
        # Normalize empty string vs None as equal for form UX.
        if (b is None or b == "") and (a is None or a == ""):
            continue
        diffs.append(FieldDiff(field=key, before=b, after=a))
    return diffs


def assert_record_is_safe(record: dict[str, Any]) -> None:
    """Raise ValueError if a to-be-persisted record contains forbidden material."""
    blob = json.dumps(record, default=str)
    lowered = blob.lower()
    for bad in ("raw_pdf", "file_bytes", "api_key", "authorization", "\\u0000"):
        if bad in lowered:
            raise ValueError(f"refusing to persist unsafe training signal key/material: {bad}")
    for key in record.keys():
        if _is_forbidden_key(str(key)):
            raise ValueError(f"refusing to persist forbidden key: {key}")
    # Nested field_diffs values must not be binary.
    for diff in record.get("field_diffs") or []:
        if not isinstance(diff, dict):
            continue
        for side in ("before", "after"):
            if _value_looks_like_binary_or_secret(diff.get(side)):
                raise ValueError(f"refusing binary/secret value in field_diffs.{side}")


def build_signal_record(payload: FeedbackSignalIn) -> FeedbackSignalRecord:
    """Validate inbound payload and build a persistable record (no store I/O)."""
    diffs = list(payload.field_diffs)
    if not diffs and (payload.before is not None or payload.after is not None):
        diffs = compute_field_diffs(payload.before, payload.after)

    safe_diffs = [
        FieldDiff(field=d.field, before=d.before, after=d.after)
        for d in diffs
        if d.field in ALLOWED_SIGNAL_FIELDS
        and not _value_looks_like_binary_or_secret(d.before)
        and not _value_looks_like_binary_or_secret(d.after)
    ]

    return FeedbackSignalRecord(
        id=str(uuid.uuid4()),
        timestamp=_utc_now(),
        field_diffs=safe_diffs,
        ticker=payload.ticker,
        source_type=payload.source_type,
        diff_count=len(safe_diffs),
    )


def record_to_dict(record: FeedbackSignalRecord) -> dict[str, Any]:
    data = record.model_dump(mode="json")
    assert_record_is_safe(data)
    return data


def append_signal(
    payload: FeedbackSignalIn,
    *,
    store_path: Path | None = None,
) -> FeedbackSignalOut:
    """Append one training signal to JSONL. Never writes raw files/bytes."""
    path = Path(store_path) if store_path is not None else DEFAULT_STORE_PATH
    record = build_signal_record(payload)
    data = record_to_dict(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # Defense: refuse if serialized line somehow embeds forbidden markers.
    if any(
        marker in line.lower()
        for marker in ("raw_pdf", "file_bytes", '"api_key"', "authorization:")
    ):
        raise ValueError("refusing to write training signal with forbidden material")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    logger.info(
        "feedback_signal stored id=%s source=%s diffs=%s ticker=%s",
        record.id,
        record.source_type,
        record.diff_count,
        record.ticker,
    )
    return FeedbackSignalOut(
        signal=record,
        stored=True,
        store_path=str(path),
        warning=None if record.diff_count else "no_field_diffs",
    )


def count_signals(*, store_path: Path | None = None) -> FeedbackSignalCountOut:
    """Count JSONL lines for monitoring counters / scheduler."""
    path = Path(store_path) if store_path is not None else DEFAULT_STORE_PATH
    if not path.is_file():
        return FeedbackSignalCountOut(count=0, store_path=str(path))
    n = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return FeedbackSignalCountOut(count=n, store_path=str(path))


def ingest_feedback_for_scheduler(*, store_path: Path | None = None) -> tuple[int, str]:
    """Thin scheduler hook: report how many training signals are on disk.

    Does not retrain models; only surfaces count for PipelineJob detail.
    """
    result = count_signals(store_path=store_path)
    detail = f"feedback_signals={result.count}; path={result.store_path}"
    return result.count, detail
