from pathlib import Path

from crawlers.url_finder.evidence import score_html
from crawlers.url_finder.search import parse_ddg_html, unwrap_ddg_href

FIXTURES = Path(__file__).parent / "fixtures"

RAL = {
    "ticker": "RAL",
    "legal_name": "Công ty Cổ phần Bóng đèn Rạng Đông",
    "tax_id": "0101526991",
    "address": "87-89 phố Hạ Đình, Quận Thanh Xuân, Thành phố Hà Nội",
    "aliases": ["RALACO"],
}


def test_tax_id_in_footer_scores_high():
    html = (FIXTURES / "site_with_mst.html").read_text(encoding="utf-8")
    score, reasons = score_html(RAL, html, url="https://rangdong.com.vn")
    assert score >= 4.0
    assert "tax_id_on_page" in reasons
    assert any(r.startswith("domain_tokens:") for r in reasons)


def test_unrelated_page_stays_below_threshold():
    html = (FIXTURES / "site_unrelated.html").read_text(encoding="utf-8")
    score, reasons = score_html(RAL, html, url="https://unrelated-example.com")
    assert score < 4.0
    assert "tax_id_on_page" not in reasons


def test_parse_ddg_unwraps_uddg_and_skips_nothing_here():
    html = (FIXTURES / "ddg_results.html").read_text(encoding="utf-8")
    hits = parse_ddg_html(html)
    urls = [h.url for h in hits]
    assert "https://rangdong.com.vn/" in urls
    assert "https://masothue.com/0101526991-cong-ty" in urls
    assert "https://cafef.vn/ral" in urls


def test_unwrap_ddg_href():
    raw = "//duckduckgo.com/l/?uddg=https%3A%2F%2Frangdong.com.vn%2F"
    assert unwrap_ddg_href(raw) == "https://rangdong.com.vn/"
