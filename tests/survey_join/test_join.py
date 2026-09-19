"""Join keys, unmatched rows, disagreement — synthetic MST/ticker only."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from crawlers.survey_join.join import (
    OUTPUT_COLUMNS,
    SURVEY_COLUMNS,
    SurveyJoinError,
    disagreements,
    index_cascade,
    join_rows,
    join_survey,
    load_survey_csv,
    match_cascade,
    normalize_mst,
    web_flags_from_cascade,
)
from crawlers.survey_join.paths import SEED_COMPANIES_JSON, SURVEY_COLUMNS as PATH_COLS

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _survey(**overrides: str) -> dict[str, str]:
    row = {c: "" for c in SURVEY_COLUMNS}
    row.update(overrides)
    return row


def _write_survey_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(SURVEY_COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in SURVEY_COLUMNS})


SYNTHETIC_LISTED_MST = "0000000001"
SYNTHETIC_LISTED_TICKER = "TEST"
UNKNOWN_MST = "2222222222"


def test_normalize_mst_strips_spaces_keeps_hyphen():
    assert normalize_mst(" 0101552800-003 ") == "0101552800-003"
    assert normalize_mst("010 155 2800-003") == "0101552800-003"
    assert normalize_mst("0101552800-003") != normalize_mst("0101552800")


def test_match_order_mst_before_ticker():
    cascade = index_cascade(
        [
            {
                "firm_id": "0000000000",
                "source_cohort": "frame_pilot",
                "fetch_ok": True,
                "tier1": {"has_order_cart": True},
            },
            {
                "firm_id": "TEST",
                "source_cohort": "listed28",
                "fetch_ok": True,
                "tier1": {"has_order_cart": False},
            },
        ]
    )
    rec, via = match_cascade(
        mst="0000000000",
        ticker="TEST",
        cascade_by_id=cascade,
        frame_tax_codes=set(),
    )
    assert via == "mst"
    assert rec is not None
    assert rec["firm_id"] == "0000000000"


def test_match_via_ticker_when_mst_misses():
    cascade = index_cascade(
        [{"firm_id": "TEST", "source_cohort": "listed28", "fetch_ok": True, "tier1": {}}]
    )
    rec, via = match_cascade(
        mst="1111111111",
        ticker="TEST",
        cascade_by_id=cascade,
        frame_tax_codes=set(),
    )
    assert via == "ticker"
    assert rec is not None
    assert rec["firm_id"] == "TEST"


def test_frame_pilot_tax_code_maps_when_in_cascade():
    cascade = index_cascade(
        [
            {
                "firm_id": "0000000000-001",
                "source_cohort": "frame_pilot",
                "fetch_ok": True,
                "tier1": {"has_order_cart": False},
            }
        ]
    )
    rec, via = match_cascade(
        mst="0000000000-001",
        ticker="TEST",
        cascade_by_id=cascade,
        frame_tax_codes={"0000000000-001"},
    )
    assert rec is not None
    assert rec["firm_id"] == "0000000000-001"
    assert via == "frame_pilot"


def test_in_frame_pilot_but_not_cascade_does_not_invent_website():
    rows = join_rows(
        [_survey(mst="8888888888", company_name="Frame Only")],
        cascade_records=[],
        frame_tax_codes={"8888888888"},
    )
    assert len(rows) == 1
    assert rows[0]["web_match"] is False
    assert rows[0]["in_frame_pilot"] is True
    assert rows[0]["web_website_url"] is None
    assert rows[0]["web_has_order_cart"] is None


def test_unmatched_row_kept_with_null_web_flags():
    rows = join_rows(
        [_survey(mst="9999999999", has_order_cart="true")],
        cascade_records=[
            {"firm_id": "TEST", "source_cohort": "listed28", "fetch_ok": True, "tier1": {}}
        ],
        frame_tax_codes=set(),
    )
    assert rows[0]["web_match"] is False
    assert rows[0]["web_match_via"] is None
    assert rows[0]["web_fetch_ok"] is None
    assert rows[0]["disagree_has_order_cart"] is None


def test_disagree_only_when_fetch_ok():
    survey = _survey(has_order_cart="false", has_website="true")
    ok_web = web_flags_from_cascade(
        {
            "firm_id": "0000000000",
            "fetch_ok": True,
            "tier1": {
                "has_product_catalog": True,
                "has_order_cart": True,
                "payment_methods": [],
                "social_links": [],
                "marketplace_links": [],
            },
        }
    )
    disag_ok = disagreements(survey, ok_web, fetch_ok=True)
    assert disag_ok["disagree_has_order_cart"] is True

    fail_web = web_flags_from_cascade(
        {"firm_id": "0000000000", "fetch_ok": False, "website_url": "https://x.example"}
    )
    disag_fail = disagreements(survey, fail_web, fetch_ok=False)
    assert disag_fail["disagree_has_order_cart"] is None
    assert fail_web["web_has_order_cart"] is None
    assert fail_web["web_website_url"] == "https://x.example"
    assert fail_web["web_fetch_ok"] is False


def test_fixture_join_end_to_end(tmp_path: Path):
    result = join_survey(
        survey_path=FIXTURES / "survey.csv",
        out_dir=tmp_path,
        cascade_path=FIXTURES / "cascade.jsonl",
        frame_pilot_path=FIXTURES / "frame_pilot.csv",
    )
    rows = {r["mst_normalized"]: r for r in result["rows"]}
    assert set(rows) == {"0000000000", "1111111111", "9999999999"}

    mst_row = rows["0000000000"]
    assert mst_row["web_match"] is True
    assert mst_row["web_match_via"] == "frame_pilot"
    assert mst_row["in_frame_pilot"] is True
    assert mst_row["web_has_order_cart"] is True
    assert mst_row["disagree_has_order_cart"] is True
    assert mst_row["estimated_online_revenue"] == 175_000_000
    assert mst_row["estimate_skipped_reason"] is None

    ticker_row = rows["1111111111"]
    assert ticker_row["web_match"] is True
    assert ticker_row["web_match_via"] == "ticker"
    assert ticker_row["web_firm_id"] == "TEST"
    assert ticker_row["estimated_online_revenue"] is None
    assert ticker_row["estimate_skipped_reason"] == "missing_revenue"
    assert ticker_row["disagree_has_order_cart"] is False

    unmatched = rows["9999999999"]
    assert unmatched["web_match"] is False
    assert unmatched["web_has_order_cart"] is None
    assert unmatched["estimated_online_revenue"] is None
    assert unmatched["estimate_skipped_reason"] == "bin_unknown"

    summary = result["summary"]
    assert summary["n_survey_rows"] == 3
    assert summary["n_web_matched"] == 2
    assert summary["n_web_unmatched"] == 1
    assert summary["used_seed_financials"] is False
    assert summary["real_survey_responses_exist"] is False
    assert not SEED_COMPANIES_JSON.samefile(FIXTURES / "survey.csv")

    jsonl = (tmp_path / "joined.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(jsonl) == 3
    parsed = [json.loads(line) for line in jsonl]
    assert all(set(OUTPUT_COLUMNS) <= set(p) for p in parsed)


def test_missing_survey_file_errors(tmp_path: Path):
    with pytest.raises(SurveyJoinError, match="not found"):
        join_survey(
            survey_path=tmp_path / "missing.csv",
            out_dir=tmp_path / "out",
            cascade_path=FIXTURES / "cascade.jsonl",
            frame_pilot_path=FIXTURES / "frame_pilot.csv",
        )
    assert not (tmp_path / "out" / "joined.csv").exists()


def test_empty_survey_file_errors(tmp_path: Path):
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(SurveyJoinError, match="empty"):
        join_survey(
            survey_path=empty,
            out_dir=tmp_path / "out",
            cascade_path=FIXTURES / "cascade.jsonl",
            frame_pilot_path=FIXTURES / "frame_pilot.csv",
        )
    assert not (tmp_path / "out" / "joined.csv").exists()


def test_header_only_survey_errors(tmp_path: Path):
    header_only = tmp_path / "header.csv"
    header_only.write_text(",".join(PATH_COLS) + "\n", encoding="utf-8")
    with pytest.raises(SurveyJoinError, match="no data rows"):
        load_survey_csv(header_only)


def test_fixture_survey_is_not_real_frame_pilot_rows():
    text = (FIXTURES / "survey.csv").read_text(encoding="utf-8")
    assert "0101552800" not in text
    assert "masothue" not in text.lower()
    rows = load_survey_csv(FIXTURES / "survey.csv")
    assert len(rows) == 3
    assert {r["ticker"].strip() for r in rows} <= {"", "TEST"}


def test_mst_only_joins_listed_via_identity_tax_id(tmp_path: Path):
    identity = tmp_path / "identity.json"
    identity.write_text(
        json.dumps(
            [
                {
                    "ticker": SYNTHETIC_LISTED_TICKER,
                    "tax_id": f" {SYNTHETIC_LISTED_MST} ",
                }
            ]
        ),
        encoding="utf-8",
    )
    cascade = tmp_path / "cascade.jsonl"
    cascade.write_text(
        json.dumps(
            {
                "firm_id": SYNTHETIC_LISTED_TICKER,
                "source_cohort": "listed28",
                "website_url": "https://test.example",
                "fetch_ok": True,
                "tier1": {"has_order_cart": False},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    survey = tmp_path / "survey.csv"
    _write_survey_csv(
        survey,
        [_survey(mst=SYNTHETIC_LISTED_MST, company_name="Synthetic listed MST only")],
    )
    survey_text = survey.read_text(encoding="utf-8")
    assert "0101526991" not in survey_text
    assert "RAL" not in survey_text

    result = join_survey(
        survey_path=survey,
        out_dir=tmp_path / "out",
        cascade_path=cascade,
        identity_path=identity,
    )
    row = result["rows"][0]
    assert row["web_match"] is True
    assert row["web_match_via"] == "listed_tax_id"
    assert row["web_firm_id"] == SYNTHETIC_LISTED_TICKER
    assert row["ticker_normalized"] is None
    assert result["summary"]["n_matched_via"]["listed_tax_id"] == 1


def test_unknown_mst_unmatched_even_when_identity_present(tmp_path: Path):
    identity = tmp_path / "identity.json"
    identity.write_text(
        json.dumps([{"ticker": SYNTHETIC_LISTED_TICKER, "tax_id": SYNTHETIC_LISTED_MST}]),
        encoding="utf-8",
    )
    cascade = tmp_path / "cascade.jsonl"
    cascade.write_text(
        json.dumps(
            {
                "firm_id": SYNTHETIC_LISTED_TICKER,
                "source_cohort": "listed28",
                "website_url": "https://test.example",
                "fetch_ok": True,
                "tier1": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    survey = tmp_path / "survey.csv"
    _write_survey_csv(survey, [_survey(mst=UNKNOWN_MST, company_name="Unknown MST")])
    assert "0101526991" not in survey.read_text(encoding="utf-8")

    result = join_survey(
        survey_path=survey,
        out_dir=tmp_path / "out",
        cascade_path=cascade,
        identity_path=identity,
    )
    row = result["rows"][0]
    assert row["web_match"] is False
    assert row["web_match_via"] is None
    assert row["web_firm_id"] is None
    assert row["web_website_url"] is None
    assert row["web_has_website"] is None


def test_missing_identity_file_skips_listed_tax_id(tmp_path: Path):
    cascade = tmp_path / "cascade.jsonl"
    cascade.write_text(
        json.dumps(
            {
                "firm_id": SYNTHETIC_LISTED_TICKER,
                "source_cohort": "listed28",
                "website_url": "https://test.example",
                "fetch_ok": True,
                "tier1": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    survey = tmp_path / "survey.csv"
    _write_survey_csv(survey, [_survey(mst=SYNTHETIC_LISTED_MST)])
    result = join_survey(
        survey_path=survey,
        out_dir=tmp_path / "out",
        cascade_path=cascade,
        identity_path=tmp_path / "missing_identity.json",
    )
    row = result["rows"][0]
    assert row["web_match"] is False
    assert row["web_match_via"] is None
    assert row["web_website_url"] is None


def test_ticker_wins_over_listed_tax_id():
    cascade = index_cascade(
        [
            {
                "firm_id": SYNTHETIC_LISTED_TICKER,
                "source_cohort": "listed28",
                "fetch_ok": True,
                "tier1": {},
            },
            {
                "firm_id": "OTHR",
                "source_cohort": "listed28",
                "fetch_ok": True,
                "tier1": {},
            },
        ]
    )
    rec, via = match_cascade(
        mst=SYNTHETIC_LISTED_MST,
        ticker="OTHR",
        cascade_by_id=cascade,
        frame_tax_codes=set(),
        tax_id_to_ticker={SYNTHETIC_LISTED_MST: SYNTHETIC_LISTED_TICKER},
    )
    assert via == "ticker"
    assert rec is not None
    assert rec["firm_id"] == "OTHR"
