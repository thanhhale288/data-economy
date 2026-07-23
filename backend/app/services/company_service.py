"""Company list/detail (Module 2) — profile, channels, online est., RAL case study."""

from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from backend.app.models import Company, DigitalPresence, MarketplaceListing
from backend.app.schemas import (
    CompanyCaseStudyOut,
    CompanyCrawlEventOut,
    CompanyDataQualityOut,
    CompanyDetail,
    CompanyOut,
    DigitalMetricOut,
    DigitalPresenceOut,
    FinancialReportOut,
    MarketplaceListingOut,
    VsicCodeOut,
)

_MARKETPLACE_PLATFORMS = frozenset({"shopee", "tiktok", "lazada"})
_RAL_CODE = "RAL"


def list_companies(
    db: Session,
    *,
    vsic: str | None = None,
) -> list[CompanyOut]:
    """List companies; optional ``vsic`` filters by code or 2-digit division prefix."""
    q = db.query(Company)
    if vsic:
        prefix = vsic.strip()
        if len(prefix) == 2:
            q = q.filter(Company.vsic_code.startswith(prefix))
        else:
            q = q.filter(Company.vsic_code == prefix)
    return q.order_by(Company.stock_code).all()


def peer_companies(db: Session, stock_code: str, *, limit: int = 12) -> list[Company]:
    """Same VSIC 2-digit division peers (excludes self)."""
    company = (
        db.query(Company)
        .filter(Company.stock_code == stock_code.upper())
        .first()
    )
    if not company or not company.vsic_code:
        return []
    division = company.vsic_code[:2]
    return (
        db.query(Company)
        .filter(
            Company.vsic_code.startswith(division),
            Company.stock_code != company.stock_code,
        )
        .order_by(Company.stock_code)
        .limit(limit)
        .all()
    )


def get_company(db: Session, stock_code: str) -> CompanyDetail | None:
    company = (
        db.query(Company)
        .options(
            joinedload(Company.digital_presence),
            joinedload(Company.digital_metrics),
            joinedload(Company.financial_reports),
            joinedload(Company.marketplace_listings),
            joinedload(Company.vsic),
        )
        .filter(Company.stock_code == stock_code.upper())
        .first()
    )
    if not company:
        return None
    peers = peer_companies(db, company.stock_code)
    return build_company_detail(company, peers=peers)


def build_company_detail(
    company: Company,
    *,
    peers: list[Company] | None = None,
) -> CompanyDetail:
    presence = list(company.digital_presence or [])
    listings = list(company.marketplace_listings or [])
    metrics = list(company.digital_metrics or [])
    reports = list(company.financial_reports or [])
    peer_rows = peers if peers is not None else []
    division = (
        company.vsic_code[:2]
        if company.vsic_code and len(company.vsic_code) >= 2
        else company.vsic_code
    )

    return CompanyDetail(
        id=company.id,
        stock_code=company.stock_code,
        name=company.name,
        vsic_code=company.vsic_code,
        exchange=company.exchange,
        website_url=company.website_url,
        has_ecommerce_site=company.has_ecommerce_site,
        digital_channels=company.digital_channels,
        description=company.description,
        digital_presence=[DigitalPresenceOut.model_validate(p) for p in presence],
        digital_metrics=[DigitalMetricOut.model_validate(m) for m in metrics],
        financial_reports=[FinancialReportOut.model_validate(r) for r in reports],
        marketplace_listings=[MarketplaceListingOut.model_validate(ml) for ml in listings],
        vsic=VsicCodeOut.model_validate(company.vsic) if company.vsic else None,
        crawl_timeline=build_crawl_timeline(presence, listings),
        data_quality=compute_data_quality(company, presence, listings, metrics),
        case_study=build_case_study(company, presence),
        peers=[CompanyOut.model_validate(p) for p in peer_rows],
        vsic_division=division,
    )


def build_crawl_timeline(
    presence: list[DigitalPresence],
    listings: list[MarketplaceListing],
) -> list[CompanyCrawlEventOut]:
    events: list[CompanyCrawlEventOut] = []

    for dp in presence:
        events.append(
            CompanyCrawlEventOut(
                event_type="digital_presence",
                source=dp.channel_type,
                label=f"Kênh {dp.channel_type}",
                url=dp.url,
                status="active" if dp.is_active else "inactive",
                crawled_at=dp.crawled_at,
                detail=(
                    f"checkout={'yes' if dp.has_checkout else 'no'}; "
                    f"confidence={dp.match_confidence}"
                    if dp.match_confidence is not None
                    else f"checkout={'yes' if dp.has_checkout else 'no'}"
                ),
            )
        )

    for ml in listings:
        events.append(
            CompanyCrawlEventOut(
                event_type="marketplace_listing",
                source=ml.platform,
                label=ml.product_name[:80] if ml.product_name else ml.platform,
                url=ml.product_url,
                status="recorded",
                crawled_at=ml.crawled_at,
                detail=_listing_detail(ml),
            )
        )

    events.sort(
        key=lambda e: e.crawled_at or e.label,
        reverse=True,
    )
    return events


