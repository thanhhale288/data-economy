from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class VsicCode(Base):
    __tablename__ = "vsic_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vsic_code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    isic_code: Mapped[str] = mapped_column(String(10), index=True)
    level: Mapped[int] = mapped_column(Integer)
    name_vi: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    companies: Mapped[list["Company"]] = relationship(back_populates="vsic")
    gso_macro: Mapped[list["GsoMacro"]] = relationship(back_populates="vsic")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    vsic_code: Mapped[str] = mapped_column(String(10), ForeignKey("vsic_codes.vsic_code"))
    exchange: Mapped[str] = mapped_column(String(10), default="HOSE")
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    has_ecommerce_site: Mapped[bool] = mapped_column(Boolean, default=False)
    digital_channels: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    vsic: Mapped["VsicCode"] = relationship(back_populates="companies")
    financial_reports: Mapped[list["FinancialReport"]] = relationship(back_populates="company")
    digital_presence: Mapped[list["DigitalPresence"]] = relationship(back_populates="company")
    marketplace_listings: Mapped[list["MarketplaceListing"]] = relationship(
        back_populates="company"
    )
    digital_metrics: Mapped[list["DigitalMetric"]] = relationship(back_populates="company")


class FinancialReport(Base):
    __tablename__ = "financial_reports"
    __table_args__ = (UniqueConstraint("company_id", "period", "report_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    period: Mapped[Date] = mapped_column(Date)
    report_type: Mapped[str] = mapped_column(String(20), default="annual")
    revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit_before_tax: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_assets: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_assets: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_liabilities: Mapped[float | None] = mapped_column(Float, nullable=True)
    operating_expenses: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_of_goods: Mapped[float | None] = mapped_column(Float, nullable=True)
    rental_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    remuneration: Mapped[float | None] = mapped_column(Float, nullable=True)
    employees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gross_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="financial_reports")


class DigitalPresence(Base):
    __tablename__ = "digital_presence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    channel_type: Mapped[str] = mapped_column(String(50))
    url: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    has_checkout: Mapped[bool] = mapped_column(Boolean, default=False)
    match_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company: Mapped["Company"] = relationship(back_populates="digital_presence")


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    platform: Mapped[str] = mapped_column(String(50))
    product_name: Mapped[str] = mapped_column(String(500))
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    units_sold_est: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revenue_est: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company: Mapped["Company"] = relationship(back_populates="marketplace_listings")


class DigitalMetric(Base):
    __tablename__ = "digital_metrics"
    __table_args__ = (UniqueConstraint("company_id", "period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    period: Mapped[Date] = mapped_column(Date)
    online_revenue_est: Mapped[float | None] = mapped_column(Float, nullable=True)
    digital_va_contribution: Mapped[float | None] = mapped_column(Float, nullable=True)
    industry_share_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    digital_adoption_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    channel_diversity: Mapped[float | None] = mapped_column(Float, nullable=True)
    online_revenue_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="digital_metrics")


class GsoMacro(Base):
    __tablename__ = "gso_macro"
    __table_args__ = (UniqueConstraint("vsic_code", "indicator_code", "period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vsic_code: Mapped[str] = mapped_column(String(10), ForeignKey("vsic_codes.vsic_code"))
    indicator_code: Mapped[str] = mapped_column(String(50))
    indicator_name: Mapped[str] = mapped_column(String(255))
    period: Mapped[Date] = mapped_column(Date)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50), default="index")
    source: Mapped[str] = mapped_column(String(50), default="GSO")

    vsic: Mapped["VsicCode"] = relationship(back_populates="gso_macro")


class OecdIndicator(Base):
    __tablename__ = "oecd_indicators"
    __table_args__ = (UniqueConstraint("indicator_code", "country", "period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicator_code: Mapped[str] = mapped_column(String(50))
    indicator_name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(10), default="VNM")
    isic_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    period: Mapped[Date] = mapped_column(Date)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50), default="index")
    frequency: Mapped[str] = mapped_column(String(20), default="monthly")
    # OECD | OECD_FALLBACK | OECD_PEER — never invent VNM values for missing series.
    source: Mapped[str] = mapped_column(String(50), default="OECD")


class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(50))
    target_indicator: Mapped[str] = mapped_column(String(50))
    period: Mapped[Date] = mapped_column(Date)
    predicted_value: Mapped[float] = mapped_column(Float)
    actual_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(50))
    model_type: Mapped[str] = mapped_column(String(50))
    version: Mapped[str] = mapped_column(String(20))
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    artifact_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
