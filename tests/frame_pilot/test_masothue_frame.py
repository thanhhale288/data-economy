from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crawlers.companies.masothue_frame import max_page_from_listing, parse_listing_page


FIXTURE = Path("tests/frame_pilot/fixtures/listing_2220_page1.html")


def test_parse_listing_fixture_extracts_rows() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    rows = parse_listing_page(
        html,
        vsic_4digit="2220",
        listing_url="https://www.masothue.com/tra-cuu-ma-so-thue-theo-nganh-nghe/san-xuat-san-pham-tu-plastic-2220",
        retrieved_at="2026-08-24T00:00:00Z",
    )
    assert len(rows) >= 20
    assert all(r.vsic_4digit == "2220" for r in rows)
    assert all(r.vsic_division == "22" for r in rows)
    assert all(r.tax_code for r in rows)


def test_max_page_from_fixture_is_bounded() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    max_page = max_page_from_listing(html)
    assert max_page >= 1
    assert max_page < 1000
