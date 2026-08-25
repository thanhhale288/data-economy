import json
from pathlib import Path

import pytest

from crawlers.jp_calibration.frame import split_identity_and_label
from crawlers.jp_calibration.gbizinfo import _form_fields, parse_profile, parse_search_results
from crawlers.jp_calibration.identity import load_jp_identity
from crawlers.jp_calibration.nta import parse_nta_csv, parse_zenken_index
from crawlers.url_finder.config_loader import load_config
from crawlers.url_finder.identity import assert_no_url_fields


def test_ja_config_loads():
    cfg = load_config("ja")
    assert cfg["language"] == "ja"
    assert ".co.jp" in cfg["hypothesis_suffixes"]
    assert any(r["suffix"] == ".co.jp" for r in cfg["evidence"]["tld_bonuses"])


def test_split_drops_url_from_identity():
    identity, label = split_identity_and_label(
        corporate_number="6180301013611",
        nta={
            "legal_name": "株式会社アイシン",
            "address": "愛知県刈谷市朝日町２丁目１番地",
            "prefecture": "愛知県",
            "en_name": "AISIN CORPORATION",
            "furigana": "アイシン",
        },
        profile={
            "company_url": "https://www.aisin.com/jp/",
            "jsic_raw": "E.製造業",
            "jsic_division": "E",
            "employee_stratum": "301+",
            "employee_number": 34384,
        },
    )
    assert_no_url_fields(identity, context="test")
    assert "AISIN" in identity["aliases"][0]
    assert any("aishin" in a.lower() or "aisin" in a.lower() for a in identity["aliases"])
    assert label["gold_url"] == "https://www.aisin.com/jp/"
    assert identity["tax_id"] == "6180301013611"


def test_jp_identity_rejects_url(tmp_path: Path):
    path = tmp_path / "id.json"
    path.write_text(
        json.dumps(
            [
                {
                    "ticker": "6180301013611",
                    "legal_name": "株式会社アイシン",
                    "tax_id": "6180301013611",
                    "company_url": "https://www.aisin.com/jp/",
                }
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must not contain URL"):
        load_jp_identity(path)


def test_jp_identity_requires_13_digits(tmp_path: Path):
    path = tmp_path / "id.json"
    path.write_text(
        json.dumps(
            [{"ticker": "0101526991", "legal_name": "VN", "tax_id": "0101526991"}]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="13 digits"):
        load_jp_identity(path)


def test_parse_profile_aisin():
    html = """
    <html><head><title>株式会社アイシン | 6180301013611 | Gビズインフォ</title></head>
    <body>
    商号または名称 株式会社アイシン
    所在地 愛知県刈谷市朝日町２丁目１番地 （法人番号公表サイト）
    業種 E.製造業 （職場情報総合サイト）
    従業員数 34,384人 （職場情報総合サイト）
    企業ホームページ https://www.aisin.com/jp/ （職場情報総合サイト）
    <a href="https://www.aisin.com/jp/">https://www.aisin.com/jp/</a>
    </body></html>
    """
    parsed = parse_profile(html, corporate_number="6180301013611")
    assert parsed["company_url"].startswith("https://www.aisin.com")
    assert parsed["jsic_division"] == "E"
    assert parsed["is_manufacturing"] is True
    assert parsed["employee_number"] == 34384
    assert parsed["employee_stratum"] == "301+"
    assert "刈谷" in parsed["address"]


def test_parse_search_submit_profile():
    html = """
    <a href="javascript:submitProfile('6180301013611');">株式会社アイシン</a>
    <a href="javascript:submitProfile('1180001092357');">愛三工業株式会社</a>
    """
    rows = parse_search_results(html, prefecture="愛知県", stratum="301+")
    assert [r["corporate_number"] for r in rows] == [
        "6180301013611",
        "1180001092357",
    ]


def test_form_fields_maps_return_screen():
    html = """
    <form id="return_screen">
      <input name="shozaichiTodofuken" value="23">
      <input name="jugyoinsuFrom" value="301">
      <input name="gyoshu" value="E">
      <input name="hojinShubetsu" value="301">
      <input name="pageKensuHidden" value="50">
    </form>
    """
    fields = _form_fields(html)
    assert fields["ShozaichiTodofuken"] == "23"
    assert fields["JugyoinsuFrom"] == "301"
    assert fields["searchTypeHidden"] == "changePage"


def test_parse_zenken_do_download():
    html = """
    <h2>CSV形式・Unicode</h2>
    <dt>愛知県</dt>
    <dd><a href="#" onclick="return doDownload(27744);">zip 14MB</a></dd>
    <h2>XML形式・Unicode</h2>
    <dt>愛知県</dt>
    <dd><a href="#" onclick="return doDownload(27745);">分割1</a></dd>
    """
    rows = parse_zenken_index(html)
    assert len(rows) == 1
    assert rows[0]["prefecture"] == "愛知県"
    assert rows[0]["file_no"] == "27744"


def test_parse_nta_csv_latest_open_kk(tmp_path: Path):
    cells = [""] * 30
    cells[1] = "6180301013611"
    cells[6] = "株式会社アイシン"
    cells[8] = "301"
    cells[9] = "愛知県"
    cells[10] = "刈谷市"
    cells[11] = "朝日町２丁目１番地"
    cells[13] = "23"
    cells[18] = ""
    cells[23] = "1"
    cells[24] = "AISIN CORPORATION"
    cells[28] = "アイシン"
    cells[29] = "0"
    path = tmp_path / "23_aichi.csv"
    path.write_text(",".join(cells) + "\n", encoding="utf-8")
    rows = parse_nta_csv(path)
    assert len(rows) == 1
    assert rows[0]["en_name"] == "AISIN CORPORATION"
    assert rows[0]["address"].startswith("愛知県刈谷市")
