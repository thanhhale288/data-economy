"""Integration tests for build_features / run_feature_engineering."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from crawlers.oecd.sdmx_client import PEER_MEI_IP_COUNTRY
from pipeline.features.engineering import build_features, run_feature_engineering
from pipeline.features.validation import validate_feature_frame


def test_build_features_macro_plus_digital_financial_and_cross(
    monkeypatch, tmp_path, seeded_macro_db, seeded_digital, seeded_financial
):
    # Isolate from repo cleaned_macro.parquet / write targets.
    import pipeline.features.engineering as eng

    monkeypatch.setattr(eng, "_CLEANED_MACRO_PATH", tmp_path / "missing_cleaned.parquet")
    out = build_features(seeded_macro_db)
    assert "iip" in out.columns
    assert "iip_lag1" in out.columns
    assert "indigo_lag1" in out.columns
    assert "digital_adoption_score" in out.columns
    assert "online_revenue_ratio" in out.columns
    assert "roa" in out.columns
    assert "roe" in out.columns
    assert "current_ratio" in out.columns
    assert "online_revenue_ratio_x_iip_growth" in out.columns
    assert "mei_bci" not in out.columns
    assert out["digital_alignment"].eq("broadcast_latest").all()
    assert out["financial_alignment"].eq("broadcast_latest").all()
    # Cross = ratio * growth on overlapping rows
    expected = out["online_revenue_ratio"] * out["iip_growth"]
    assert (out["online_revenue_ratio_x_iip_growth"] - expected).abs().fillna(0).max() < 1e-12
    validate_feature_frame(
        out, require_digital=True, require_financial=True, check_lags=False
    )


def test_run_feature_engineering_writes_parquet_and_manifest(
    monkeypatch, tmp_path, seeded_macro_db, seeded_financial
):
    import pipeline.features.engineering as eng

    processed = tmp_path / "processed"
    monkeypatch.setattr(eng, "_CLEANED_MACRO_PATH", tmp_path / "nope.parquet")
    monkeypatch.setattr(eng, "_PROCESSED_DIR", processed)
    monkeypatch.setattr(eng, "_FEATURES_PATH", processed / "features.parquet")
    monkeypatch.setattr(eng, "_MANIFEST_PATH", processed / "features_manifest.json")

    n = run_feature_engineering(seeded_macro_db)
    assert n > 0
    path = processed / "features.parquet"
    assert path.exists()
    df = pd.read_parquet(path)
    assert "iip" in df.columns
    assert "roa" in df.columns
    assert "mei_bci" not in df.columns
    manifest = (processed / "features_manifest.json").read_text(encoding="utf-8")
    assert PEER_MEI_IP_COUNTRY in manifest
    assert "financial_present" in manifest


def test_prefers_cleaned_macro_artifact(
    monkeypatch, tmp_path, seeded_macro_db, seeded_financial
):
    import pipeline.features.engineering as eng

    cleaned = pd.DataFrame(
        {
            "period": pd.date_range("2024-01-01", periods=5, freq="MS"),
            "iip": [101.0, 102.0, 103.0, 104.0, 105.0],
            "indigo": [80.0, 81.0, 82.0, 83.0, 84.0],
            "mei_bci": [999.0] * 5,  # stale forbidden column must be stripped
        }
    )
    cleaned_path = tmp_path / "cleaned_macro.parquet"
    cleaned.to_parquet(cleaned_path, index=False)
    monkeypatch.setattr(eng, "_CLEANED_MACRO_PATH", cleaned_path)

    out = build_features(seeded_macro_db)
    assert "mei_bci" not in out.columns
    # Warm-up dropna removes first 3 lag rows; remaining IIP values are from artifact.
    assert set(out["iip"].tolist()) == {104.0, 105.0}
    assert out["iip"].iloc[0] == 104.0
