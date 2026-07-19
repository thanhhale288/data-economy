"""Unit tests for pipeline.cleaning.vsic_validation (no DB required)."""

from __future__ import annotations

from pipeline.cleaning.vsic_validation import (
    REASON_MISSING_CODE,
    REASON_NOT_SECTION_C,
    REASON_UNKNOWN_CODE,
    validate_vsic_codes,
)


VALID_CODES = {"C", "10", "24", "2740", "2410", "1050"}


def test_validate_vsic_codes_accepts_valid():
    issues = validate_vsic_codes(["2740", "C", "10"], VALID_CODES)
    assert issues == []


def test_validate_vsic_codes_missing_code():
    issues = validate_vsic_codes([None, "", "  "], VALID_CODES)
    assert len(issues) == 3
    assert all(i.reason == REASON_MISSING_CODE for i in issues)
    assert issues[0].vsic_code is None


def test_validate_vsic_codes_unknown_section_c_shape():
    # Looks like Section C (division 27 class) but not in reference set.
    issues = validate_vsic_codes(["2799"], VALID_CODES)
    assert len(issues) == 1
    assert issues[0].reason == REASON_UNKNOWN_CODE
    assert issues[0].vsic_code == "2799"


def test_validate_vsic_codes_not_section_c():
    # Agriculture / services shapes — not Section C manufacturing.
    issues = validate_vsic_codes(["A", "01", "6201"], VALID_CODES)
    assert len(issues) == 3
    assert all(i.reason == REASON_NOT_SECTION_C for i in issues)


def test_validate_vsic_codes_strips_whitespace():
    issues = validate_vsic_codes([" 2740 ", "C"], VALID_CODES)
    assert issues == []


def test_validate_vsic_codes_entity_ids_parallel():
    issues = validate_vsic_codes(
        [None, "A"],
        VALID_CODES,
        entity_type="company",
        entity_ids=["RAL", "HPG"],
    )
    assert [i.entity_id for i in issues] == ["RAL", "HPG"]
    assert issues[0].reason == REASON_MISSING_CODE
    assert issues[1].reason == REASON_NOT_SECTION_C


def test_validate_vsic_codes_default_entity_id_is_index():
    issues = validate_vsic_codes(["ZZ"], VALID_CODES)
    assert issues[0].entity_id == 0
    assert issues[0].reason == REASON_NOT_SECTION_C


def test_validate_vsic_optional_db_path(db_session, seeded_cleaning_db):
    """Light DB check when sqlite fixture is available (optional path)."""
    from pipeline.cleaning.vsic_validation import validate_vsic

    report = validate_vsic(seeded_cleaning_db)
    assert report.companies_checked >= 1
    assert report.gso_checked >= 1
    assert report.valid_code_count >= 1
    assert report.companies_fail == 0
    assert report.gso_fail == 0
    d = report.to_dict()
    assert "issues" in d
