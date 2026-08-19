"""Task #79 — Harvest alias/unit-rule proposals from feedback JSONL (no auto-apply)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.services.feedback_alias_harvest import (
    harvest_from_jsonl,
    render_markdown,
    report_to_dict,
    write_reports,
)
from backend.app.services.feedback_signal import FORBIDDEN_PAYLOAD_KEYS

EXTRACT_PATH = Path("backend/app/services/bctc_extract.py")
FIXTURE_PATH = Path("tests/benchmark/fixtures/feedback_alias_harvest.jsonl")


def _write_jsonl(path: Path, records: list[dict]) -> Path:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
        encoding="utf-8",
    )
    return path


def _edit(
    field: str,
    before,
    after,
    *,
    ticker: str | None = "RAL",
    source_type: str = "docai_extract",
    timestamp: str = "2026-08-01T00:00:00",
) -> dict:
    return {
        "id": "test",
        "timestamp": timestamp,
        "ticker": ticker,
        "source_type": source_type,
        "diff_count": 1,
        "field_diffs": [{"field": field, "before": before, "after": after}],
    }


def test_below_min_count_emits_no_proposal(tmp_path: Path):
    store = _write_jsonl(
        tmp_path / "signals.jsonl",
        [
            _edit("profit_before_tax", 100, 150, ticker="RAL"),
            _edit("profit_before_tax", 200, 250, ticker="HPG"),
        ],
    )
    report = harvest_from_jsonl(store, min_count=3)
    assert report.field_counts["profit_before_tax"] == 2
    assert report.proposals == []
    markdown = render_markdown(report)
    assert "No proposals" in markdown
    assert report.auto_applied is False
    assert report.aliases_written is False


def test_at_min_count_emits_review_proposal(tmp_path: Path):
    store = _write_jsonl(
        tmp_path / "signals.jsonl",
        [
            _edit("profit_before_tax", 100, 150, ticker="RAL"),
            _edit("profit_before_tax", 200, 180, ticker="HPG"),
            _edit("profit_before_tax", 50, 80, ticker="VNM"),
        ],
    )
    report = harvest_from_jsonl(store, min_count=3)
    kinds = {(p.kind, p.field) for p in report.proposals}
    assert ("review_aliases", "profit_before_tax") in kinds
    alias = next(p for p in report.proposals if p.kind == "review_aliases")
    assert alias.count == 3
    assert alias.proposed_aliases == []
    assert alias.auto_applied is False
    assert alias.in_extract_aliases is True
    assert set(alias.tickers) == {"RAL", "HPG", "VNM"}
    # Unrelated ratios must not invent a unit-scale rule.
    assert not any(p.kind == "review_unit_scale" for p in report.proposals)


def test_consistent_thousand_ratio_proposes_unit_scale(tmp_path: Path):
    store = _write_jsonl(
        tmp_path / "signals.jsonl",
        [
            _edit("operating_revenue", 1_000, 1_000_000, ticker="RAL"),
            _edit("operating_revenue", 2_000, 2_000_000, ticker="RAL"),
            _edit("operating_revenue", 3_500, 3_500_000, ticker="BMP"),
        ],
    )
    report = harvest_from_jsonl(store, min_count=3)
    unit = next(p for p in report.proposals if p.kind == "review_unit_scale")
    assert unit.field == "operating_revenue"
    assert unit.unit_scale == "nghin"
    assert unit.count == 3
    assert unit.auto_applied is False
    assert unit.proposed_aliases == []
    assert "nghìn" in (unit.suggested_rule or "").lower() or "nghin" in (unit.suggested_rule or "").lower()


def test_million_ratio_proposes_trieu_scale(tmp_path: Path):
    store = _write_jsonl(
        tmp_path / "signals.jsonl",
        [
            _edit("total_assets", 10, 10_000_000, ticker="HPG"),
            _edit("total_assets", 12, 12_000_000, ticker="HPG"),
            _edit("total_assets", 8, 8_000_000, ticker="HPG"),
        ],
    )
    report = harvest_from_jsonl(store, min_count=3)
    unit = next(p for p in report.proposals if p.kind == "review_unit_scale")
    assert unit.unit_scale == "trieu"


def test_report_contains_no_raw_pdf_or_secrets(tmp_path: Path):
    poisoned = _edit("employees", 10, 12, ticker="ABC")
    poisoned["raw_pdf"] = "%PDF-1.4 fake binary"
    poisoned["file_bytes"] = "AQID" + ("A" * 200)
    poisoned["api_key"] = "sk-secret-should-never-appear"
    poisoned["content"] = "data:application/pdf;base64," + ("B" * 80)
    store = _write_jsonl(
        tmp_path / "signals.jsonl",
        [poisoned, _edit("employees", 11, 13, ticker="ABC"), _edit("employees", 14, 16, ticker="ABC")],
    )
    report = harvest_from_jsonl(store, min_count=3)
    markdown = render_markdown(report)
    payload = report_to_dict(report)
    blob = (markdown + json.dumps(payload)).lower()
    assert "raw_pdf" not in blob
    assert "file_bytes" not in blob
    assert "api_key" not in blob
    assert "%pdf" not in blob
    assert "sk-secret" not in blob
    assert "data:application/pdf" not in blob
    for bad in ("raw_pdf", "file_bytes", "api_key"):
        assert bad in FORBIDDEN_PAYLOAD_KEYS


def test_harvest_does_not_patch_label_aliases(tmp_path: Path):
    before = EXTRACT_PATH.read_text(encoding="utf-8")
    store = _write_jsonl(
        tmp_path / "signals.jsonl",
        [
            _edit("operating_revenue", 1, 2),
            _edit("operating_revenue", 3, 4),
            _edit("operating_revenue", 5, 6),
        ],
    )
    harvest_from_jsonl(store, min_count=3)
    after = EXTRACT_PATH.read_text(encoding="utf-8")
    assert after == before
    assert "_LABEL_ALIASES" in after


def test_write_reports_markdown_and_json(tmp_path: Path):
    store = _write_jsonl(
        tmp_path / "signals.jsonl",
        [
            _edit("total_equity", 1, 2, ticker="REE"),
            _edit("total_equity", 3, 4, ticker="REE"),
            _edit("total_equity", 5, 6, ticker="REE"),
        ],
    )
    report = harvest_from_jsonl(store, min_count=3)
    md_path = tmp_path / "out.md"
    json_path = tmp_path / "out.json"
    markdown, payload = write_reports(report, markdown_path=md_path, json_path=json_path)
    assert md_path.read_text(encoding="utf-8") == markdown
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert saved["auto_applied"] is False
    assert saved["aliases_written"] is False
    assert saved["proposals"][0]["kind"] == "review_aliases"
    assert "raw_pdf" not in markdown.lower()
    assert payload["min_count"] == 3


def test_committed_fixture_harvests_operating_revenue():
    report = harvest_from_jsonl(FIXTURE_PATH, min_count=3)
    assert report.field_counts["operating_revenue"] == 3
    assert report.field_counts["employees"] == 2
    kinds = {p.kind for p in report.proposals if p.field == "operating_revenue"}
    assert "review_aliases" in kinds
    assert "review_unit_scale" in kinds
    assert not any(p.field == "employees" for p in report.proposals)
    markdown = render_markdown(report)
    assert "raw_pdf" not in markdown.lower()
