"""Tesco parser.

Source: https://nakup.itesco.cz/shop/cs-CZ/browse/napoje/lihoviny (server-rendered
HTML, no catalogue JSON). Pagination via ?page=N&count=24.

Tesco runs Akamai / DataDome in front of the shop and hard-blocks `httpx` with
a 403 (verified in M0 spike). A real browser from a residential IP passes
without any header spoofing, so this source uses Playwright Chromium.
Selectors come straight out of 04 Zdroje/Tesco.md; the paired fixture
`tests/fixtures/tesco/lihoviny_two_tiles.html` covers both the Clubcard-promo
and plain-regular tile shapes.

For each tile the parser yields:
  - price_type='regular' from .online-components-product-tile-price__text
  - price_type='loyalty' when the Clubcard container is present, with
    promo_from=today, promo_to from the "Nabídka platí do …" text, and
    regular_czk = the plain price on the same tile.
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterator
from datetime import date, datetime
from decimal import Decimal

from selectolax.lexbor import LexborHTMLParser as HTMLParser
from selectolax.lexbor import LexborNode as Node

from scraper.matching.normalize import parse as normalize_name
from scraper.models import ScrapedItem
from scraper.sources import register
from scraper.sources.base import Source

log = logging.getLogger(__name__)

STORE_CODE = "tesco"
BASE_URL = "https://nakup.itesco.cz"
CATEGORY_PATH = "/shop/cs-CZ/browse/napoje/lihoviny"
PAGE_SIZE = 48
MAX_PAGES = 20  # hard safety cap; the current category is 346 items / 48 per page ≈ 8

_PRICE_RE = re.compile(r"(\d+)[,.](\d{1,2})")
# Pagination: "Zobrazeno 1 až 24 z 346 produktů".
_TOTAL_RE = re.compile(r"z\s+(\d+)\s+produk")
_DATE_RE = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})")


@register
class Tesco(Source):
    code = STORE_CODE
    needs_browser = True

    def fetch(self) -> Iterator[ScrapedItem]:
        from playwright.sync_api import sync_playwright

        # Visible browser window; the shop's price module hydrates more
        # reliably that way. Owner can set TESCO_HEADLESS=1 in scraper/.env
        # to try the quiet background mode instead.
        headless = os.environ.get("TESCO_HEADLESS", "0") == "1"
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=headless)
            context = browser.new_context(
                locale="cs-CZ", viewport={"width": 1366, "height": 900}
            )
            page = context.new_page()
            try:
                total_pages = self._discover_total_pages(page)
                log.info("tesco: paginating %d page(s), %d items/page", total_pages, PAGE_SIZE)
                for page_no in range(1, total_pages + 1):
                    url = self._page_url(page_no)
                    page.goto(url, wait_until="networkidle", timeout=30_000)
                    try:
                        page.wait_for_selector(
                            "li[data-testid] p.online-components-product-tile-price__text",
                            timeout=10_000,
                        )
                    except Exception:
                        log.warning("tesco: price module did not render on page %d", page_no)
                    html = page.content()
                    yield from parse_tiles(html)
            finally:
                context.close()
                browser.close()

    def _discover_total_pages(self, page) -> int:
        page.goto(self._page_url(1), wait_until="domcontentloaded", timeout=30_000)
        text = page.content()
        m = _TOTAL_RE.search(text)
        if not m:
            return 1
        total_items = int(m.group(1))
        pages = -(-total_items // PAGE_SIZE)  # ceil
        return min(pages, MAX_PAGES)

    @staticmethod
    def _page_url(page_no: int) -> str:
        return f"{BASE_URL}{CATEGORY_PATH}?sortBy=relevance&page={page_no}&count={PAGE_SIZE}"


# ---------------------------------------------------------------------------
# HTML parsing — called straight from fixture-backed tests.
# ---------------------------------------------------------------------------


def parse_tiles(html: str) -> Iterator[ScrapedItem]:
    tree = HTMLParser(html)
    for tile in tree.css("li[data-testid]"):
        if not tile.css_first(".online-components-product-tile-product-link__link"):
            continue
        try:
            yield from _tile_items(tile)
        except Exception as exc:
            name_node = tile.css_first(
                ".online-components-product-tile-product-heading__heading a"
            )
            raw = name_node.text(strip=True) if name_node else "?"
            log.warning("tesco: skipping tile %r — %s", raw, exc)
            continue


def _tile_items(tile: Node) -> Iterator[ScrapedItem]:
    store_sku = tile.attributes.get("data-testid")
    if not store_sku:
        return

    name_link = tile.css_first(".online-components-product-tile-product-heading__heading a")
    if name_link is None:
        return
    raw_name = name_link.text(strip=True)
    url = name_link.attributes.get("href")

    parsed = normalize_name(raw_name)
    if parsed.is_multipack:
        log.info("tesco: skipping multipack %r", raw_name)
        return

    img = tile.css_first("img.online-components-product-tile-product-image__image")
    image_url = _strip_image_resize_query(img.attributes.get("src")) if img else None

    regular_node = tile.css_first("p.online-components-product-tile-price__text")
    if regular_node is None:
        # Some tiles have "Momentálně nedostupné" — skip.
        return
    regular_price = _price_from_text(regular_node.text())
    if regular_price is None:
        return

    base = dict(
        store_code=STORE_CODE,
        store_sku=store_sku,
        raw_name=raw_name,
        volume_ml=parsed.volume_ml,
        abv=parsed.abv,
        url=url,
        image_url=image_url,
        source_kind="catalog",
        raw={"testid": store_sku},
    )

    # Always emit the regular price first.
    yield ScrapedItem(
        **base,
        price_czk=regular_price,
        price_type="regular",
    )

    clubcard = tile.css_first(".online-components-product-tile-clubcard-promotion__wrapper")
    if clubcard is None:
        return
    loyalty = _parse_clubcard(clubcard, regular_price)
    if loyalty is None:
        return
    loyalty_price, promo_to = loyalty
    yield ScrapedItem(
        **base,
        price_czk=loyalty_price,
        price_type="loyalty",
        regular_czk=regular_price,
        promo_from=date.today(),
        promo_to=promo_to,
    )


def _parse_clubcard(container: Node, regular_price: Decimal) -> tuple[Decimal, date | None] | None:
    price_node = container.css_first(".ddsweb-value-bar__content-text")
    if price_node is None:
        return None
    price = _price_from_text(price_node.text())
    if price is None or price >= regular_price:
        return None

    terms = container.css_first(".ddsweb-value-bar__terms")
    promo_to = _parse_cz_date(terms.text()) if terms else None
    return price, promo_to


def _price_from_text(text: str) -> Decimal | None:
    m = _PRICE_RE.search(text.replace("\xa0", " "))
    if not m:
        return None
    return Decimal(f"{m.group(1)}.{m.group(2)}")


def _parse_cz_date(text: str) -> date | None:
    m = _DATE_RE.search(text.replace("\xa0", " "))
    if not m:
        return None
    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date()
    except ValueError:
        return None


def _strip_image_resize_query(src: str | None) -> str | None:
    if not src:
        return None
    return src.split("?", 1)[0]
