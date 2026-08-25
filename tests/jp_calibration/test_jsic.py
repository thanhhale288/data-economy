from crawlers.jp_calibration.jsic import is_manufacturing, jsic_division
from crawlers.jp_calibration.romaji import kana_to_romaji


def test_division_e_from_gbizinfo_label():
    assert jsic_division("E.製造業") == "E"
    assert is_manufacturing("E.製造業")
    assert is_manufacturing("製造業")
    assert not is_manufacturing("I.卸売業、小売業")
    assert not is_manufacturing("D.建設業")


def test_kana_to_romaji_toyota_stem():
    assert "toyota" in kana_to_romaji("トヨタ")
    # Hepburn シ→shi; brand spelling "AISIN" comes from NTA enName, not kana.
    assert kana_to_romaji("アイシン") == "aishin"
