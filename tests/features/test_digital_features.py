"""Unit tests for digital feature aggregation / calendar alignment."""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.features.digital_features import (
    DIGITAL_FEATURE_COLUMNS,
    aggregate_digital_features,
    digital_features_for_calendar,
)


def test_aggregate_digital_mean_across_firms(digital_rows):
    out = aggregate_digital_features(digital_rows)
    assert len(out) == 1
    assert out.loc[0, "digital_adoption_score"] == pytest.approx(0.5)
    assert out.loc[0, "channel_diversity"] == pytest.approx(0.6)
    assert out.loc[0, "online_revenue_ratio"] == pytest.approx(0.15)
    assert out.loc[0, "digital_alignment"] == "period_aggregate"


def test_aggregate_digital_null_when_all_missing():
    df = pd.DataFrame(
        [
            {
                "company_id": 1,
                "period": "2024-01-01",
                "digital_adoption_score": None,
                "channel_diversity": None,
                "online_revenue_ratio": None,
            }
        ]
    )
    out = aggregate_digital_features(df)
    assert len(out) == 1
    for col in DIGITAL_FEATURE_COLUMNS:
        assert pd.isna(out.loc[0, col])


def test_digital_broadcast_latest_onto_calendar(seeded_digital, macro_months):
    out = digital_features_for_calendar(seeded_digital, macro_months)
    assert len(out) == len(macro_months)
    assert set(out["digital_alignment"].unique()) == {"broadcast_latest"}
    assert out["online_revenue_ratio"].tolist() == pytest.approx([0.15] * len(out))


def test_digital_empty_db_returns_empty_schema(db_session, macro_months):
    out = digital_features_for_calendar(db_session, macro_months)
    assert out.empty
    assert list(out.columns) == [
        "period",
        *DIGITAL_FEATURE_COLUMNS,
        "digital_alignment",
    ]
