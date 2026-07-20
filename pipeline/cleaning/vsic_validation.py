"""Validate company and GSO macro VSIC codes against the seeded reference table.

Does not auto-correct codes — only flags and reports issues.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models import Company, GsoMacro, VsicCode

logger = logging.getLogger(__name__)

REASON_MISSING_CODE = "missing_code"
REASON_UNKNOWN_CODE = "unknown_code"
REASON_NOT_SECTION_C = "not_section_c"

ENTITY_COMPANY = "company"
ENTITY_GSO_MACRO = "gso_macro"

# VSIC Section C manufacturing divisions (level 2).
_SECTION_C_DIVISIONS = {f"{n:02d}" for n in range(10, 34)}


@dataclass
class VsicIssue:
    entity_type: str  # "company" | "gso_macro"
    entity_id: str | int | None
    vsic_code: str | None
    reason: str  # "missing_code" | "unknown_code" | "not_section_c"


@dataclass
class VsicValidationReport:
    companies_checked: int
    companies_ok: int
    companies_fail: int
    gso_checked: int
    gso_ok: int
    gso_fail: int
    issues: list[VsicIssue] = field(default_factory=list)
    valid_code_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "companies_checked": self.companies_checked,
            "companies_ok": self.companies_ok,
            "companies_fail": self.companies_fail,
            "gso_checked": self.gso_checked,
            "gso_ok": self.gso_ok,
            "gso_fail": self.gso_fail,
            "valid_code_count": self.valid_code_count,
            "issues": [asdict(issue) for issue in self.issues],
        }


def _normalize_code(code: str | None) -> str | None:
    if code is None:
        return None
    stripped = str(code).strip()
    return stripped if stripped else None


def _looks_like_section_c(code: str) -> bool:
    """Deterministic shape check for Section C codes (C / 10–33 / 4-digit class)."""
    if code == "C":
        return True
    if code in _SECTION_C_DIVISIONS:
        return True
    if len(code) == 4 and code.isdigit() and code[:2] in _SECTION_C_DIVISIONS:
        return True
    return False


def _classify_invalid(code: str | None, valid_codes: set[str]) -> str:
    """Return reason for an invalid (missing or unknown) code. Never invents a mapping."""
    if code is None:
        return REASON_MISSING_CODE
    if code in valid_codes:
        raise ValueError("valid code passed to _classify_invalid")
    if not _looks_like_section_c(code):
        return REASON_NOT_SECTION_C
    return REASON_UNKNOWN_CODE


def validate_vsic_codes(
    codes: Iterable[str | None],
    valid_codes: set[str],
    *,
    entity_type: str = ENTITY_COMPANY,
    entity_ids: Iterable[str | int | None] | None = None,
) -> list[VsicIssue]:
    """Validate an iterable of VSIC codes against a reference set (no DB).

    ``entity_ids`` may be provided in parallel with ``codes``; otherwise
    ``entity_id`` is the 0-based index of the code in the input.
    """
    id_list = list(entity_ids) if entity_ids is not None else None
    issues: list[VsicIssue] = []
    for i, raw in enumerate(codes):
        code = _normalize_code(raw)
        entity_id: str | int | None = id_list[i] if id_list is not None else i
        if code is None:
            issues.append(
                VsicIssue(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    vsic_code=None if raw is None else (str(raw).strip() or None),
                    reason=REASON_MISSING_CODE,
                )
            )
            continue
        if code not in valid_codes:
            issues.append(
                VsicIssue(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    vsic_code=code,
                    reason=_classify_invalid(code, valid_codes),
                )
            )
    return issues


def _load_valid_codes(db: Session) -> set[str]:
    rows = db.query(VsicCode.vsic_code).all()
    return {row[0] for row in rows if row[0]}


def validate_vsic(db: Session) -> VsicValidationReport:
    """Validate all company and gso_macro VSIC codes against ``vsic_codes``.

    Flags only — does not mutate rows or invent corrections.
    """
    valid_codes = _load_valid_codes(db)
    valid_code_count = len(valid_codes)
    issues: list[VsicIssue] = []

    companies = db.query(Company).all()
    companies_checked = len(companies)
    companies_fail = 0
    for company in companies:
        code = _normalize_code(company.vsic_code)
        entity_id = company.stock_code or company.id
        if code is None:
            companies_fail += 1
            issues.append(
                VsicIssue(
                    entity_type=ENTITY_COMPANY,
                    entity_id=entity_id,
                    vsic_code=None,
                    reason=REASON_MISSING_CODE,
                )
            )
            continue
        if code not in valid_codes:
            companies_fail += 1
            issues.append(
                VsicIssue(
                    entity_type=ENTITY_COMPANY,
                    entity_id=entity_id,
                    vsic_code=code,
                    reason=_classify_invalid(code, valid_codes),
                )
            )

    companies_ok = companies_checked - companies_fail

    gso_rows = db.query(GsoMacro).all()
    gso_checked = len(gso_rows)
    gso_fail = 0
    for row in gso_rows:
        code = _normalize_code(row.vsic_code)
        if code is None:
            gso_fail += 1
            issues.append(
                VsicIssue(
                    entity_type=ENTITY_GSO_MACRO,
                    entity_id=row.id,
                    vsic_code=None,
                    reason=REASON_MISSING_CODE,
                )
            )
            continue
        if code not in valid_codes:
            gso_fail += 1
            issues.append(
                VsicIssue(
                    entity_type=ENTITY_GSO_MACRO,
                    entity_id=row.id,
                    vsic_code=code,
                    reason=_classify_invalid(code, valid_codes),
                )
            )

    gso_ok = gso_checked - gso_fail

    report = VsicValidationReport(
        companies_checked=companies_checked,
        companies_ok=companies_ok,
        companies_fail=companies_fail,
        gso_checked=gso_checked,
        gso_ok=gso_ok,
        gso_fail=gso_fail,
        issues=issues,
        valid_code_count=valid_code_count,
    )

    logger.info(
        "VSIC validation: companies ok=%s fail=%s/%s; gso ok=%s fail=%s/%s; "
        "valid_codes=%s issues=%s",
        companies_ok,
        companies_fail,
        companies_checked,
        gso_ok,
        gso_fail,
        gso_checked,
        valid_code_count,
        len(issues),
    )
    for issue in issues:
        logger.warning(
            "VSIC issue entity_type=%s entity_id=%s vsic_code=%r reason=%s",
            issue.entity_type,
            issue.entity_id,
            issue.vsic_code,
            issue.reason,
        )

    return report
