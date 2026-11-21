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

from scraper.http import BlockedError
from scraper.matching.normalize import parse as normalize_name
from scraper.models import ScrapedItem
from scraper.sources import register
from scraper.sources.base import Source

log = logging.getLogger(__name__)

STORE_CODE = "tesco"
BASE_URL = "https://nakup.itesco.cz"
CATEGORY_PATH = "/shop/cs-CZ/browse/napoje/lihoviny"
PAGE_SIZE = 48

# Tesco answers 403 to the second page in a session, so each run loads exactly
# one page (48 items) and the next run takes the next listing from this
# rotation. Over successive updates that walks most of the 346 spirits without
# ever requesting more than one page per run. ("" = the whole spirits listing.)
LISTINGS = (
    "", "vodka", "gin", "whisky-bourbon-a-jine-destilaty", "rum-likery-a-elixiry",
    "likery-a-medovina", "konak", "brandy", "tequila", "borovicka",
    "ovocne-destilaty", "tuzemak", "ostatni-lihoviny",
)
SORTS = ("relevance", "price-ascending", "price-descending")
ROTATION = tuple((listing, sort) for sort in SORTS for listing in LISTINGS)

_PRICE_RE = re.compile(r"(\d+)[,.](\d{1,2})")
# Pagination: "Zobrazeno 1 až 24 z 346 produktů".
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
        # The bundled "Chrome for Testing" build fails Windows side-by-side
        # activation on the owner's PC, so default to the system Edge that
        # ships with Windows. PLAYWRIGHT_CHANNEL="" falls back to the bundle.
        channel = os.environ.get("PLAYWRIGHT_CHANNEL", "msedge") or None
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel=channel, headless=headless)
            context = browser.new_context(
                locale="cs-CZ", viewport={"width": 1366, "height": 900}
            )
            page = context.new_page()
            step = _next_rotation_step()
            listing, sort = ROTATION[step]
            try:
                # BlockedError on this single page propagates -> run 'failed'.
                html = self._load_page(page, listing, sort)
            finally:
                context.close()
                browser.close()

        _save_rotation_step(step + 1)
        # partial = SCD2 keeps prices of the items this run did not look at.
        self.partial_reason = (
            f"výpis {step + 1}/{len(ROTATION)}: {listing or 'lihoviny'} · {sort}"
            f" (1 stránka za běh)"
        )
        log.info("tesco: %s", self.partial_reason)
        yield from parse_tiles(html)

    def _load_page(self, page, listing: str, sort: str) -> str:
        # The shop keeps firing analytics beacons, so "networkidle" never
        # settles; wait for DOM + the price element instead.
        resp = page.goto(page_url(listing, sort), wait_until="domcontentloaded", timeout=30_000)
        if resp is not None and resp.status in (401, 403, 429):
            raise BlockedError(f"HTTP {resp.status}")
        try:
            page.wait_for_selector(
                "li[data-testid] p.online-components-product-tile-price__text",
                timeout=15_000,
            )
        except Exception:
            log.warning("tesco: price module did not render on %s", listing or "lihoviny")
        return page.content()


def page_url(listing: str, sort: str) -> str:
    path = f"{CATEGORY_PATH}/{listing}" if listing else CATEGORY_PATH
    return f"{BASE_URL}{path}?sortBy={sort}&count={PAGE_SIZE}"


def _rotation_file():
    from scraper.config import SCRAPER_ROOT

    return SCRAPER_ROOT / ".cache" / "tesco_rotation.txt"


def _next_rotation_step() -> int:
    try:
        return int(_rotation_file().read_text().strip()) % len(ROTATION)
    except (OSError, ValueError):
        return 0


def _save_rotation_step(step: int) -> None:
    path = _rotation_file()
    path.parent.mkdir(exist_ok=True)
    path.write_text(str(step % len(ROTATION)))


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
        source_category=_source_category(tile),
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


def _source_category(tile: Node) -> str | None:
    """Tesco subcategory path from the tile's "Více z kategorie" link,
    e.g. ".../browse/napoje/lihoviny/vodka/cista-vodka" -> "vodka/cista-vodka"."""
    link = tile.css_first("a.online-components-product-tile-rest-of-shelf__rest-of-shelf")
    href = link.attributes.get("href") if link else None
    if not href:
        return None
    marker = f"{CATEGORY_PATH}/"
    idx = href.find(marker)
    if idx < 0:
        return None
    path = href[idx + len(marker):].split("?", 1)[0].strip("/")
    return path.removesuffix("/all") or None


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
