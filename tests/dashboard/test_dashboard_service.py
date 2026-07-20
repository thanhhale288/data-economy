"""Task #13 — Dashboard ngành service tests."""

from __future__ import annotations

from datetime import date

from backend.app.models import ModelRegistry
from backend.app.services import dashboard_service as svc


def test_oecd_vs_gso_missing_peer_is_explicit(db_session, seeded_iip):
    result = svc.get_oecd_vs_gso(db_session)

    assert result["oecd_status"] == "missing"
    assert result["oecd"] == []
    assert result["oecd_country"] is None
    assert "không" in result["oecd_note"].lower() or "không" in result["oecd_note"]
    assert all(row["oecd"] is None for row in result["aligned"])
    assert any(row["gso"] is not None for row in result["aligned"])
    # Must not invent peer values when series is absent
    assert not any(row.get("oecd") for row in result["oecd"])


def test_oecd_vs_gso_aligns_by_period_not_index(db_session, seeded_iip, seeded_peer_mei):
    result = svc.get_oecd_vs_gso(db_session)

    assert result["oecd_status"] == "available"
    assert result["oecd_country"] == "EA20"
    assert result["oecd_source"] == "OECD_PEER"
    assert len(result["oecd"]) == 4

    by_period = {row["period"]: row for row in result["aligned"]}
    # Overlap month: both present
    jan = by_period["2024-01"]
    assert jan["gso"] == 101.0
    assert jan["oecd"] == 91.0
    # GSO-only later month: oecd null, not shifted from another month
    jun = by_period["2024-06"]
    assert jun["gso"] == 106.0
    assert jun["oecd"] is None


def test_heatmap_includes_labels_and_intensity(db_session, seeded_companies_va):
    rows = svc.get_industry_heatmap(db_session)

    assert len(rows) == 2
    assert rows[0]["vsic_code"] == "2740"
    assert rows[0]["vsic_name"] == "Sản xuất thiết bị chiếu sáng điện"
    assert rows[0]["digital_va"] == 5e8
    assert rows[0]["intensity"] == 1.0
    assert rows[1]["intensity"] == 0.2
    assert rows[0]["company_count"] == 1


def test_summary_preferred_model_by_lowest_mape(db_session, seeded_iip):
    db_session.add_all(
        [
            ModelRegistry(
                model_name="xgboost",
                model_type="ml",
                version="1",
                metrics={"mae": 2.0, "rmse": 3.0, "mape": 5.0},
                is_active=True,
            ),
            ModelRegistry(
                model_name="arima",
                model_type="stats",
                version="1",
                metrics={"mae": 1.0, "rmse": 1.5, "mape": 2.0},
                is_active=True,
            ),
        ]
    )
    db_session.commit()

    summary = svc.get_dashboard_summary(db_session)
    assert summary.preferred_forecast_model == "arima"
    assert summary.iip_latest == 106.0
    assert "arima" in summary.model_metrics
    assert "xgboost" in summary.model_metrics


def test_iip_timeseries_preserves_source(db_session, seeded_iip):
    series = svc.get_iip_timeseries(db_session, "C")
    assert len(series) == 6
    assert series[0]["period"] == date(2024, 1, 1).isoformat()
    assert series[0]["source"] == "GSO"
    assert series[-1]["value"] == 106.0
