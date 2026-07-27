"""
Scraper parsing tests, run against real HTML captured from the live sites
(tests/fixtures/*.html) rather than hitting the network on every test run.
The fixtures were saved directly from books.toscrape.com, scrapeme.live,
and coupons.com — not hand-written — so these tests catch real layout
regressions, the same class of bug the discount_scraper's is_code check
actually had during development (see workers/discount_scraper.py history).
"""
from pathlib import Path

import pytest

from scrapers.books_to_scrape_scraper import BooksToScrapeScraper
from scrapers.scrapeme_scraper import ScrapeMeScraper
from workers.discount_scraper import _parse_store_page

FIXTURES = Path(__file__).parent / "fixtures"


class _FakeResponse:
    def __init__(self, text: str, url: str = "") -> None:
        self.text = text
        self.url = url

    def raise_for_status(self) -> None:
        pass


@pytest.fixture()
def books_scraper(monkeypatch):
    scraper = BooksToScrapeScraper()
    html = (FIXTURES / "books_to_scrape_product.html").read_text()
    monkeypatch.setattr(scraper, "_get", lambda url: _FakeResponse(html))
    return scraper


@pytest.fixture()
def scrapeme_scraper(monkeypatch):
    scraper = ScrapeMeScraper()
    html = (FIXTURES / "scrapeme_product.html").read_text()
    monkeypatch.setattr(scraper, "_get", lambda url: _FakeResponse(html))
    return scraper


def test_books_to_scrape_parses_real_page(books_scraper):
    result = books_scraper.fetch("https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")
    assert result.name == "A Light in the Attic"
    assert result.price == 51.77
    assert result.currency == "GBP"


def test_scrapeme_parses_real_page(scrapeme_scraper):
    result = scrapeme_scraper.fetch("https://scrapeme.live/shop/Bulbasaur/")
    assert result.name == "Bulbasaur"
    assert result.price == 63.0


def test_scrapeme_search_multi_match(monkeypatch):
    scraper = ScrapeMeScraper()
    html = (FIXTURES / "scrapeme_search_multi.html").read_text()
    monkeypatch.setattr(scraper, "_get", lambda url: _FakeResponse(html, url="https://scrapeme.live/?s=char&post_type=product"))

    results = scraper.search("char")
    names = {r.name for r in results}
    assert "Charizard" in names
    assert "Charmander" in names
    assert all(r.price > 0 for r in results)


def test_scrapeme_search_single_match_redirect(monkeypatch):
    """Regression test for a real bug: WooCommerce redirects a search with
    exactly one strong match straight to the product page instead of a
    results list. An earlier version parsed that page with the
    results-list selectors and silently returned its "related products"
    carousel (Ivysaur/Squirtle/Metapod) instead of Pikachu itself."""
    scraper = ScrapeMeScraper()
    html = (FIXTURES / "scrapeme_search_single_redirect.html").read_text()
    monkeypatch.setattr(scraper, "_get", lambda url: _FakeResponse(html, url="https://scrapeme.live/shop/Pikachu/"))

    results = scraper.search("pikachu")
    assert len(results) == 1
    assert results[0].name == "Pikachu"
    assert results[0].price > 0


def test_discount_scraper_distinguishes_code_from_deal_offers():
    """Regression test for a real bug: every offer card on coupons.com has
    a voucher-tag span, but only its TEXT ("CODE" vs "DEAL") distinguishes
    an actual promo code from an automatic deal. An earlier version checked
    only the tag's presence and classified every offer as a code."""
    html = (FIXTURES / "coupons_nike.html").read_text()
    offers = _parse_store_page(html)

    assert len(offers) == 15
    codes = [o for o in offers if o["code"] == "SEE SITE"]
    deals = [o for o in offers if o["code"] == "AUTOMATIC"]
    assert len(codes) == 1
    assert len(deals) == 14

    # Every offer should have a real, non-empty description scraped from the page.
    assert all(o["description"] for o in offers)
