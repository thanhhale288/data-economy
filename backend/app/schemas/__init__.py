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


class CompanyDetail(CompanyOut):
    digital_presence: list["DigitalPresenceOut"] = []
    digital_metrics: list["DigitalMetricOut"] = []
    financial_reports: list["FinancialReportOut"] = []
    marketplace_listings: list["MarketplaceListingOut"] = []
    vsic: VsicCodeOut | None = None


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
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime


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


class ForecastRequest(BaseModel):
    model_name: str = "xgboost"
    horizon_months: int = 6


class CrawlTriggerRequest(BaseModel):
    crawler: str  # gso, oecd, companies, marketplace, all
