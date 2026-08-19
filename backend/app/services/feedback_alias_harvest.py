"""Harvest alias/unit-rule *proposals* from feedback JSONL (Task #79).

Honest v1: the store (`data/feedback/training_signals.jsonl`) only has allowlisted
numeric form diffs, ticker, source_type, and timestamp. It does **not** contain
original BCTC labels or PDF text, so this module never invents alias strings and
**never writes** ``_LABEL_ALIASES`` in ``bctc_extract.py``.

When humans correct the same field ≥ N times (default 3), emit a review proposal.
If after/before ratios cluster around 1000 or 1e6 across ≥ N edits, also propose
a unit-scale rule (nghìn / triệu) for a human to apply later.

Does not call Prefect. Does not retrain sklearn/OCR.
"""

from __future__ import annotations

import json
import logging
import math
import os
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from backend.app.schemas.feedback_signal import ALLOWED_SIGNAL_FIELDS
from backend.app.services.bctc_extract import EXTRACT_FIELDS
from backend.app.services.feedback_signal import (
    DEFAULT_STORE_PATH,
    FORBIDDEN_PAYLOAD_KEYS,
    _is_forbidden_key,
    _value_looks_like_binary_or_secret,
)

logger = logging.getLogger(__name__)

DEFAULT_MIN_COUNT = 3
MIN_COUNT_ENV = "FEEDBACK_ALIAS_HARVEST_MIN_COUNT"
RATIO_REL_TOL = 0.08

# Headcount / codes are not VND unit-scale candidates.
_UNIT_SCALE_SKIP_FIELDS: frozenset[str] = frozenset({"stock_code", "vsic_code", "employees"})

# Extract mapper targets (aliases live in bctc_extract._LABEL_ALIASES — read-only here).
_EXTRACT_ALIAS_FIELDS: frozenset[str] = frozenset(EXTRACT_FIELDS) | {"current_assets"}

# (ratio, id, human rule suggestion)
_SCALE_CLASSES: tuple[tuple[float, str, str], ...] = (
    (1_000.0, "nghin", "Review nghìn / 1.000 VND unit detection (human values ~×1000 vs extract)."),
    (1_000_000.0, "trieu", "Review triệu VND unit detection (human values ~×1e6 vs extract)."),
    (0.001, "nghin_overapplied", "Review whether nghìn scale was applied when the PDF was already full VND (~×0.001)."),
    (1e-6, "trieu_overapplied", "Review whether triệu scale was applied when the PDF was already full VND (~×1e-6)."),
)

# Markers that must never appear in harvest output (raw docs / secrets).
_UNSAFE_REPORT_MARKERS: tuple[str, ...] = (
    "raw_pdf",
    "file_bytes",
    "api_key",
    "authorization",
    "%pdf",
    "data:application/pdf",
)


def default_min_count() -> int:
    raw = os.environ.get(MIN_COUNT_ENV, str(DEFAULT_MIN_COUNT)).strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_MIN_COUNT


@dataclass
class FieldEdit:
    field: str
    ticker: str | None
    before: Any
    after: Any
    source_type: str | None
    timestamp: str | None


@dataclass
class Proposal:
    kind: str
    field: str
    count: int
    min_count: int
    tickers: list[str] = field(default_factory=list)
    ticker_counts: dict[str, int] = field(default_factory=dict)
    source_types: list[str] = field(default_factory=list)
    in_extract_aliases: bool = False
    unit_scale: str | None = None
    suggested_rule: str | None = None
    proposed_aliases: list[str] = field(default_factory=list)
    sample_ratios: list[float] = field(default_factory=list)
    rationale: str = ""
    auto_applied: bool = False


