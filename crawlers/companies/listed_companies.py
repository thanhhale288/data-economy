"""Listed manufacturing company crawler."""

import json
import re
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from backend.app.models import Company, DigitalPresence

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SEED_FILE = DATA_DIR / "seeds" / "companies.json"

ECOMMERCE_KEYWORDS = [
    "giỏ hàng",
    "cart",
    "checkout",
    "mua ngay",
    "đặt hàng",
    "add to cart",
    "shop now",
    "thanh toán",
]


def detect_ecommerce_site(url: str) -> tuple[bool, bool]:
    """Returns (has_ecommerce, has_checkout)."""
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code != 200:
                return False, False
            text = response.text.lower()
            has_shop = any(
                kw in text
                for kw in ["shop", "cửa hàng", "sản phẩm", "product", "mua hàng"]
            )
            has_checkout = any(kw in text for kw in ECOMMERCE_KEYWORDS)
            return has_shop, has_checkout
    except Exception:
        return False, False


def crawl_company_website(company: Company) -> dict:
    if not company.website_url:
        return {"has_ecommerce_site": False, "has_checkout": False}
    has_shop, has_checkout = detect_ecommerce_site(company.website_url)
    return {"has_ecommerce_site": has_shop, "has_checkout": has_checkout}


def load_seed_companies() -> list[dict]:
    with open(SEED_FILE) as f:
        return json.load(f)


def update_company_from_seed(db: Session, seed: dict) -> bool:
    company = (
        db.query(Company).filter(Company.stock_code == seed["stock_code"]).first()
    )
    if not company:
        return False

    website_info = crawl_company_website(company)
    company.has_ecommerce_site = website_info["has_ecommerce_site"] or seed.get(
        "has_ecommerce_site", False
    )
    company.digital_channels = seed.get("digital_channels")
    company.updated_at = datetime.utcnow()

    for dp in company.digital_presence:
        if dp.channel_type == "website":
            dp.has_checkout = website_info["has_checkout"]
            dp.is_active = True
            dp.crawled_at = datetime.utcnow()

    db.commit()
    return True


def run_company_crawl(db: Session) -> int:
    seeds = load_seed_companies()
    count = 0
    for seed in seeds:
        if update_company_from_seed(db, seed):
            count += 1
    return count
