"""
Entrypoint for the background worker process (`python -m workers.scheduler`).

Runs on a short tick (default 15 minutes); price_scraper.run_price_checks
itself decides which items are actually due based on the owning user's
tier, so the scheduler doesn't need separate hourly/daily triggers.
"""
from __future__ import annotations

import os
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from backend.db.session import SessionLocal
from workers.alert_sender import run_alert_checks
from workers.discount_scraper import run_discount_scrape
from workers.logging_setup import get_logger
from workers.price_scraper import run_price_checks

logger = get_logger("scheduler")

TICK_MINUTES = int(os.getenv("WORKER_TICK_MINUTES", "15"))
DISCOUNT_SCRAPE_HOUR = int(os.getenv("DISCOUNT_SCRAPE_HOUR", "3"))


def price_and_alert_tick() -> None:
    db = SessionLocal()
    try:
        run_price_checks(db)
        run_alert_checks(db)
    except Exception:
        logger.exception("price_and_alert_tick failed")
    finally:
        db.close()


def discount_scrape_tick() -> None:
    db = SessionLocal()
    try:
        run_discount_scrape(db)
    except Exception:
        logger.exception("discount_scrape_tick failed")
    finally:
        db.close()


def main() -> None:
    scheduler = BlockingScheduler()
    scheduler.add_job(price_and_alert_tick, "interval", minutes=TICK_MINUTES, next_run_time=datetime.now())
    scheduler.add_job(discount_scrape_tick, "cron", hour=DISCOUNT_SCRAPE_HOUR)

    logger.info("Worker started: price/alert tick every %d min, discount scrape daily at %02d:00", TICK_MINUTES, DISCOUNT_SCRAPE_HOUR)
    scheduler.start()


if __name__ == "__main__":
    main()
