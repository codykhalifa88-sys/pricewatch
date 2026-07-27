"""
Scraper for books.toscrape.com — a scraping sandbox explicitly built (by
Zyte) for practicing scraping. No robots.txt restrictions.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, ScrapedProduct, ScrapeError, SearchResult

PRICE_RE = re.compile(r"[\d.]+")
CATALOGUE_BASE = "https://books.toscrape.com/catalogue/"

# books.toscrape.com is a fully static site with no server-side search
# endpoint (verified: /catalogue/search returns 404). Search here means
# crawling its real catalogue listing pages and filtering by title —
# capped at a few pages so a search doesn't walk the whole ~1000-book
# catalog on every request. A production integration would use the
# store's real search/product API instead of this workaround.
MAX_CATALOGUE_PAGES_TO_SCAN = 10


class BooksToScrapeScraper(BaseScraper):
    store_name = "books_to_scrape"

    def fetch(self, product_url: str) -> ScrapedProduct:
        resp = self._get(product_url)
        soup = BeautifulSoup(resp.text, "html.parser")

        price_el = soup.select_one("p.price_color")
        if price_el is None:
            raise ScrapeError(f"No price element found on {product_url}")
        match = PRICE_RE.search(price_el.get_text())
        if not match:
            raise ScrapeError(f"Could not parse price from {price_el.get_text()!r}")
        price = float(match.group())

        title_el = soup.select_one("div.product_main h1")
        name = title_el.get_text(strip=True) if title_el else None
        if not name:
            title_tag = soup.select_one("title")
            name = title_tag.get_text(strip=True).split("|")[0].strip() if title_tag else product_url

        return ScrapedProduct(name=name, price=price, currency="GBP")

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        query_lower = query.lower()
        results: list[SearchResult] = []

        for page in range(1, MAX_CATALOGUE_PAGES_TO_SCAN + 1):
            if len(results) >= limit:
                break
            try:
                resp = self._get(f"{CATALOGUE_BASE}page-{page}.html")
            except ScrapeError:
                break  # ran past the last page

            soup = BeautifulSoup(resp.text, "html.parser")
            articles = soup.select("article.product_pod")
            if not articles:
                break

            for article in articles:
                link_el = article.select_one("h3 a")
                price_el = article.select_one("p.price_color")
                if link_el is None or price_el is None:
                    continue
                title = link_el.get("title") or link_el.get_text(strip=True)
                if query_lower not in title.lower():
                    continue
                match = PRICE_RE.search(price_el.get_text())
                if not match:
                    continue
                results.append(
                    SearchResult(
                        name=title,
                        price=float(match.group()),
                        product_url=CATALOGUE_BASE + link_el["href"],
                        currency="GBP",
                    )
                )
                if len(results) >= limit:
                    break

        return results
