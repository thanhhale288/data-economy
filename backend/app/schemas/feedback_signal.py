"""Feedback-to-training signal schemas (Task #64).

Stores field-level before/after edits only — never raw PDF/bytes/API keys.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# Benchmark form / extract fields allowed in training signals.
ALLOWED_SIGNAL_FIELDS: frozenset[str] = frozenset(
    {
        "stock_code",
        "vsic_code",
        "operating_revenue",
        "profit_before_tax",
        "employees",
        "operating_expenses",
        "cost_of_goods",
        "rental_cost",
        "remuneration",
        "total_assets",
        "total_equity",
        "current_assets",
        "current_liabilities",
    }
)


class FieldDiff(BaseModel):
    """One edited field: prefill/extract value vs human-confirmed value."""

    field: str
    before: Any | None = None
    after: Any | None = None

    @field_validator("field")
    @classmethod
    def field_must_be_allowlisted(cls, value: str) -> str:
        key = str(value).strip()
        if key not in ALLOWED_SIGNAL_FIELDS:
            raise ValueError(f"field not allowlisted for training signal: {key}")
        return key


class FeedbackSignalIn(BaseModel):
    """POST body for creating a training signal from DocAI/Benchmark edits.

    Extra keys such as ``raw_pdf`` / ``file_bytes`` / ``api_key`` are ignored
    (``extra='ignore'``) and never written by the service.
    """

    model_config = {"extra": "ignore"}

    field_diffs: list[FieldDiff] = Field(default_factory=list)
    ticker: str | None = Field(default=None, max_length=16)
    source_type: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="e.g. docai_extract, cafef_prefill, manual",
    )
    # Optional maps — server computes diffs when field_diffs empty.
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip().upper()
        return cleaned or None

    @field_validator("source_type")
    @classmethod
    def normalize_source_type(cls, value: str) -> str:
        cleaned = str(value).strip().lower().replace(" ", "_")
        if not cleaned:
            raise ValueError("source_type is required")
        return cleaned


class FeedbackSignalRecord(BaseModel):
    """Persisted training signal (JSONL / API response)."""

    id: str
    timestamp: datetime
    field_diffs: list[FieldDiff] = Field(default_factory=list)
    ticker: str | None = None
    source_type: str
    diff_count: int = 0


class FeedbackSignalOut(BaseModel):
    """API response after recording a signal."""

    signal: FeedbackSignalRecord
    stored: bool = True
    store_path: str | None = None
    warning: str | None = None


class FeedbackSignalCountOut(BaseModel):
    """Lightweight counter for monitoring / scheduler."""

    count: int = 0
    store_path: str | None = None
