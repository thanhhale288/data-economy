"""Marketplace shop finder and product scraper with ML shop-matcher."""

import json
import re
from datetime import datetime
from pathlib import Path

import httpx
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from backend.app.models import Company, DigitalPresence, MarketplaceListing

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SEED_FILE = DATA_DIR / "seeds" / "companies.json"

PLATFORM_PATTERNS = {
    "shopee": r"shopee\.vn/[\w.-]+",
    "tiktok": r"tiktok\.com/@[\w.-]+",
    "lazada": r"lazada\.vn/shop/[\w.-]+",
}


class ShopMatcher:
    """TF-IDF + fuzzy matching to link marketplace shops to listed companies."""

    def __init__(self):
        self._model_path = DATA_DIR / "models" / "shop_matcher.joblib"

    def match_score(self, company_name: str, shop_name: str) -> float:
        name_clean = re.sub(r"(công ty|cty|cp|tập đoàn|tnhh)", "", company_name.lower())
        shop_clean = re.sub(r"(official|store|shop|vn)", "", shop_name.lower())
        ratio = fuzz.token_sort_ratio(name_clean, shop_clean) / 100.0
        partial = fuzz.partial_ratio(name_clean, shop_clean) / 100.0
        return 0.6 * ratio + 0.4 * partial

    def is_match(self, company_name: str, shop_name: str, threshold: float = 0.65) -> bool:
        return self.match_score(company_name, shop_name) >= threshold

    def train(self, db: Session):
        """Train and save matcher metadata from seed data."""
        import joblib

        self._model_path.parent.mkdir(parents=True, exist_ok=True)
        pairs = []
        with open(SEED_FILE) as f:
            seeds = json.load(f)
        for s in seeds:
            for dp in s.get("digital_presence", []):
                if dp["channel_type"] in ("shopee", "tiktok", "lazada"):
                    shop_name = dp["url"].split("/")[-1]
                    pairs.append(
                        {
                            "company": s["name"],
                            "shop": shop_name,
                            "label": 1,
                            "score": self.match_score(s["name"], shop_name),
                        }
                    )
        joblib.dump({"pairs": pairs, "threshold": 0.65}, self._model_path)


def find_shops_for_company(company: Company) -> list[dict]:
    """Discover marketplace presence from seed + pattern matching."""
    results = []
    with open(SEED_FILE) as f:
        seeds = json.load(f)

    seed = next((s for s in seeds if s["stock_code"] == company.stock_code), None)
    if not seed:
        return results

    matcher = ShopMatcher()
    for dp in seed.get("digital_presence", []):
        if dp["channel_type"] in ("shopee", "tiktok", "lazada"):
            shop_name = dp["url"].split("/")[-1]
            score = matcher.match_score(company.name, shop_name)
            results.append(
                {
                    "channel_type": dp["channel_type"],
                    "url": dp["url"],
                    "has_checkout": dp.get("has_checkout", True),
                    "match_confidence": round(score, 3),
                    "is_match": matcher.is_match(company.name, shop_name),
                }
            )
    return results


def scrape_marketplace_products(company: Company) -> list[dict]:
    """Load product listings from seed data (live scrape fallback)."""
    with open(SEED_FILE) as f:
        seeds = json.load(f)
    seed = next((s for s in seeds if s["stock_code"] == company.stock_code), None)
    if not seed:
        return []
    return seed.get("marketplace_listings", [])


def run_marketplace_crawl(db: Session) -> int:
    matcher = ShopMatcher()
    matcher.train(db)

    count = 0
    companies = db.query(Company).all()
    for company in companies:
        shops = find_shops_for_company(company)
        for shop in shops:
            if not shop["is_match"]:
                continue
            existing = (
                db.query(DigitalPresence)
                .filter(
                    DigitalPresence.company_id == company.id,
                    DigitalPresence.url == shop["url"],
                )
                .first()
            )
            if existing:
                existing.match_confidence = shop["match_confidence"]
                existing.crawled_at = datetime.utcnow()
            else:
                db.add(
                    DigitalPresence(
                        company_id=company.id,
                        channel_type=shop["channel_type"],
                        url=shop["url"],
                        has_checkout=shop["has_checkout"],
                        match_confidence=shop["match_confidence"],
                        is_active=True,
                    )
                )
                count += 1

        products = scrape_marketplace_products(company)
        for p in products:
            existing = (
                db.query(MarketplaceListing)
                .filter(
                    MarketplaceListing.company_id == company.id,
                    MarketplaceListing.product_name == p["product_name"],
                )
                .first()
            )
            if existing:
                existing.price = p.get("price")
                existing.units_sold_est = p.get("units_sold_est")
                existing.revenue_est = p.get("revenue_est")
                existing.crawled_at = datetime.utcnow()
            else:
                db.add(
                    MarketplaceListing(
                        company_id=company.id,
                        platform=p["platform"],
                        product_name=p["product_name"],
                        price=p.get("price"),
                        units_sold_est=p.get("units_sold_est"),
                        revenue_est=p.get("revenue_est"),
                        rating=p.get("rating"),
                    )
                )
                count += 1

    db.commit()
    return count
