"""Unit tests for financial ratio features."""

from __future__ import annotations

import pandas as pd

from pipeline.features.financial_features import (
    FINANCIAL_FEATURE_COLUMNS,
    aggregate_financial_features,
    compute_firm_ratios,
    financial_features_for_calendar,
)


def test_compute_firm_ratios_and_null_on_missing_or_zero_denom():
    df = pd.DataFrame(
        [
            {
                "company_id": 1,
                "period": "2024-03-31",
                "report_type": "quarterly",
                "net_profit": 100.0,
                "total_assets": 1000.0,
                "total_equity": 500.0,
                "current_assets": 200.0,
                "current_liabilities": 100.0,
            },
            {
                "company_id": 2,
                "period": "2024-03-31",
                "report_type": "quarterly",
                "net_profit": 10.0,
                "total_assets": 0.0,
                "total_equity": None,
                "current_assets": 5.0,
                "current_liabilities": None,
            },
        ]
    )
    out = compute_firm_ratios(df)
    assert out.loc[0, "roa"] == 0.1
    assert out.loc[0, "roe"] == 0.2
    assert out.loc[0, "current_ratio"] == 2.0
    assert pd.isna(out.loc[1, "roa"])
    assert pd.isna(out.loc[1, "roe"])
    assert pd.isna(out.loc[1, "current_ratio"])


def test_aggregate_financial_mean(seeded_financial):
    from pipeline.features.financial_features import load_financial_reports_frame

    raw = load_financial_reports_frame(seeded_financial)
    out = aggregate_financial_features(raw)
    assert len(out) == 1
    # mean of 0.1 and 0.1 = 0.1 ROA; ROE mean 0.2; CR mean (2.0 + 3.0) / 2 = 2.5
    assert abs(out.loc[0, "roa"] - 0.1) < 1e-12
    assert abs(out.loc[0, "roe"] - 0.2) < 1e-12
    assert abs(out.loc[0, "current_ratio"] - 2.5) < 1e-12
    assert out.loc[0, "financial_alignment"] == "step_hold_quarter"


def test_financial_broadcast_when_single_period(seeded_financial, macro_months):
    out = financial_features_for_calendar(seeded_financial, macro_months)
    assert len(out) == len(macro_months)
    assert set(out["financial_alignment"].unique()) == {"broadcast_latest"}
    for col in FINANCIAL_FEATURE_COLUMNS:
        assert out[col].notna().all()


def test_financial_empty_db(db_session, macro_months):
    out = financial_features_for_calendar(db_session, macro_months)
    assert out.empty
    assert list(out.columns) == [
        "period",
        *FINANCIAL_FEATURE_COLUMNS,
        "financial_alignment",
    ]
