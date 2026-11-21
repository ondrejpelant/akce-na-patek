"""Penny parser.

Source: https://www.penny.cz/category/alkohol-24 (SSR Nuxt 3 HTML).
Spike notes and selector reference: 04 Zdroje/Penny.md.

For each product tile the page yields two ScrapedItems with the same
store_sku:
  - price_type='promo'    — the weekly deal price
  - price_type='regular'  — the strikethrough "price before discount",
                            which populates `leaflet_regular` in SCD2.
"""

from __future__ import annotations

import hashlib
import logging
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

CATEGORY_URL = "https://www.penny.cz/category/alkohol-24"
STORE_CODE = "penny"

# "109,90 Kč" (with non-breaking space between number and Kč)
_PRICE_RE = re.compile(r"(\d+)[,.](\d{1,2})")
# "od st 18.11.2026", "do út 24.11.2026"
_DATE_RE = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})")
# "88442352" — store_sku is the trailing digit group of `data-product-slug`.
_SKU_RE = re.compile(r"-(\d+)$")


@register
class Penny(Source):
    code = STORE_CODE
    needs_browser = False

    def fetch(self) -> Iterator[ScrapedItem]:
        resp = self.http.get(CATEGORY_URL)
        yield from parse_tiles(resp.text)


def parse_tiles(html: str) -> Iterator[ScrapedItem]:
    tree = HTMLParser(html)
    for tile in tree.css(".ws-product-tile"):
        try:
            yield from _tile_items(tile)
        except Exception as exc:
            name = tile.attributes.get("data-teaser-name") or "?"
            log.warning("penny: skipping tile %r — %s", name, exc)
            continue


def _tile_items(tile: Node) -> Iterator[ScrapedItem]:
    raw_name = tile.attributes.get("data-teaser-name")
    slug = tile.attributes.get("data-product-slug")
    if not raw_name or not slug:
        return

    store_sku = _sku_from_slug(slug)
    link_node = tile.css_first("a.ws-product-tile__link")
    url = f"https://www.penny.cz{link_node.attributes.get('href')}" if link_node else None

    volume_node = tile.css_first(".ws-product-information__piece-description li")
    parsed = normalize_name(raw_name + " " + (volume_node.text(strip=True) if volume_node else ""))
    if parsed.is_multipack:
        log.info("penny: skipping multipack %r", raw_name)
        return

    promo_main = tile.css_first(".ws-product-price-value__main")
    if promo_main is None:
        return
    promo_price = _price_from_text(promo_main.text(strip=True))
    if promo_price is None:
        return

    strike = tile.css_first(".ws-product-price-strike s")
    regular_price = _price_from_text(strike.text(strip=True)) if strike else None

    promo_from, promo_to = _validity(tile)

    # image placeholder in SSR is a 1x1 base64; real image loads on scroll.
    # We skip image_url for now and let the UI render a per-category fallback.
    image_url = None

    base = dict(
        store_code=STORE_CODE,
        store_sku=store_sku,
        raw_name=raw_name,
        volume_ml=parsed.volume_ml,
        abv=parsed.abv,
        url=url,
        image_url=image_url,
        source_kind="leaflet",
        raw={"slug": slug},
    )

    yield ScrapedItem(
        **base,
        price_czk=promo_price,
        price_type="promo",
        regular_czk=regular_price,
        promo_from=promo_from,
        promo_to=promo_to,
    )

    if regular_price is not None:
        yield ScrapedItem(
            **base,
            price_czk=regular_price,
            price_type="regular",
        )


def _sku_from_slug(slug: str) -> str:
    """Pull the trailing digit group out of a slug.

    "vodka-jemna-375-kralovska-palirna-88442352" → "88442352".
    If no trailing digits (unlikely), fall back to a hash so the row is still
    stable across runs without colliding with real SKUs.
    """
    m = _SKU_RE.search(slug)
    if m:
        return m.group(1)
    return "h" + hashlib.sha1(slug.encode()).hexdigest()[:12]


def _price_from_text(text: str) -> Decimal | None:
    m = _PRICE_RE.search(text.replace("\xa0", " "))
    if not m:
        return None
    return Decimal(f"{m.group(1)}.{m.group(2)}")


def _validity(tile: Node) -> tuple[date | None, date | None]:
    """First date = promo_from, second date = promo_to.

    The container has two <div> children (od / do), but we read the two
    DD.MM.YYYY matches straight out of the combined text — it is order-stable
    and avoids engine-specific child-selector quirks.
    """
    validity = tile.css_first(".ws-product-price-validity")
    if validity is None:
        return None, None
    matches = _DATE_RE.findall(validity.text().replace("\xa0", " "))
    if len(matches) < 2:
        return None, None
    return _match_to_date(matches[0]), _match_to_date(matches[1])


def _match_to_date(m: tuple[str, str, str]) -> date | None:
    day, month, year = (int(x) for x in m)
    try:
        return datetime(year, month, day).date()
    except ValueError:
        return None
