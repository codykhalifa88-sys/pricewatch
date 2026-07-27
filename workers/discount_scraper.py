"""
Scrapes coupons.com's per-store coupon pages (real, server-rendered HTML;
robots.txt allows it — only /api/* is disallowed) and upserts into
discount_codes.

Honest limitation, documented rather than worked around: coupons.com only
puts discount_percent/description/expiry in the static HTML. The literal
code string for "CODE"-type offers is revealed by a client-side action
(likely an AJAX call behind the "Show coupon code" button) and isn't
present anywhere in the page source — verified by fetching and searching
the raw HTML, not assumed. Reproducing that click would need a headless
browser for a single field, so instead:
  - "Deals" (no code needed, discount applies automatically via the link)
    are stored with code="AUTOMATIC" — this is accurate, not a placeholder.
  - "Codes" offers are stored with code="SEE SITE" plus the real
    description/discount_percent/expiry, since fabricating a fake code
    string would be worse than admitting it isn't scraped.
"""
from __future__ import annotations

import re
import time
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.db.models import DiscountCode, ScraperRun
from workers.logging_setup import get_logger

logger = get_logger("discount_scraper")

USER_AGENT = "PriceWatchBot/1.0 (+https://github.com/pricewatch; portfolio demo, low request rate)"
MIN_DELAY_SECONDS = 3.0

# coupons.com per-store slugs to aggregate. Deliberately real, well-known
# retail brands, independent of the two price-tracking demo stores.
STORE_SLUGS = {
    "nike": "Nike",
    "target": "Target",
    "walmart": "Walmart",
    "adidas": "Adidas",
}

PERCENT_RE = re.compile(r"(\d+)%")
EXPIRY_RE = re.compile(r"Until (\d{2}/\d{2}/\d{4})")


def _parse_store_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    offers = []

    for title_el in soup.select("h3[id='offerbasecard-title']"):
        card = title_el.find_parent("div", attrs={"role": "button"})
        if card is None:
            continue

        tag_el = card.select_one("span[id^='voucher-tag-']")
        is_code = tag_el is not None and tag_el.get_text(strip=True).upper() == "CODE"

        percent_match = PERCENT_RE.search(card.get_text())
        discount_percent = float(percent_match.group(1)) if percent_match else None

        expiry_match = EXPIRY_RE.search(card.get_text())
        expires_at: date | None = None
        if expiry_match:
            try:
                expires_at = datetime.strptime(expiry_match.group(1), "%m/%d/%Y").date()
            except ValueError:
                expires_at = None

        description_el = card.select_one("[id='offerbasecard-conditions'] p")
        description = description_el.get_text(strip=True) if description_el else title_el.get_text(strip=True)

        offers.append(
            {
                "code": "SEE SITE" if is_code else "AUTOMATIC",
                "description": description,
                "discount_percent": discount_percent,
                "expires_at": expires_at,
            }
        )

    return offers


def _fetch_store_offers(slug: str) -> list[dict]:
    resp = requests.get(
        f"https://www.coupons.com/coupon-codes/{slug}",
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    resp.raise_for_status()
    return _parse_store_page(resp.text)


def run_discount_scrape(db: Session) -> dict[str, int]:
    total_upserted = 0
    failed_stores: list[str] = []

    for i, (slug, store_name) in enumerate(STORE_SLUGS.items()):
        if i > 0:
            time.sleep(MIN_DELAY_SECONDS)
        try:
            offers = _fetch_store_offers(slug)
        except requests.RequestException as exc:
            logger.warning("Discount scrape failed for %s: %s", store_name, exc)
            failed_stores.append(store_name)
            continue

        for offer in offers:
            stmt = insert(DiscountCode).values(
                store=store_name,
                code=offer["code"],
                description=offer["description"],
                discount_percent=offer["discount_percent"],
                expires_at=offer["expires_at"],
                is_verified=True,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["store", "code"],
                set_={
                    "description": stmt.excluded.description,
                    "discount_percent": stmt.excluded.discount_percent,
                    "expires_at": stmt.excluded.expires_at,
                    "scraped_at": datetime.utcnow(),
                    "is_verified": True,
                },
            )
            db.execute(stmt)
        db.commit()
        total_upserted += len(offers)
        logger.info("Discount scrape: %s -> %d offers", store_name, len(offers))

    db.add(
        ScraperRun(
            scraper_name="discount_scraper",
            status="failure" if failed_stores and not total_upserted else "success",
            items_checked=total_upserted,
            items_failed=len(failed_stores),
            error_message="; ".join(failed_stores) if failed_stores else None,
        )
    )
    db.commit()

    logger.info("Discount scrape run complete: %d offers, %d stores failed", total_upserted, len(failed_stores))
    return {"upserted": total_upserted, "failed_stores": len(failed_stores)}
