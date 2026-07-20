from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class VsicCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vsic_code: str
    isic_code: str
    level: int
    name_vi: str
    name_en: str | None = None
    parent_code: str | None = None


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_code: str
    name: str
    vsic_code: str
    exchange: str
    website_url: str | None = None
    has_ecommerce_site: bool
    digital_channels: dict | None = None
    description: str | None = None


class CompanyCrawlEventOut(BaseModel):
    """Derived crawl evidence from digital_presence / marketplace rows (not invent)."""

    event_type: str  # digital_presence | marketplace_listing
    source: str
    label: str
    url: str | None = None
    status: str = "recorded"
    crawled_at: datetime | None = None
    detail: str | None = None


class CompanyDataQualityOut(BaseModel):
    """Completeness / verification score — not market-data accuracy."""

    score: float
    max_score: float = 100.0
    components: dict[str, float] = {}
    notes: list[str] = []
    status: str = "ok"  # ok | partial | sparse


class CompanyCaseStudyOut(BaseModel):
    """Optional narrative block (e.g. Rạng Đông) built only from persisted fields."""

    stock_code: str
    title: str
    vsic_code: str
    vsic_name: str | None = None
    website_url: str | None = None
    shopee_url: str | None = None
    tiktok_url: str | None = None
    highlights: list[str] = []
    notes: list[str] = []


class CompanyDetail(CompanyOut):
    digital_presence: list["DigitalPresenceOut"] = []
    digital_metrics: list["DigitalMetricOut"] = []
    financial_reports: list["FinancialReportOut"] = []
    marketplace_listings: list["MarketplaceListingOut"] = []
    vsic: VsicCodeOut | None = None
    crawl_timeline: list[CompanyCrawlEventOut] = []
    data_quality: CompanyDataQualityOut | None = None
    case_study: CompanyCaseStudyOut | None = None


class DigitalPresenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_type: str
    url: str
    is_active: bool
    has_checkout: bool
    match_confidence: float | None = None
    crawled_at: datetime


class MarketplaceListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    product_name: str
    price: float | None = None
    units_sold_est: int | None = None
    revenue_est: float | None = None
    rating: float | None = None
    product_url: str | None = None
    crawled_at: datetime | None = None


class DigitalMetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    period: date
    online_revenue_est: float | None = None
    digital_va_contribution: float | None = None
    industry_share_pct: float | None = None
    digital_adoption_score: float | None = None
    channel_diversity: float | None = None
    online_revenue_ratio: float | None = None


class FinancialReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    period: date
    report_type: str
    revenue: float | None = None
    profit_before_tax: float | None = None
    net_profit: float | None = None
    total_assets: float | None = None
    total_equity: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    operating_expenses: float | None = None
    cost_of_goods: float | None = None
    rental_cost: float | None = None
    remuneration: float | None = None
    employees: int | None = None
    gross_margin: float | None = None


class GsoMacroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vsic_code: str
    indicator_code: str
    indicator_name: str
    period: date
    value: float
    unit: str


class OecdIndicatorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    indicator_code: str
    indicator_name: str
    country: str
    period: date
    value: float
    unit: str
    frequency: str


class ModelPredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_name: str
    target_indicator: str
    period: date
    predicted_value: float
    actual_value: float | None = None
    mae: float | None = None
    rmse: float | None = None
    mape: float | None = None


class PipelineJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_name: str
    status: str
    records_processed: int
    error_message: str | None = None
    detail: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime


class PipelineLastRunOut(BaseModel):
    family: str
    job_name: str | None = None
    status: str | None = None
    records_processed: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    detail: str | None = None


class PipelineMonitorStatusOut(BaseModel):
    last_runs: list[PipelineLastRunOut]
    jobs_listed: int = 0
    jobs_failed_in_list: int = 0
    staging_postgres: bool = False
    note: str | None = None


class CleaningQualitySummaryOut(BaseModel):
    nan_filled: int = 0
    outliers_handled: int = 0
    marketplace_outliers_flagged: int = 0
    vsic_fails: int = 0
    series_missing: list[str] = []
    artifacts: list[str] = []
    vsic_companies_fail: int = 0
    vsic_gso_fail: int = 0


class CleaningQualityReportOut(BaseModel):
    available: bool
    report_path: str
    message: str | None = None
    summary: CleaningQualitySummaryOut | None = None
    report: dict[str, Any] | None = None


class BenchmarkInput(BaseModel):
    stock_code: str | None = None
    vsic_code: str = "C"
    operating_revenue: float
    profit_before_tax: float
    employees: int
    operating_expenses: float | None = None
    cost_of_goods: float | None = None
    rental_cost: float | None = None
    remuneration: float | None = None
    total_assets: float | None = None
    total_equity: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None


class BenchmarkResult(BaseModel):
    roa: float | None = None
    roe: float | None = None
    current_ratio: float | None = None
    equity_ratio: float | None = None
    revenue_per_worker: float | None = None
    profit_per_worker: float | None = None
    percentiles: dict[str, float] = {}
    industry_averages: dict[str, float] = {}
    comparison: dict[str, str] = {}


class DashboardSummary(BaseModel):
    iip_latest: float | None = None
    iip_growth_pct: float | None = None
    total_companies: int = 0
    companies_with_ecommerce: int = 0
    avg_digital_adoption: float | None = None
    total_digital_va: float | None = None
    latest_period: date | None = None
    model_metrics: dict[str, Any] = {}
    preferred_forecast_model: str | None = None


class ForecastRequest(BaseModel):
    model_name: str = "xgboost"
    horizon_months: int = 6


class CrawlTriggerRequest(BaseModel):
    crawler: str  # gso, oecd, companies, marketplace, metrics, features, ml, cleaning, all
