"""
Cross-store price comparison: search a product name once, get real results
from every supported store's own search/catalog, sorted by price, with any
active discount codes for that store attached.

Known limitation, documented rather than hidden: the two price-tracking
demo stores (books.toscrape.com, scrapeme.live — scraping sandboxes with no
real coupons) and the discount_codes demo data (Nike/Target/Walmart/Adidas,
scraped from coupons.com) are different demo catalogs, since no
scraping-permitted sandbox site publishes both real products and real
coupons for the same catalog. In production, discount scraping would target
the same stores being price-tracked, and this join would actually light up.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.models import DiscountCode
from backend.db.session import get_db
from scrapers.base_scraper import ScrapeError
from scrapers.registry import SCRAPERS
from workers.logging_setup import get_logger

router = APIRouter(prefix="/search", tags=["search"])
logger = get_logger("search_api")


class ComparisonResult(BaseModel):
    store: str
    name: str
    price: float
    currency: str
    product_url: str
    active_discount_codes: int


@router.get("", response_model=list[ComparisonResult])
def compare_prices(
    q: str = Query(min_length=2),
    db: Session = Depends(get_db),
) -> list[ComparisonResult]:
    results: list[ComparisonResult] = []

    for store_name, scraper_cls in SCRAPERS.items():
        try:
            matches = scraper_cls().search(q, limit=5)
        except ScrapeError as exc:
            logger.warning("Search failed for store %s: %s", store_name, exc)
            continue

        discount_count = (
            db.query(DiscountCode).filter(DiscountCode.store.ilike(store_name)).count()
        )

        for m in matches:
            results.append(
                ComparisonResult(
                    store=store_name,
                    name=m.name,
                    price=m.price,
                    currency=m.currency,
                    product_url=m.product_url,
                    active_discount_codes=discount_count,
                )
            )

    results.sort(key=lambda r: r.price)
    return results
