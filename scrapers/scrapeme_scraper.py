"""
Scraper for scrapeme.live — a WooCommerce-based scraping sandbox (Pokemon
merch). robots.txt only disallows /wp-admin/, so /shop/ product pages are
explicitly permitted.
"""
from __future__ import annotations

import re
from urllib.parse import quote

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, ScrapedProduct, ScrapeError, SearchResult

PRICE_RE = re.compile(r"[\d.]+")


class ScrapeMeScraper(BaseScraper):
    store_name = "scrapeme"

    def fetch(self, product_url: str) -> ScrapedProduct:
        resp = self._get(product_url)
        soup = BeautifulSoup(resp.text, "html.parser")

        summary = soup.select_one("div.summary.entry-summary")
        if summary is None:
            raise ScrapeError(f"No product summary found on {product_url}")

        price_el = summary.select_one("p.price .woocommerce-Price-amount")
        if price_el is None:
            raise ScrapeError(f"No price element found on {product_url}")
        match = PRICE_RE.search(price_el.get_text())
        if not match:
            raise ScrapeError(f"Could not parse price from {price_el.get_text()!r}")
        price = float(match.group())

        title_el = summary.select_one("h1.product_title")
        name = title_el.get_text(strip=True) if title_el else product_url

        return ScrapedProduct(name=name, price=price, currency="GBP")

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        # Native WooCommerce search — real results from the store's own catalog.
        url = f"https://scrapeme.live/?s={quote(query)}&post_type=product"
        resp = self._get(url)

        # WooCommerce redirects straight to the product page (skipping the
        # results list entirely) when a search has exactly one strong
        # match. Parsing that page with the results-list selectors below
        # would silently pick up its "related products" carousel instead —
        # caught by testing search("pikachu") against the live site, which
        # returned Ivysaur/Squirtle/Metapod instead of Pikachu itself.
        if "/shop/" in resp.url and "?s=" not in resp.url:
            try:
                product = self.fetch(resp.url)
            except ScrapeError:
                return []
            return [SearchResult(name=product.name, price=product.price, product_url=resp.url, currency=product.currency)]

        soup = BeautifulSoup(resp.text, "html.parser")

        results: list[SearchResult] = []
        for li in soup.select("li.product")[:limit]:
            link_el = li.select_one("a.woocommerce-loop-product__link")
            title_el = li.select_one("h2.woocommerce-loop-product__title")
            price_el = li.select_one("span.price .woocommerce-Price-amount")
            if link_el is None or title_el is None or price_el is None:
                continue
            match = PRICE_RE.search(price_el.get_text())
            if not match:
                continue
            results.append(
                SearchResult(
                    name=title_el.get_text(strip=True),
                    price=float(match.group()),
                    product_url=link_el["href"],
                    currency="GBP",
                )
            )
        return results
