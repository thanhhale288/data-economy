"""Task #94 — BCTC extract vs historical DB financial_reports consistency check.

Compares a set of extracted/manually entered fields (from extract or prefill)
against the latest annual report stored in DB for the same ticker.
Returns explicit flags — never silently overwrites, never invents discrepancies.

Field mapping:
  extract field       ← → FinancialReport column
  operating_revenue       revenue
  profit_before_tax       profit_before_tax
  total_assets            total_assets
  total_equity            total_equity
  employees               employees
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from backend.app.models import Company, FinancialReport

# Relative deviation threshold before flagging as a discrepancy.
_DEFAULT_REL_THRESHOLD = 0.10  # 10 %

# Extract field → FinancialReport column name.
# Only numeric fields that appear in both surfaces.
CONSISTENCY_FIELD_MAP: dict[str, str] = {
    "operating_revenue": "revenue",
    "profit_before_tax": "profit_before_tax",
    "total_assets": "total_assets",
    "total_equity": "total_equity",
    "employees": "employees",
}

FlagSeverity = Literal["ok", "warn", "mismatch"]


@dataclass
class ConsistencyFlag:
    """Single-field consistency result."""

    extract_field: str
    db_column: str
    extract_value: float | int | None
    db_value: float | int | None
    rel_deviation: float | None
    severity: FlagSeverity
    note: str


@dataclass
class ConsistencyReport:
    """Full consistency report for one extract-vs-ticker comparison."""

    ticker: str
    period: str | None
    report_type: str | None
    flags: list[ConsistencyFlag]
    has_db_record: bool
    summary: str


def _rel_deviation(a: float | None, b: float | None) -> float | None:
    """|a − b| / |b| — None when either side is missing or b == 0."""
    if a is None or b is None or b == 0:
        return None
    return abs(a - b) / abs(b)


def _flag_severity(rel_dev: float | None) -> FlagSeverity:
    if rel_dev is None:
        return "warn"
    if rel_dev < _DEFAULT_REL_THRESHOLD:
        return "ok"
    return "mismatch"


def _latest_annual(db: Session, stock_code: str) -> FinancialReport | None:
    company = (
        db.query(Company).filter(Company.stock_code == stock_code.upper()).first()
    )
    if not company:
        return None
    return (
        db.query(FinancialReport)
        .filter(
            FinancialReport.company_id == company.id,
            FinancialReport.report_type == "annual",
        )
        .order_by(FinancialReport.period.desc())
        .first()
    )


def check_consistency(
    db: Session,
    ticker: str,
    extract_fields: dict[str, float | int | None],
    *,
    rel_threshold: float = _DEFAULT_REL_THRESHOLD,
) -> ConsistencyReport:
    """Compare *extract_fields* to the latest annual FinancialReport for *ticker*.

    Always returns a ConsistencyReport — callers decide what to show.
    When no DB record exists ``has_db_record=False`` and all flags are "warn".
    """
    report = _latest_annual(db, ticker)

    if report is None:
        flags = [
            ConsistencyFlag(
                extract_field=ef,
                db_column=db_col,
                extract_value=extract_fields.get(ef),
                db_value=None,
                rel_deviation=None,
                severity="warn",
                note="no_db_record",
            )
            for ef, db_col in CONSISTENCY_FIELD_MAP.items()
        ]
        return ConsistencyReport(
            ticker=ticker.upper(),
            period=None,
            report_type=None,
            flags=flags,
            has_db_record=False,
            summary=f"Không tìm thấy BCTC lịch sử cho {ticker.upper()} trong DB.",
        )

    flags: list[ConsistencyFlag] = []
    mismatches = 0
    warns = 0

    for ef, db_col in CONSISTENCY_FIELD_MAP.items():
        ex_val = extract_fields.get(ef)
        db_val = getattr(report, db_col, None)

        if ex_val is None and db_val is None:
            severity: FlagSeverity = "ok"
            note = "both_null"
            rel_dev = None
        elif ex_val is None:
            severity = "warn"
            note = "extract_null"
            rel_dev = None
        elif db_val is None:
            severity = "warn"
            note = "db_null"
            rel_dev = None
        else:
            rel_dev = _rel_deviation(float(ex_val), float(db_val))
            severity = "ok" if (rel_dev is not None and rel_dev < rel_threshold) else "mismatch"
            note = f"rel_dev={rel_dev:.3f}" if rel_dev is not None else "zero_db"

        if severity == "mismatch":
            mismatches += 1
        elif severity == "warn":
            warns += 1

        flags.append(
            ConsistencyFlag(
                extract_field=ef,
                db_column=db_col,
                extract_value=ex_val,
                db_value=db_val,
                rel_deviation=rel_dev,
                severity=severity,
                note=note,
            )
        )

    if mismatches:
        summary = (
            f"{mismatches} trường lệch ≥{int(rel_threshold*100)}% so với BCTC kỳ "
            f"{report.period} của {ticker.upper()}. "
            "Kiểm tra trước khi compare."
        )
    elif warns:
        summary = (
            f"Thiếu dữ liệu ở {warns} trường — không đủ để so sánh hoàn toàn với "
            f"BCTC kỳ {report.period} của {ticker.upper()}."
        )
    else:
        summary = (
            f"Tất cả trường nhất quán với BCTC kỳ {report.period} của {ticker.upper()} "
            f"(lệch < {int(rel_threshold*100)}%)."
        )

    return ConsistencyReport(
        ticker=ticker.upper(),
        period=str(report.period),
        report_type=report.report_type,
        flags=flags,
        has_db_record=True,
        summary=summary,
    )