@dataclass
class HarvestReport:
    store_path: str
    min_count: int
    records_read: int
    records_skipped: int
    edits_counted: int
    field_counts: dict[str, int]
    ticker_field_counts: dict[str, dict[str, int]]
    proposals: list[Proposal]
    auto_applied: bool = False
    aliases_written: bool = False
    note: str = (
        "v1 proposals only. JSONL has no original BCTC labels; "
        "_LABEL_ALIASES was not modified."
    )


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return None
        return number
    if isinstance(value, str):
        text = value.strip()
        if not text or len(text) > 64:
            return None
        if _value_looks_like_binary_or_secret(text):
            return None
        try:
            return float(text.replace(" ", "").replace(",", ""))
        except ValueError:
            return None
    return None


def _classify_ratio(before: Any, after: Any) -> tuple[str | None, float | None]:
    left = _as_float(before)
    right = _as_float(after)
    if left is None or right is None or left == 0:
        return None, None
    if left * right < 0:
        return None, None
    ratio = right / left
    if math.isnan(ratio) or math.isinf(ratio):
        return None, None
    for target, scale_id, _hint in _SCALE_CLASSES:
        if math.isclose(ratio, target, rel_tol=RATIO_REL_TOL, abs_tol=0.0):
            return scale_id, ratio
    return None, ratio


def iter_jsonl_records(path: Path) -> tuple[list[dict[str, Any]], int]:
    """Load JSON objects from JSONL. Skip blank/malformed lines. Drop unsafe keys."""
    if not path.is_file():
        return [], 0
    records: list[dict[str, Any]] = []
    skipped = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if not isinstance(payload, dict):
                skipped += 1
                continue
            records.append(_sanitize_record(payload))
    return records, skipped


