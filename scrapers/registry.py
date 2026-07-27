"""Registry of supported stores. Adding a store means adding one scraper
class here — nothing else in the app needs to change."""
from __future__ import annotations

from scrapers.base_scraper import BaseScraper
from scrapers.books_to_scrape_scraper import BooksToScrapeScraper
from scrapers.scrapeme_scraper import ScrapeMeScraper

SCRAPERS: dict[str, type[BaseScraper]] = {
    BooksToScrapeScraper.store_name: BooksToScrapeScraper,
    ScrapeMeScraper.store_name: ScrapeMeScraper,
}


def get_scraper(store: str) -> BaseScraper:
    scraper_cls = SCRAPERS.get(store)
    if scraper_cls is None:
        raise ValueError(f"Unsupported store: {store!r}. Supported: {list(SCRAPERS)}")
    return scraper_cls()


def supported_stores() -> list[str]:
    return list(SCRAPERS)
