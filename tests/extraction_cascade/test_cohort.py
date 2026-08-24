"""Cohort builders for listed28 + optional frame URLs."""

from __future__ import annotations

import json
from pathlib import Path

from crawlers.extraction_cascade.cohort import (
    build_cohort,
    listed28_cohort,
    load_frame_urls_file,
)


def test_listed28_has_urls():
    firms = listed28_cohort()
    assert len(firms) == 28
    assert all(f.website_url for f in firms)
    assert all(f.source_cohort == "listed28" for f in firms)


def test_load_frame_urls_file(tmp_path: Path):
    path = tmp_path / "frame_urls.json"
    path.write_text(
        json.dumps(
            [
                {
                    "firm_id": "0100123456",
                    "tax_code": "0100123456",
                    "website_url": "https://example-frame.vn",
                    "company_name": "DN A",
                    "vsic_4digit": "1010",
                }
            ]
        ),
        encoding="utf-8",
    )
    rows = load_frame_urls_file(path)
    assert len(rows) == 1
    assert rows[0].source_cohort == "frame_pilot"
    assert rows[0].website_url.endswith("example-frame.vn")


def test_build_cohort_merges_frame(tmp_path: Path, monkeypatch):
    path = tmp_path / "frame_urls.json"
    path.write_text(
        json.dumps(
            [{"firm_id": "TAX1", "website_url": "https://frame.example/", "name": "F"}]
        ),
        encoding="utf-8",
    )
    firms = build_cohort(frame_urls_path=path)
    assert any(f.firm_id == "TAX1" for f in firms)
    assert sum(1 for f in firms if f.source_cohort == "listed28") == 28