def _sanitize_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep only signal metadata + allowlisted field diffs. Never pass through raw docs."""
    diffs_out: list[dict[str, Any]] = []
    for diff in payload.get("field_diffs") or []:
        if not isinstance(diff, dict):
            continue
        name = str(diff.get("field") or "").strip()
        if not name or name not in ALLOWED_SIGNAL_FIELDS:
            continue
        if _is_forbidden_key(name):
            continue
        before, after = diff.get("before"), diff.get("after")
        if _value_looks_like_binary_or_secret(before) or _value_looks_like_binary_or_secret(after):
            continue
        diffs_out.append({"field": name, "before": before, "after": after})
    ticker = payload.get("ticker")
    if ticker is not None:
        ticker = str(ticker).strip().upper() or None
        if ticker and len(ticker) > 16:
            ticker = ticker[:16]
    source_type = payload.get("source_type")
    if source_type is not None:
        source_type = str(source_type).strip().lower().replace(" ", "_") or None
        if source_type and len(source_type) > 64:
            source_type = source_type[:64]
    timestamp = payload.get("timestamp")
    if timestamp is not None:
        timestamp = str(timestamp)
        if len(timestamp) > 64:
            timestamp = timestamp[:64]
    return {
        "ticker": ticker,
        "source_type": source_type,
        "timestamp": timestamp,
        "field_diffs": diffs_out,
    }


def iter_field_edits(records: Iterable[dict[str, Any]]) -> list[FieldEdit]:
    edits: list[FieldEdit] = []
    for record in records:
        for diff in record.get("field_diffs") or []:
            name = diff.get("field")
            if name not in ALLOWED_SIGNAL_FIELDS:
                continue
            edits.append(
                FieldEdit(
                    field=name,
                    ticker=record.get("ticker"),
                    before=diff.get("before"),
                    after=diff.get("after"),
                    source_type=record.get("source_type"),
                    timestamp=record.get("timestamp"),
                )
            )
    return edits


def _scale_hint(scale_id: str) -> str:
    for _target, sid, hint in _SCALE_CLASSES:
        if sid == scale_id:
            return hint
    return "Review unit-scale rules for this field."


def harvest_proposals(
    records: Iterable[dict[str, Any]],
    *,
    min_count: int | None = None,
) -> list[Proposal]:
    """Emit review proposals. Never patches extract aliases."""
    threshold = default_min_count() if min_count is None else max(1, int(min_count))
    edits = iter_field_edits(records)
    by_field: dict[str, list[FieldEdit]] = defaultdict(list)
    for edit in edits:
        by_field[edit.field].append(edit)

    proposals: list[Proposal] = []
    for field_name, field_edits in sorted(by_field.items()):
        count = len(field_edits)
        if count < threshold:
            continue
        ticker_counter: Counter[str] = Counter()
        sources: set[str] = set()
        for edit in field_edits:
            if edit.ticker:
                ticker_counter[edit.ticker] += 1
            if edit.source_type:
                sources.add(edit.source_type)
        in_extract = field_name in _EXTRACT_ALIAS_FIELDS
        rationale = (
            f"Humans corrected `{field_name}` {count} times (≥ {threshold}). "
            "JSONL has no original BCTC labels, so no new alias strings are proposed — "
            "review `_LABEL_ALIASES` / unit rules in bctc_extract.py manually."
            if in_extract
            else (
                f"Humans corrected `{field_name}` {count} times (≥ {threshold}). "
                "This field is allowlisted for feedback but is not a BCTC extract alias "
                "target; review prefill/mapping rules. No alias strings invented."
            )
        )
        proposals.append(
            Proposal(
                kind="review_aliases",
                field=field_name,
                count=count,
                min_count=threshold,
                tickers=sorted(ticker_counter),
                ticker_counts=dict(sorted(ticker_counter.items())),
                source_types=sorted(sources),
                in_extract_aliases=in_extract,
                proposed_aliases=[],
                rationale=rationale,
                auto_applied=False,
            )
        )

        if field_name in _UNIT_SCALE_SKIP_FIELDS:
            continue
        scale_hits: Counter[str] = Counter()
        ratios_by_scale: dict[str, list[float]] = defaultdict(list)
        for edit in field_edits:
            scale_id, ratio = _classify_ratio(edit.before, edit.after)
            if scale_id is None or ratio is None:
                continue
            scale_hits[scale_id] += 1
            ratios_by_scale[scale_id].append(round(ratio, 6))
        if not scale_hits:
            continue
        scale_id, scale_count = scale_hits.most_common(1)[0]
        if scale_count < threshold:
            continue
        sample = ratios_by_scale[scale_id][:12]
        proposals.append(
            Proposal(
                kind="review_unit_scale",
                field=field_name,
                count=scale_count,
                min_count=threshold,
                tickers=sorted(ticker_counter),
                ticker_counts=dict(sorted(ticker_counter.items())),
                source_types=sorted(sources),
                in_extract_aliases=in_extract,
                unit_scale=scale_id,
                suggested_rule=_scale_hint(scale_id),
                proposed_aliases=[],
                sample_ratios=sample,
                rationale=(
                    f"{scale_count} numeric edits of `{field_name}` have after/before ≈ "
                    f"{scale_id} (tolerance {RATIO_REL_TOL:.0%}). "
                    "Proposal only — unit regex in bctc_extract.py was not changed."
                ),
                auto_applied=False,
            )
        )
    return proposals


def harvest_from_jsonl(
    store_path: Path | None = None,
    *,
    min_count: int | None = None,
) -> HarvestReport:
    path = Path(store_path) if store_path is not None else DEFAULT_STORE_PATH
    threshold = default_min_count() if min_count is None else max(1, int(min_count))
    records, skipped = iter_jsonl_records(path)
    edits = iter_field_edits(records)
    field_counts: dict[str, int] = defaultdict(int)
    ticker_field: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for edit in edits:
        field_counts[edit.field] += 1
        if edit.ticker:
            ticker_field[edit.ticker][edit.field] += 1
    proposals = harvest_proposals(records, min_count=threshold)
    report = HarvestReport(
        store_path=str(path),
        min_count=threshold,
        records_read=len(records),
        records_skipped=skipped,
        edits_counted=len(edits),
        field_counts=dict(sorted(field_counts.items())),
        ticker_field_counts={
            ticker: dict(sorted(counts.items()))
            for ticker, counts in sorted(ticker_field.items())
        },
        proposals=proposals,
        auto_applied=False,
        aliases_written=False,
    )
    assert_report_is_safe(report)
    return report


def report_to_dict(report: HarvestReport) -> dict[str, Any]:
    data = asdict(report)
    assert_report_is_safe(data)
    return data


def render_markdown(report: HarvestReport) -> str:
    lines = [
        "# Feedback alias / unit-rule harvest (v1)",
        "",
        "Proposals only. **`_LABEL_ALIASES` was not modified.** JSONL has no PDF bytes "
        "and no original BCTC labels — v1 does not invent alias strings.",
        "",
        f"- Store: `{report.store_path}`",
        f"- Min count: {report.min_count}",
        f"- Records read: {report.records_read} (skipped malformed: {report.records_skipped})",
        f"- Field edits counted: {report.edits_counted}",
        f"- Auto-applied: **no**",
        f"- Aliases written: **no**",
        "",
        "## Field correction counts",
        "",
        "| field | count | at/above threshold |",
        "| --- | ---: | --- |",
    ]
    if report.field_counts:
        for name, count in report.field_counts.items():
            flag = "yes" if count >= report.min_count else "no"
            lines.append(f"| `{name}` | {count} | {flag} |")
    else:
        lines.append("| _(none)_ | 0 | no |")
    lines.extend(["", "## Proposals", ""])
    if not report.proposals:
        lines.append("No proposals (no field reached the min-count threshold).")
    else:
        for prop in report.proposals:
            title = f"### `{prop.field}` — {prop.kind}"
            lines.append(title)
            lines.append("")
            lines.append(f"- Count: {prop.count} (min {prop.min_count})")
            lines.append(f"- Tickers: {', '.join(prop.tickers) if prop.tickers else '(none)'}")
            lines.append(
                f"- Source types: {', '.join(prop.source_types) if prop.source_types else '(none)'}"
            )
            lines.append(f"- In extract aliases: {'yes' if prop.in_extract_aliases else 'no'}")
            lines.append("- Proposed aliases: _(none — labels not in JSONL)_")
            if prop.unit_scale:
                lines.append(f"- Unit scale class: `{prop.unit_scale}`")
            if prop.suggested_rule:
                lines.append(f"- Suggested rule: {prop.suggested_rule}")
            if prop.sample_ratios:
                lines.append(f"- Sample after/before ratios: {prop.sample_ratios}")
            lines.append(f"- Auto-applied: **no**")
            lines.append(f"- Rationale: {prop.rationale}")
            lines.append("")
    if report.ticker_field_counts:
        lines.extend(["## Counts by ticker", ""])
        for ticker, counts in report.ticker_field_counts.items():
            parts = ", ".join(f"{k}={v}" for k, v in counts.items())
            lines.append(f"- `{ticker}`: {parts}")
        lines.append("")
    lines.extend(["## Note", "", report.note, ""])
    text = "\n".join(lines)
    _assert_text_is_safe(text)
    return text


def assert_report_is_safe(report: HarvestReport | dict[str, Any]) -> None:
    blob = json.dumps(report if isinstance(report, dict) else asdict(report), default=str)
    _assert_text_is_safe(blob)
    payload = report if isinstance(report, dict) else asdict(report)
    for key in payload.keys():
        if _is_forbidden_key(str(key)):
            raise ValueError(f"refusing harvest report with forbidden key: {key}")


def _assert_text_is_safe(text: str) -> None:
    lowered = text.lower()
    for marker in _UNSAFE_REPORT_MARKERS:
        if marker in lowered:
            raise ValueError(f"refusing harvest output containing {marker}")
    for bad in FORBIDDEN_PAYLOAD_KEYS:
        # Allow the *names* of forbidden keys in the safety note? No — report
        # must not contain raw_pdf at all (tests assert absence).
        if bad in {"raw_pdf", "file_bytes", "api_key"} and bad in lowered:
            raise ValueError(f"refusing harvest output containing {bad}")


def write_reports(
    report: HarvestReport,
    *,
    markdown_path: Path | None = None,
    json_path: Path | None = None,
) -> tuple[str, dict[str, Any]]:
    markdown = render_markdown(report)
    payload = report_to_dict(report)
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return markdown, payload
