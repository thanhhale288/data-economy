"""Mini-gold scoring tests."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from crawlers.mini_gold.evaluate import evaluate_worksheet, score_field, summarize_metrics
from crawlers.mini_gold.paths import ALL_FIELDS
from crawlers.mini_gold.worksheet import (
    firm_to_worksheet_row,
    load_fetch_ok_firms,
    write_worksheet,
)


def test_score_bool_hit_wrong_abstain():
    assert score_field(field="has_order_cart", gold_raw="true", pred_raw="true") == "hit"
    assert score_field(field="has_order_cart", gold_raw="true", pred_raw="false") == "wrong"
    assert (
        score_field(field="has_order_cart", gold_raw="true", pred_raw="abstain")
        == "abstain_pred"
    )
    assert (
        score_field(field="has_order_cart", gold_raw="abstain", pred_raw="true")
        == "abstain_gold"
    )


def test_score_tier2_null_counts_as_abstain_pred():
    assert (
        score_field(field="has_product_catalog", gold_raw="true", pred_raw="null")
        == "abstain_pred"
    )


def test_score_payment_presence():
    assert (
        score_field(field="payment_methods", gold_raw="vnpay,cod", pred_raw="cod,vnpay")
        == "hit"
    )
    assert score_field(field="payment_methods", gold_raw="abstain", pred_raw="") == (
        "abstain_gold"
    )
    assert (
        score_field(field="payment_methods", gold_raw="", pred_raw="abstain")
        == "abstain_pred"
    )
    assert (
        score_field(field="payment_methods", gold_raw="cod", pred_raw="") == "wrong"
    )
    assert score_field(field="payment_methods", gold_raw="", pred_raw="") == "hit"


def test_score_social_presence():
    assert score_field(field="social_links", gold_raw="true", pred_raw="true") == "hit"
    assert score_field(field="social_links", gold_raw="false", pred_raw="true") == "wrong"


def test_score_language():
    assert score_field(field="website_language", gold_raw="vi", pred_raw="vi") == "hit"
    assert score_field(field="website_language", gold_raw="vi", pred_raw="en") == "wrong"
    assert (
        score_field(field="website_language", gold_raw="vi", pred_raw="unknown") == "hit"
    )
    assert (
        score_field(field="website_language", gold_raw="abstain", pred_raw="vi")
        == "abstain_gold"
    )


def test_evaluate_reviewed_only(tmp_path: Path):
    path = tmp_path / "w.csv"
    rows = [
        {
            "firm_id": "A",
            "source_cohort": "listed28",
            "website_url": "https://a.example",
            "pre_t1_has_product_catalog": "true",
            "pre_t1_has_order_cart": "false",
            "pre_t1_payment_methods": "",
            "pre_t1_social_links": "true",
            "pre_t1_marketplace_links": "false",
            "pre_t1_website_language": "vi",
            "pre_t2_has_product_catalog": "true",
            "pre_t2_has_order_cart": "abstain",
            "pre_t2_payment_methods": "abstain",
            "pre_t2_social_links": "false",
            "pre_t2_marketplace_links": "false",
            "pre_t2_website_language": "vi",
            "gold_has_product_catalog": "true",
            "gold_has_order_cart": "false",
            "gold_payment_methods": "",
            "gold_social_links": "true",
            "gold_marketplace_links": "false",
            "gold_website_language": "vi",
            "reviewed": "true",
            "notes": "",
        },
        {
            "firm_id": "B",
            "source_cohort": "frame_pilot",
            "website_url": "https://b.example",
            "pre_t1_has_product_catalog": "true",
            "pre_t1_has_order_cart": "true",
            "pre_t1_payment_methods": "cod",
            "pre_t1_social_links": "false",
            "pre_t1_marketplace_links": "false",
            "pre_t1_website_language": "vi",
            "pre_t2_has_product_catalog": "true",
            "pre_t2_has_order_cart": "true",
            "pre_t2_payment_methods": "cod",
            "pre_t2_social_links": "false",
            "pre_t2_marketplace_links": "false",
            "pre_t2_website_language": "vi",
            "gold_has_product_catalog": "true",
            "gold_has_order_cart": "true",
            "gold_payment_methods": "cod",
            "gold_social_links": "false",
            "gold_marketplace_links": "false",
            "gold_website_language": "vi",
            "reviewed": "false",
            "notes": "",
        },
    ]
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    scored, metrics = evaluate_worksheet(path=path, require_reviewed=True)
    assert metrics["n_firms_reviewed"] == 1
    assert all(r["firm_id"] == "A" for r in scored)
    t1 = metrics["tiers"]["tier1"]["aggregate"]
    assert t1["hit"] >= 1
    t2_cart = metrics["tiers"]["tier2"]["by_field"]["has_order_cart"]
    assert t2_cart["abstain_pred"] == 1


def _cascade_rec(*, firm_id: str = "RAL", fetch_ok: bool = True) -> dict:
    return {
        "firm_id": firm_id,
        "source_cohort": "listed28",
        "website_url": "https://rangdong.com.vn",
        "fetch_ok": fetch_ok,
        "tier2_decision": "ok",
        "model_id": "qwen3:8b",
        "tier1": {
            "has_product_catalog": True,
            "has_order_cart": True,
            "payment_methods": [],
            "social_links": [{"platform": "facebook", "url": "https://facebook.com/x"}],
            "marketplace_links": [],
            "website_language": "vi",
        },
        "tier2": {
            "has_product_catalog": {
                "value": True,
                "confidence": 0.9,
                "abstain": False,
                "reason": "ok",
            },
            "has_order_cart": {
                "value": None,
                "confidence": 0.1,
                "abstain": True,
                "reason": "thin",
            },
            "payment_methods": {
                "value": [],
                "confidence": 0.1,
                "abstain": True,
                "reason": "thin",
            },
            "social_links": {
                "value": [],
                "confidence": 0.1,
                "abstain": True,
                "reason": "thin",
            },
            "marketplace_links": {
                "value": [],
                "confidence": 0.1,
                "abstain": True,
                "reason": "thin",
            },
            "website_language": {
                "value": "vi",
                "confidence": 1.0,
                "abstain": False,
                "reason": "vi",
            },
        },
    }


def _unreviewed_row(firm_id: str = "X") -> dict[str, str]:
    row = {
        "firm_id": firm_id,
        "source_cohort": "listed28",
        "website_url": "https://x.example",
        "pre_t1_has_product_catalog": "true",
        "pre_t1_has_order_cart": "true",
        "pre_t1_payment_methods": "cod",
        "pre_t1_social_links": "true",
        "pre_t1_marketplace_links": "false",
        "pre_t1_website_language": "vi",
        "pre_t2_has_product_catalog": "true",
        "pre_t2_has_order_cart": "true",
        "pre_t2_payment_methods": "cod",
        "pre_t2_social_links": "true",
        "pre_t2_marketplace_links": "false",
        "pre_t2_website_language": "vi",
        "gold_has_product_catalog": "",
        "gold_has_order_cart": "",
        "gold_payment_methods": "",
        "gold_social_links": "",
        "gold_marketplace_links": "",
        "gold_website_language": "",
        "reviewed": "false",
        "notes": "",
    }
    return row


def test_build_worksheet_from_cascade_fixture(tmp_path: Path):
    jsonl = tmp_path / "indicators.jsonl"
    rec = _cascade_rec()
    skipped = _cascade_rec(firm_id="SKIP", fetch_ok=False)
    jsonl.write_text(
        json.dumps(skipped) + "\n" + json.dumps(rec) + "\n", encoding="utf-8"
    )
    loaded = load_fetch_ok_firms(jsonl)
    assert [r["firm_id"] for r in loaded] == ["RAL"]

    row = firm_to_worksheet_row(rec)
    assert row["pre_t1_has_order_cart"] == "true"
    assert row["pre_t2_has_order_cart"] == "abstain"
    for name in ALL_FIELDS:
        assert row[f"gold_{name}"] == ""
        pre = row[f"pre_t1_{name}"]
        if pre:
            assert row[f"gold_{name}"] != pre
    assert row["reviewed"] == "false"

    m = summarize_metrics([], n_firms=0)
    assert m["n_firms_reviewed"] == 0


def test_write_worksheet_leaves_gold_blank(tmp_path: Path):
    jsonl = tmp_path / "indicators.jsonl"
    jsonl.write_text(json.dumps(_cascade_rec()) + "\n", encoding="utf-8")
    out = tmp_path / "worksheet_89.csv"
    meta = write_worksheet(jsonl_path=jsonl, out_csv=out)
    assert meta["n_fetch_ok"] == 1
    with out.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    for name in ALL_FIELDS:
        assert rows[0][f"gold_{name}"] == ""
    assert rows[0]["reviewed"] == "false"
    assert (tmp_path / "sample_manifest.json").is_file()
    assert (tmp_path / "PROVENANCE.md").is_file()


def test_evaluate_unreviewed_empty_gold_is_zero_firms(tmp_path: Path):
    path = tmp_path / "w.csv"
    row = _unreviewed_row()
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        w.writeheader()
        w.writerow(row)
    scored, metrics = evaluate_worksheet(path=path, require_reviewed=True)
    assert scored == []
    assert metrics["n_firms_reviewed"] == 0


def test_eval_cli_exits_2_when_no_reviewed(tmp_path: Path, monkeypatch, capsys):
    from crawlers.mini_gold import __main__ as mini_main
    from crawlers.mini_gold import evaluate as ev

    path = tmp_path / "worksheet_89.csv"
    row = _unreviewed_row()
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        w.writeheader()
        w.writerow(row)
    monkeypatch.setattr(ev, "WORKSHEET_CSV", path)
    assert mini_main.main(["eval"]) == 2
    err = capsys.readouterr().err
    assert "No reviewed rows" in err
    assert not (tmp_path / "metrics.json").exists()
