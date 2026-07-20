"""Digital feature loading and calendar alignment.

Firm values are aggregated with a null-skipping mean for each metric; an
all-null metric therefore remains null.  With multiple metric periods, values
are aligned to month starts by period and step-held between observations.  A
single snapshot is explicitly broadcast to every requested calendar month and
marked ``broadcast_latest``; it is not represented as monthly observations.
"""

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models import DigitalMetric


DIGITAL_FEATURE_COLUMNS = (
    "digital_adoption_score",
    "channel_diversity",
    "online_revenue_ratio",
)
_OUTPUT_COLUMNS = ("period", *DIGITAL_FEATURE_COLUMNS, "digital_alignment")


def load_digital_metrics_frame(db: Session) -> pd.DataFrame:
    """Return raw ``digital_metrics`` rows for all companies without imputation."""
    rows = (
        db.query(DigitalMetric)
        .order_by(DigitalMetric.period, DigitalMetric.company_id)
        .all()
    )
    return pd.DataFrame(
        [
            {
                "id": row.id,
                "company_id": row.company_id,
                "period": row.period,
                "online_revenue_est": row.online_revenue_est,
                "digital_va_contribution": row.digital_va_contribution,
                "industry_share_pct": row.industry_share_pct,
                "digital_adoption_score": row.digital_adoption_score,
                "channel_diversity": row.channel_diversity,
                "online_revenue_ratio": row.online_revenue_ratio,
            }
            for row in rows
        ]
    )


def aggregate_digital_features(df: pd.DataFrame) -> pd.DataFrame:
    """Mean the three digital features across firms per period, skipping nulls."""
    if df.empty:
        return pd.DataFrame(columns=_OUTPUT_COLUMNS)

    frame = df.copy()
    frame["period"] = pd.to_datetime(frame["period"], errors="coerce")
    frame = frame.dropna(subset=["period"])
    for column in DIGITAL_FEATURE_COLUMNS:
        if column not in frame:
            frame[column] = pd.NA
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if frame.empty:
        return pd.DataFrame(columns=_OUTPUT_COLUMNS)

    aggregated = (
        frame.groupby("period", as_index=False)[list(DIGITAL_FEATURE_COLUMNS)]
        .mean()
        .sort_values("period")
        .reset_index(drop=True)
    )
    aggregated["digital_alignment"] = "period_aggregate"
    return aggregated.loc[:, _OUTPUT_COLUMNS]


def _monthly_calendar(
    calendar: pd.Series | pd.DatetimeIndex | list,
) -> pd.DataFrame:
    """Normalize requested dates to unique month starts."""
    periods = pd.to_datetime(calendar, errors="coerce")
    periods = pd.DatetimeIndex(periods).dropna().to_period("M").to_timestamp()
    return pd.DataFrame({"period": periods.unique().sort_values()})


def _has_monthly_periods(periods: pd.Series) -> bool:
    """Whether consecutive source periods are one calendar month apart."""
    month_numbers = periods.dt.year * 12 + periods.dt.month
    return len(periods) > 1 and month_numbers.diff().dropna().eq(1).all()


def digital_features_for_calendar(
    db: Session,
    calendar: pd.Series | pd.DatetimeIndex | list,
) -> pd.DataFrame:
    """Return digital features aligned to requested month starts.

    Multiple source periods are aggregated across firms then step-held at month
    starts from each observed period.  A single source period is broadcast to
    every calendar month and marked ``broadcast_latest`` rather than treated as
    a set of monthly measurements.  An empty database returns an empty frame;
    callers can left-join it onto their calendar.
    """
    aggregated = aggregate_digital_features(load_digital_metrics_frame(db))
    if aggregated.empty:
        return pd.DataFrame(columns=_OUTPUT_COLUMNS)

    monthly_calendar = _monthly_calendar(calendar)
    if monthly_calendar.empty:
        return pd.DataFrame(columns=_OUTPUT_COLUMNS)

    if len(aggregated) == 1:
        result = monthly_calendar.copy()
        for column in DIGITAL_FEATURE_COLUMNS:
            result[column] = aggregated.iloc[0][column]
        result["digital_alignment"] = "broadcast_latest"
        return result.loc[:, _OUTPUT_COLUMNS]

    source = aggregated.copy()
    if _has_monthly_periods(source["period"]):
        source["period"] = source["period"].dt.to_period("M").dt.to_timestamp()
    result = pd.merge_asof(
        monthly_calendar.sort_values("period"),
        source,
        on="period",
        direction="backward",
    )
    result["digital_alignment"] = "period_aggregate"
    return result.loc[:, _OUTPUT_COLUMNS]
