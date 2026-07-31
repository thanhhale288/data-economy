"""Tests for ml.product_categorizer — happy path + OOV/unknown abstain."""

from __future__ import annotations

from pathlib import Path

import pytest

from ml.product_categorizer import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    ProductCategorizer,
    evaluate_precision,
    load_labels,
)
from ml.product_categorizer.vsic import section_c_vsic_4digit

REPO_ROOT = Path(__file__).resolve().parents[2]
LABELS_PATH = REPO_ROOT / "data" / "seeds" / "product_categorizer_labels.json"


@pytest.fixture
def trained(tmp_path: Path) -> ProductCategorizer:
    cat = ProductCategorizer(model_path=tmp_path / "product_categorizer.joblib")
    cat.train(labels_path=LABELS_PATH, persist=True)
    return cat


def test_labels_file_exists_and_has_splits():
    rows = load_labels(LABELS_PATH)
    assert len(rows) >= 20
    splits = {r.get("split") for r in rows}
    assert "train" in splits and "test" in splits
    assert any(r.get("vsic_code") is None for r in rows)
    whitelist = section_c_vsic_4digit()
    for r in rows:
        code = r.get("vsic_code")
        if code is not None:
            assert str(code) in whitelist
            assert len(str(code)) == 4


def test_whitelist_is_section_c_four_digit():
    codes = section_c_vsic_4digit()
    assert "2740" in codes
    assert "1050" in codes
    assert "C" not in codes
    assert "10" not in codes


def test_happy_path_seed_products(trained: ProductCategorizer):
    cases = [
        ("Bóng LED Rạng Đông 9W", "2740"),
        ("Sữa tươi Vinamilk 1L", "1050"),
        ("Laptop FPT", "2620"),
        ("Nhẫn vàng PNJ", "3211"),
        ("Nước mắm Chin-su", "1020"),
    ]
    for name, expected in cases:
        out = trained.predict(name)
        assert out.vsic_code == expected, (
            f"{name!r} → {out.vsic_code} conf={out.confidence} reason={out.reason}"
        )
        assert out.confidence >= DEFAULT_CONFIDENCE_THRESHOLD
        assert out.reason is None


def test_paraphrase_test_split_precision(trained: ProductCategorizer):
    report = evaluate_precision(trained, labels_path=LABELS_PATH, split="test")
    assert report["n"] >= 10
    assert report["fp"] == 0
    assert report["precision"] == 1.0
    # Must correctly abstain on at least one unknown OOV
    assert report["tn_abstain_correct"] >= 1


def test_oov_unknown_abstains(trained: ProductCategorizer):
    unknowns = [
        "Vé máy bay nội địa",
        "Thuê căn hộ chung cư 2PN",
        "Tour du lịch Đà Nẵng 3 ngày",
        "xyzqwerty 999 unrelated junk",
        "",
        "ab",
    ]
    for name in unknowns:
        out = trained.predict(name)
        assert out.vsic_code is None, f"invented code for {name!r}: {out}"
        assert out.reason is not None


def test_never_returns_code_outside_whitelist(trained: ProductCategorizer):
    whitelist = section_c_vsic_4digit()
    probes = [
        "Bóng LED Panel",
        "Sữa chua uống",
        "something random service package consulting",
        "Phân bón NPK",
    ]
    for name in probes:
        out = trained.predict(name)
        if out.vsic_code is not None:
            assert out.vsic_code in whitelist


def test_save_and_load_roundtrip(tmp_path: Path):
    path = tmp_path / "pc.joblib"
    cat = ProductCategorizer(model_path=path)
    cat.train(labels_path=LABELS_PATH, persist=True)
    assert path.exists()

    loaded = ProductCategorizer(model_path=path)
    assert loaded.load() is True
    out = loaded.predict("Đèn LED bulb 9W")
    assert out.vsic_code == "2740"


def test_train_rejects_non_whitelist_label(tmp_path: Path):
    cat = ProductCategorizer(model_path=tmp_path / "x.joblib")
    with pytest.raises(ValueError, match="whitelist"):
        cat.train(
            [
                {
                    "product_name": "fake",
                    "vsic_code": "9999",
                    "split": "train",
                }
            ],
            persist=False,
        )
