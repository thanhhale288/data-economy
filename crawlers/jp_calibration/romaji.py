"""Katakana/hiragana → Hepburn romaji for URL-finder aliases (identity only)."""

from __future__ import annotations

import re

# Longest-first. Covers the kana we see in 商号カナ / furigana, not literary Japanese.
_KANA = (
    ("キャ", "kya"),
    ("キュ", "kyu"),
    ("キョ", "kyo"),
    ("シャ", "sha"),
    ("シュ", "shu"),
    ("ショ", "sho"),
    ("チャ", "cha"),
    ("チュ", "chu"),
    ("チョ", "cho"),
    ("ニャ", "nya"),
    ("ニュ", "nyu"),
    ("ニョ", "nyo"),
    ("ヒャ", "hya"),
    ("ヒュ", "hyu"),
    ("ヒョ", "hyo"),
    ("ミャ", "mya"),
    ("ミュ", "myu"),
    ("ミョ", "myo"),
    ("リャ", "rya"),
    ("リュ", "ryu"),
    ("リョ", "ryo"),
    ("ギャ", "gya"),
    ("ギュ", "gyu"),
    ("ギョ", "gyo"),
    ("ジャ", "ja"),
    ("ジュ", "ju"),
    ("ジョ", "jo"),
    ("ビャ", "bya"),
    ("ビュ", "byu"),
    ("ビョ", "byo"),
    ("ピャ", "pya"),
    ("ピュ", "pyu"),
    ("ピョ", "pyo"),
    ("ティ", "ti"),
    ("ディ", "di"),
    ("トゥ", "tu"),
    ("ドゥ", "du"),
    ("ファ", "fa"),
    ("フィ", "fi"),
    ("フェ", "fe"),
    ("フォ", "fo"),
    ("ウィ", "wi"),
    ("ウェ", "we"),
    ("ウォ", "wo"),
    ("ヴァ", "va"),
    ("ヴィ", "vi"),
    ("ヴェ", "ve"),
    ("ヴォ", "vo"),
    ("ア", "a"),
    ("イ", "i"),
    ("ウ", "u"),
    ("エ", "e"),
    ("オ", "o"),
    ("カ", "ka"),
    ("キ", "ki"),
    ("ク", "ku"),
    ("ケ", "ke"),
    ("コ", "ko"),
    ("サ", "sa"),
    ("シ", "shi"),
    ("ス", "su"),
    ("セ", "se"),
    ("ソ", "so"),
    ("タ", "ta"),
    ("チ", "chi"),
    ("ツ", "tsu"),
    ("テ", "te"),
    ("ト", "to"),
    ("ナ", "na"),
    ("ニ", "ni"),
    ("ヌ", "nu"),
    ("ネ", "ne"),
    ("ノ", "no"),
    ("ハ", "ha"),
    ("ヒ", "hi"),
    ("フ", "fu"),
    ("ヘ", "he"),
    ("ホ", "ho"),
    ("マ", "ma"),
    ("ミ", "mi"),
    ("ム", "mu"),
    ("メ", "me"),
    ("モ", "mo"),
    ("ヤ", "ya"),
    ("ユ", "yu"),
    ("ヨ", "yo"),
    ("ラ", "ra"),
    ("リ", "ri"),
    ("ル", "ru"),
    ("レ", "re"),
    ("ロ", "ro"),
    ("ワ", "wa"),
    ("ヲ", "o"),
    ("ン", "n"),
    ("ガ", "ga"),
    ("ギ", "gi"),
    ("グ", "gu"),
    ("ゲ", "ge"),
    ("ゴ", "go"),
    ("ザ", "za"),
    ("ジ", "ji"),
    ("ズ", "zu"),
    ("ゼ", "ze"),
    ("ゾ", "zo"),
    ("ダ", "da"),
    ("ヂ", "ji"),
    ("ヅ", "zu"),
    ("デ", "de"),
    ("ド", "do"),
    ("バ", "ba"),
    ("ビ", "bi"),
    ("ブ", "bu"),
    ("ベ", "be"),
    ("ボ", "bo"),
    ("パ", "pa"),
    ("ピ", "pi"),
    ("プ", "pu"),
    ("ペ", "pe"),
    ("ポ", "po"),
)

_HIRAGANA_OFFSET = ord("ア") - ord("あ")


def _to_katakana(text: str) -> str:
    out: list[str] = []
    for ch in text or "":
        code = ord(ch)
        if ord("ぁ") <= code <= ord("ゖ"):
            out.append(chr(code + _HIRAGANA_OFFSET))
        else:
            out.append(ch)
    return "".join(out)


def kana_to_romaji(text: str) -> str:
    raw = _to_katakana(text or "")
    raw = raw.replace("ー", "")
    for src, dst in _KANA:
        raw = raw.replace(src, dst)
    # Sokuon: ッ + consonant → doubled consonant
    raw = re.sub(r"ッ([bcdfghjklmnpqrstvwxyz])", r"\1\1", raw, flags=re.I)
    raw = raw.replace("ッ", "")
    compact = re.sub(r"[^a-z0-9]+", "", raw.lower())
    return compact
