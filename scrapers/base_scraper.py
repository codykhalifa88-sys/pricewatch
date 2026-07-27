"""
Shared interface every store scraper implements, plus a small per-scraper
rate limiter.

Deliberate design choice (see README "Key Design Decisions"): PriceWatch
supports a small, fixed list of stores with a dedicated scraper each,
rather than trying to accept "any URL." A general-purpose scraper that
guesses at price selectors across arbitrary sites breaks constantly and
would make every demo look flaky; a handful of well-understood, explicitly
scraping-permitted sites (checked against robots.txt) is what actually
holds up, and mirrors how a real version of this product would instead use
official retailer partner APIs.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests

USER_AGENT = "PriceWatchBot/1.0 (+https://github.com/pricewatch; portfolio demo, low request rate)"
REQUEST_TIMEOUT_SECONDS = 10


@dataclass
class ScrapedProduct:
    name: str
    price: float
    currency: str = "GBP"


@dataclass
class SearchResult:
    name: str
    price: float
    product_url: str
    currency: str = "GBP"


class ScrapeError(Exception):
    """Raised when a page can't be fetched or parsed — callers catch this
    and skip the item rather than crashing the whole batch."""


class BaseScraper(ABC):
    store_name: str
    min_delay_seconds: float = 2.0  # be a good citizen — don't hammer the site

    def __init__(self) -> None:
        self._last_request_at: float = 0.0
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})

    def _respect_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_delay_seconds:
            time.sleep(self.min_delay_seconds - elapsed)
        self._last_request_at = time.monotonic()

    def _get(self, url: str) -> requests.Response:
        self._respect_rate_limit()
        try:
            resp = self._session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise ScrapeError(f"Request failed for {url}: {exc}") from exc
        return resp

    @abstractmethod
    def fetch(self, product_url: str) -> ScrapedProduct:
        """Fetch and parse the current price for a product URL. Raises
        ScrapeError if the page can't be fetched or the expected price
        element isn't found (site layout changed, item unavailable, etc)."""
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search this store's real catalog for products matching `query`.
        Powers the cross-store price comparison feature — every result
        here is a live product this store's search/catalog actually
        returned, not a guess at what might match."""
        raise NotImplementedError
