from crawlers.url_finder.identity import parse_masothue_hq

HQ_HTML = """
<html><body>
<h1>0101526991 - CÔNG TY CỔ PHẦN BÓNG ĐÈN PHÍCH NƯỚC RẠNG ĐÔNG</h1>
<table class="table-taxinfo">
<tr><td>CÔNG TY CỔ PHẦN BÓNG ĐÈN PHÍCH NƯỚC RẠNG ĐÔNG</td></tr>
<tr><td>Mã số thuế</td><td>0101526991</td></tr>
<tr><td>Địa chỉ</td><td>87 Hạ Đình, Thành phố Hà Nội, Việt Nam</td></tr>
<tr><td>Tên viết tắt</td><td>RALACO</td></tr>
</table>
</body></html>
"""

BRANCH_HTML = """
<html><body>
<h1>0101526991-001 - CHI NHÁNH CÔNG TY CỔ PHẦN BÓNG ĐÈN PHÍCH NƯỚC RẠNG ĐÔNG</h1>
<table class="table-taxinfo">
<tr><td>Mã số thuế</td><td>0101526991-001</td></tr>
</table>
</body></html>
"""


def test_parse_hq_extracts_tax_and_address():
    row = parse_masothue_hq(
        HQ_HTML,
        "https://masothue.com/0101526991-cong-ty-co-phan-bong-den-phich-nuoc-rang-dong",
    )
    assert row is not None
    assert row["tax_id"] == "0101526991"
    assert "Hà Nội" in row["province"] or "Ha Noi" in row["province"]
    assert "RALACO" in row["aliases"]


def test_parse_skips_branch_path():
    row = parse_masothue_hq(
        HQ_HTML,
        "https://masothue.com/0101526991-001-chi-nhanh-rang-dong",
    )
    assert row is None


def test_parse_skips_branch_heading():
    row = parse_masothue_hq(
        BRANCH_HTML,
        "https://masothue.com/0101526991-cong-ty",
    )
    assert row is None
