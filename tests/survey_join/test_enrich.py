"""Unmatched-survey plan: self-report URL, URL-finder, or unactionable. No invented hosts."""

from __future__ import annotations

from pathlib import Path

import crawlers.survey_join.enrich as enrich_mod
from crawlers.survey_join.enrich import cohort_from_self_report, plan_unmatched

SYNTH_MATCHED = "0000000000"
SYNTH_UNMATCHED = "9999999999"


def _survey(**overrides: str) -> dict[str, str]:
    row = {
        "mst": "",
        "company_name": "",
        "ticker": "",
        "website_url_self_report": "",
    }
    row.update(overrides)
    return row


def _cascade_mst() -> list[dict]:
    return [{"firm_id": SYNTH_MATCHED, "source_cohort": "frame_pilot", "fetch_ok": True}]


def _cascade_ticker() -> list[dict]:
    return [{"firm_id": "TEST", "source_cohort": "listed28", "fetch_ok": True}]


def test_matched_cascade_mst_skipped():
    plan = plan_unmatched(
        [_survey(mst=SYNTH_MATCHED, company_name="Already In Cascade")],
        _cascade_mst(),
    )
    assert plan == []


def test_matched_self_report_still_skipped():
    plan = plan_unmatched(
        [
            _survey(
                mst=SYNTH_MATCHED,
                company_name="Already In Cascade",
                website_url_self_report="https://already-in-cascade.example",
            )
        ],
        _cascade_mst(),
    )
    assert plan == []


def test_matched_via_frame_pilot_skipped():
    plan = plan_unmatched(
        [_survey(mst=SYNTH_MATCHED, company_name="Frame Firm")],
        _cascade_mst(),
        frame_tax_codes={SYNTH_MATCHED},
    )
    assert plan == []


def test_matched_via_ticker_skipped():
    plan = plan_unmatched(
        [_survey(mst=SYNTH_UNMATCHED, ticker="TEST", company_name="Listed")],
        _cascade_ticker(),
    )
    assert plan == []


def test_matched_via_listed_tax_to_ticker_skipped():
    plan = plan_unmatched(
        [_survey(mst=SYNTH_MATCHED, company_name="Listed Via Map")],
        _cascade_ticker(),
        listed_tax_to_ticker={SYNTH_MATCHED: "TEST"},
    )
    assert plan == []


def test_unmatched_https_self_report_plans_cascade():
    url = "https://fake-unmatched.example/shop"
    plan = plan_unmatched(
        [
            _survey(
                mst=SYNTH_UNMATCHED,
                company_name="Unmatched Co",
                website_url_self_report=url,
            )
        ],
        _cascade_mst(),
    )
    assert len(plan) == 1
    assert plan[0]["action"] == "cascade_self_report"
    assert plan[0]["website_url"] == url
    assert plan[0]["mst"] == SYNTH_UNMATCHED
    assert plan[0]["reason"] is None


def test_unmatched_http_self_report_accepted():
    url = "http://fake-unmatched.example"
    plan = plan_unmatched(
        [_survey(mst=SYNTH_UNMATCHED, website_url_self_report=url)],
        [],
    )
    assert plan[0]["action"] == "cascade_self_report"
    assert plan[0]["website_url"] == url


def test_unmatched_name_mst_needs_url_finder_without_guessed_domain():
    plan = plan_unmatched(
        [_survey(mst=SYNTH_UNMATCHED, company_name="Cong ty ABC")],
        _cascade_mst(),
    )
    assert len(plan) == 1
    assert plan[0]["action"] == "needs_url_finder"
    assert plan[0]["website_url"] is None
    blob = " ".join(str(v) for v in plan[0].values())
    assert "abc.com" not in blob.lower()
    assert "congtyabc" not in blob.lower()


def test_non_http_self_report_is_not_cascade_url():
    plan = plan_unmatched(
        [
            _survey(
                mst=SYNTH_UNMATCHED,
                company_name="Bare Domain Co",
                website_url_self_report="fake-unmatched.example",
            )
        ],
        [],
    )
    assert plan[0]["action"] == "needs_url_finder"
    assert plan[0]["website_url"] is None


def test_unmatched_missing_fields_unactionable():
    no_name = plan_unmatched([_survey(mst=SYNTH_UNMATCHED)], [])
    assert no_name[0]["action"] == "unactionable"
    assert no_name[0]["website_url"] is None
    assert "missing_fields" in no_name[0]["reason"]
    assert "company_name" in no_name[0]["reason"]

    no_mst = plan_unmatched([_survey(company_name="Nameless MST")], [])
    assert no_mst[0]["action"] == "unactionable"
    assert no_mst[0]["website_url"] is None
    assert "missing_fields" in no_mst[0]["reason"]
    assert "mst" in no_mst[0]["reason"]


def test_cohort_from_self_report_frame_url_shape():
    url = "https://fake-unmatched.example"
    plan = plan_unmatched(
        [
            _survey(
                mst=SYNTH_UNMATCHED,
                company_name="Unmatched Co",
                website_url_self_report=url,
            ),
            _survey(mst=SYNTH_UNMATCHED, company_name="Needs Finder Co"),
            _survey(mst=SYNTH_UNMATCHED),
        ],
        [],
    )
    assert [p["action"] for p in plan] == [
        "cascade_self_report",
        "needs_url_finder",
        "unactionable",
    ]
    cohort = cohort_from_self_report(plan)
    assert len(cohort) == 1
    assert set(cohort[0]) == {
        "firm_id",
        "tax_code",
        "website_url",
        "name",
        "notes",
    }
    assert cohort[0]["firm_id"] == SYNTH_UNMATCHED
    assert cohort[0]["tax_code"] == SYNTH_UNMATCHED
    assert cohort[0]["website_url"] == url
    assert cohort[0]["name"] == "Unmatched Co"
    assert "self_report" in cohort[0]["notes"]


def test_enrich_has_no_http_fetch():
    source = Path(enrich_mod.__file__).read_text(encoding="utf-8")
    assert "httpx" not in source
    assert "requests" not in source
    assert "urllib.request" not in source
    assert "urlopen" not in source
    assert "fetch(" not in source
