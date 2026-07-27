"""
Checks each active tracked item on a cadence determined by the owning
user's tier (hourly for Pro, daily for Free), scrapes the current price,
records it in price_history, and updates tracked_items.current_price.

A scrape failure for one item (site layout changed, item unavailable,
network blip) is logged and skipped — it never aborts the rest of the
batch. Every run is logged to scraper_runs for the admin/health view.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import FREE_TIER_CHECK_INTERVAL_HOURS, PRO_TIER_CHECK_INTERVAL_HOURS
from backend.db.models import PriceHistory, ScraperRun, TrackedItem, User
from scrapers.base_scraper import ScrapeError
from scrapers.registry import get_scraper
from workers.logging_setup import get_logger

logger = get_logger("price_scraper")


def _is_due(item: TrackedItem, db: Session, now: datetime) -> bool:
    interval_hours = (
        PRO_TIER_CHECK_INTERVAL_HOURS if item.user.subscription_tier == "pro" else FREE_TIER_CHECK_INTERVAL_HOURS
    )
    last_checked = (
        db.query(func.max(PriceHistory.checked_at))
        .filter(PriceHistory.tracked_item_id == item.id)
        .scalar()
    )
    if last_checked is None:
        return True
    if last_checked.tzinfo is None:
        last_checked = last_checked.replace(tzinfo=timezone.utc)
    return now - last_checked >= timedelta(hours=interval_hours)


def check_item(item: TrackedItem, db: Session) -> float | None:
    """Scrape one item and record the result. Returns the new price, or
    None if the scrape failed (already logged)."""
    scraper = get_scraper(item.store)
    try:
        result = scraper.fetch(item.product_url)
    except ScrapeError as exc:
        logger.warning("Scrape failed for item %d (%s): %s", item.id, item.store, exc)
        return None

    db.add(PriceHistory(tracked_item_id=item.id, price=result.price))
    item.current_price = result.price
    if result.name and not item.product_name:
        item.product_name = result.name
    db.commit()
    logger.info("Item %d (%s): price=%.2f", item.id, item.store, result.price)
    return result.price


def run_price_checks(db: Session, now: datetime | None = None) -> dict[str, int]:
    now = now or datetime.now(timezone.utc)

    items = (
        db.query(TrackedItem)
        .join(User)
        .filter(TrackedItem.is_active.is_(True))
        .all()
    )

    checked = 0
    failed = 0
    error_messages: list[str] = []

    for item in items:
        if not _is_due(item, db, now):
            continue
        price = check_item(item, db)
        if price is None:
            failed += 1
            error_messages.append(f"item {item.id} ({item.store})")
        else:
            checked += 1

    db.add(
        ScraperRun(
            scraper_name="price_scraper",
            status="failure" if failed and not checked else "success",
            items_checked=checked,
            items_failed=failed,
            error_message="; ".join(error_messages) if error_messages else None,
        )
    )
    db.commit()

    logger.info("Price check run complete: checked=%d failed=%d", checked, failed)
    return {"checked": checked, "failed": failed}
