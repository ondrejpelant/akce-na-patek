"""Billa parser — regular catalogue prices plus BILLA Klub prices.

Billa closed its e-shop (31. 1. 2026) but kept the product catalogue online
with prices: https://www.billa.cz/produkty/lihoviny-1559 (Nuxt SSR, same REWE
frontend as Penny, so the tile markup and helpers are shared).

Listing quirks (04 Zdroje/Billa.md):
  - `?page=N` returns pages 1..N in one response; a page past the end returns
    nothing, so the declared product count decides N.
  - Tiles only carry a base64 placeholder image; the real URLs sit in the
    Nuxt payload keyed by article number ("82-219425" == sku 82219425).
  - The parent listing has every spirit (456), the subcategories only cover
    ~290 of them; they are fetched just to tag the store category.

Each tile has one or two price blocks:
  "Běžná cena"          -> price_type='regular'
  "S BILLA klub účtem"  -> price_type='loyalty', regular_czk = the regular block
A block with a strikethrough price is an all-customers promo.
"""

from __future__ import annotations

import logging
import math
import re
from collections.abc import Iterator

from selectolax.lexbor import LexborHTMLParser as HTMLParser
from selectolax.lexbor import LexborNode as Node

from scraper.matching.normalize import f_norm
from scraper.matching.normalize import parse as normalize_name
from scraper.models import ScrapedItem
from scraper.sources import register
from scraper.sources.base import Source
from scraper.sources.penny import _price_from_text, _sku_from_slug, _validity

log = logging.getLogger(__name__)

STORE_CODE = "billa"
BASE_URL = "https://www.billa.cz"
PAGE_SIZE = 30
PARENT = "lihoviny-1559"
SUBCATEGORIES = (
    "rum-a-tuzemak-1560",
    "gin-1561",
    "brandy-a-konak-1562",
    "whiskey-a-bourbon-1563",
    "likery-1564",
    "vodka-1566",
)

_DECLARED_RE = re.compile(r"(?<!\d)(\d+)\s*produkt")
_IMAGE_RE = re.compile(
    r"https:\\u002F\\u002Fimages\.cdn\.[^\"]*?\\u002F(\d{2}-\d{6})-[^\"]+?\.(?:jpg|jpeg|png|webp)"
)


@register
class Billa(Source):
    code = STORE_CODE
    needs_browser = False

    def fetch(self) -> Iterator[ScrapedItem]:
        html = self._full_listing(PARENT)
        categories: dict[str, str] = {}
        for sub in SUBCATEGORIES:
            path = sub.rsplit("-", 1)[0]  # "rum-a-tuzemak-1560" -> "rum-a-tuzemak"
            for slug in _tile_slugs(self._full_listing(sub)):
                categories.setdefault(slug, path)
        images = parse_images(html)
        for item in parse_tiles(html):
            slug = item.raw.get("slug", "")
            yield item.model_copy(update={
                "source_category": categories.get(slug),
                "image_url": images.get(item.store_sku),
            })

    def _full_listing(self, category: str) -> str:
        url = f"{BASE_URL}/produkty/{category}"
        first = self.http.get(url).text
        pages = math.ceil(declared_count(first) / PAGE_SIZE)
        if pages <= 1:
            return first
        return self.http.get(url, params={"page": pages}).text


def declared_count(html: str) -> int:
    body = HTMLParser(html).body
    # separator matters: without it adjacent elements glue together
    # ("…44" + "456 produktů" -> "44456 produktů").
    m = _DECLARED_RE.search(body.text(separator=" ") if body else "")
    return int(m.group(1)) if m else 0


def parse_images(html: str) -> dict[str, str]:
    """sku -> first image URL from the Nuxt payload, as the CDN's medium size."""
    out: dict[str, str] = {}
    for m in _IMAGE_RE.finditer(html):
        sku = m.group(1).replace("-", "")
        if sku in out:
            continue
        url = m.group(0).replace("\\u002F", "/")
        out[sku] = re.sub(r"\.(jpg|jpeg|png|webp)$", r"-medium.\1", url)
    return out


def _tile_slugs(html: str) -> list[str]:
    return [t.attributes.get("data-product-slug") or "" for t in HTMLParser(html).css(".ws-product-tile")]


def parse_tiles(html: str) -> Iterator[ScrapedItem]:
    for tile in HTMLParser(html).css(".ws-product-tile"):
        try:
            yield from _tile_items(tile)
        except Exception as exc:
            log.warning("billa: skipping tile %r — %s", tile.attributes.get("data-teaser-name"), exc)


def _tile_items(tile: Node) -> Iterator[ScrapedItem]:
    raw_name = tile.attributes.get("data-teaser-name")
    slug = tile.attributes.get("data-product-slug")
    if not raw_name or not slug:
        return

    volume_node = tile.css_first(".ws-product-information__piece-description li")
    parsed = normalize_name(raw_name + " " + (volume_node.text(strip=True) if volume_node else ""))
    if parsed.is_multipack:
        return

    regular = loyalty = promo = None
    regular_before_promo = None
    for block in tile.css('[data-test="product-price-type"]'):
        value = block.css_first(".ws-product-price-value__main")
        price = _price_from_text(value.text()) if value else None
        if price is None:
            continue
        strike = block.css_first(".ws-product-price-strike s")
        if "klub" in f_norm(block.text()):
            loyalty = price
        elif strike is not None:
            promo = price
            regular_before_promo = _price_from_text(strike.text())
        else:
            regular = price
    regular = regular or regular_before_promo
    if regular is None and promo is None and loyalty is None:
        return

    promo_from, promo_to = _validity(tile)
    base = dict(
        store_code=STORE_CODE,
        store_sku=_sku_from_slug(slug),
        raw_name=raw_name,
        volume_ml=parsed.volume_ml,
        abv=parsed.abv,
        url=f"{BASE_URL}/produkt/{slug}",
        source_kind="catalog",
        raw={"slug": slug},
    )
    if regular is not None:
        yield ScrapedItem(**base, price_czk=regular, price_type="regular")
    if promo is not None:
        yield ScrapedItem(**base, price_czk=promo, price_type="promo", regular_czk=regular,
                          promo_from=promo_from, promo_to=promo_to)
    if loyalty is not None:
        yield ScrapedItem(**base, price_czk=loyalty, price_type="loyalty", regular_czk=regular,
                          promo_from=promo_from, promo_to=promo_to)