def compute_data_quality(
    company: Company,
    presence: list[DigitalPresence],
    listings: list[MarketplaceListing],
    metrics: list,
) -> CompanyDataQualityOut:
    """Deterministic completeness score from persisted fields only."""
    components: dict[str, float] = {}
    notes: list[str] = []

    # Website presence (0–20)
    has_website = any(p.channel_type == "website" and p.is_active for p in presence)
    if not has_website and company.website_url:
        has_website = True
        notes.append("Website URL trên profile; chưa có digital_presence.website active.")
    components["website_presence"] = 20.0 if has_website else 0.0
    if not has_website:
        notes.append("Thiếu kênh website đã xác minh.")

    # Marketplace channel (0–20)
    mkt_presence = [
        p
        for p in presence
        if p.channel_type in _MARKETPLACE_PLATFORMS and p.is_active
    ]
    components["marketplace_channel"] = 20.0 if mkt_presence else 0.0
    if not mkt_presence:
        notes.append(
            "Chưa có Shopee/TikTok/Lazada trong digital_presence "
            "(không bịa kênh)."
        )

    # Match confidence (0–25)
    confidences = [
        p.match_confidence
        for p in presence
        if p.is_active and p.match_confidence is not None
    ]
    if confidences:
        avg_conf = sum(confidences) / len(confidences)
        components["match_confidence"] = round(avg_conf * 25.0, 2)
    else:
        components["match_confidence"] = 0.0
        notes.append("Không có match_confidence trên kênh active.")

    # Listing completeness (0–20) — only marketplace platforms count
    mkt_listings = [ml for ml in listings if ml.platform in _MARKETPLACE_PLATFORMS]
    if mkt_listings:
        complete = sum(1 for ml in mkt_listings if _listing_is_complete(ml))
        ratio = complete / len(mkt_listings)
        components["listing_completeness"] = round(ratio * 20.0, 2)
        if ratio < 1.0:
            notes.append(
                f"Listing marketplace thiếu price×units hoặc revenue_est "
                f"({complete}/{len(mkt_listings)} đủ)."
            )
    else:
        components["listing_completeness"] = 0.0
        notes.append("Không có listing Shopee/TikTok/Lazada — online est. có thể = 0.")

    # Digital metrics present (0–15)
    has_metric = any(
        getattr(m, "online_revenue_est", None) is not None for m in metrics
    )
    components["digital_metrics"] = 15.0 if has_metric else 0.0
    if not has_metric:
        notes.append(
            "Chưa có digital_metrics (chạy job metrics / compute_all_digital_metrics)."
        )

    score = round(sum(components.values()), 2)
    if score >= 70:
        status = "ok"
    elif score >= 35:
        status = "partial"
    else:
        status = "sparse"

    notes.insert(
        0,
        "Điểm chất lượng = độ đầy đủ / xác minh kênh & listing, "
        "không phải độ chính xác doanh thu thị trường.",
    )

    return CompanyDataQualityOut(
        score=score,
        max_score=100.0,
        components=components,
        notes=notes,
        status=status,
    )


def build_case_study(
    company: Company,
    presence: list[DigitalPresence],
) -> CompanyCaseStudyOut | None:
    if company.stock_code.upper() != _RAL_CODE:
        return None

    by_type = {
        p.channel_type: p
        for p in presence
        if p.is_active
    }
    website = by_type.get("website")
    shopee = by_type.get("shopee")
    tiktok = by_type.get("tiktok")

    website_url = (website.url if website else None) or company.website_url
    shopee_url = shopee.url if shopee else None
    tiktok_url = tiktok.url if tiktok else None

    vsic_name = company.vsic.name_vi if company.vsic else None
    highlights: list[str] = []
    if website_url:
        highlights.append(f"Website bán hàng: {website_url}")
    if shopee_url:
        highlights.append(f"Shop Shopee đã ghi nhận: {shopee_url}")
    if company.vsic_code:
        label = f"VSIC {company.vsic_code}"
        if vsic_name:
            label += f" — {vsic_name}"
        highlights.append(label)
    if company.has_ecommerce_site:
        highlights.append("Có dấu hiệu website TMĐT / checkout.")
    if not tiktok_url:
        highlights.append("TikTok: chưa có trong dữ liệu (không bịa).")

    notes = [
        "Ước lượng online_revenue_est chỉ cộng listing Shopee/TikTok/Lazada; "
        "listing platform=website không tính vào tổng online.",
        "industry_share_pct là tỷ trọng Digital VA trong nhóm VSIC cùng prefix "
        "(không phải tổng ngành GSO).",
    ]

    return CompanyCaseStudyOut(
        stock_code=company.stock_code,
        title="Case study: Rạng Đông (RAL)",
        vsic_code=company.vsic_code,
        vsic_name=vsic_name,
        website_url=website_url,
        shopee_url=shopee_url,
        tiktok_url=tiktok_url,
        highlights=highlights,
        notes=notes,
    )


def _listing_is_complete(ml: MarketplaceListing) -> bool:
    if ml.price is not None and ml.units_sold_est is not None:
        return True
    return ml.revenue_est is not None


def _listing_detail(ml: MarketplaceListing) -> str:
    parts = [f"platform={ml.platform}"]
    if ml.price is not None:
        parts.append(f"price={ml.price}")
    if ml.units_sold_est is not None:
        parts.append(f"units_est={ml.units_sold_est}")
    if ml.revenue_est is not None:
        parts.append(f"revenue_est={ml.revenue_est}")
    return "; ".join(parts)
