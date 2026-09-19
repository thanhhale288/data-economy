"""CLI wiring for survey join (offline, fixture paths only)."""

from __future__ import annotations

from pathlib import Path

from crawlers.survey_join.__main__ import main

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_cli_writes_joined_artifacts(tmp_path: Path):
    out = tmp_path / "out"
    rc = main(
        [
            "--survey",
            str(FIXTURES / "survey.csv"),
            "--out",
            str(out),
            "--cascade",
            str(FIXTURES / "cascade.jsonl"),
            "--frame-pilot",
            str(FIXTURES / "frame_pilot.csv"),
        ]
    )
    assert rc == 0
    assert (out / "joined.csv").exists()
    assert (out / "joined.jsonl").exists()
    assert (out / "summary.json").exists()
    csv_text = (out / "joined.csv").read_text(encoding="utf-8")
    assert "0000000000" in csv_text
    assert "175000000" in csv_text
    assert "TEST" in csv_text


def test_cli_recode_google_form_fixture(tmp_path: Path):
    dest = tmp_path / "locked.csv"
    rc = main(
        [
            "recode",
            "--src",
            str(FIXTURES / "google_form_vi.csv"),
            "--dest",
            str(dest),
        ]
    )
    assert rc == 0
    assert dest.exists()
    text = dest.read_text(encoding="utf-8")
    assert text.splitlines()[0].startswith("mst,company_name")
    assert "0000000000" in text


def test_cli_plan_writes_unmatched_json(tmp_path: Path):
    out = tmp_path / "plan"
    rc = main(
        [
            "plan",
            "--survey",
            str(FIXTURES / "survey.csv"),
            "--out",
            str(out),
            "--cascade",
            str(FIXTURES / "cascade.jsonl"),
            "--frame-pilot",
            str(FIXTURES / "frame_pilot.csv"),
            "--identity",
            str(tmp_path / "missing_identity.json"),
        ]
    )
    assert rc == 0
    plan_path = out / "unmatched_plan.json"
    cohort_path = out / "frame_urls_self_report.json"
    assert plan_path.exists()
    assert cohort_path.exists()


def test_cli_missing_survey_returns_2(tmp_path: Path, capsys):
    rc = main(
        [
            "--survey",
            str(tmp_path / "nope.csv"),
            "--out",
            str(tmp_path / "out"),
            "--cascade",
            str(FIXTURES / "cascade.jsonl"),
            "--frame-pilot",
            str(FIXTURES / "frame_pilot.csv"),
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "not found" in err
    assert not (tmp_path / "out" / "joined.csv").exists()
