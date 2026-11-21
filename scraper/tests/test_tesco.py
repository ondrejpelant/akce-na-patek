from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from scraper.sources.tesco import parse_tiles

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "tesco"
    / "lihoviny_two_tiles.html"
)


@pytest.fixture(scope="module")
def items():
    html = FIXTURE.read_text(encoding="utf-8")
    return list(parse_tiles(html))


def _by(items, store_sku, price_type):
    for it in items:
        if it.store_sku == store_sku and it.price_type == price_type:
            return it
    raise AssertionError(f"no item for sku={store_sku} type={price_type}")


def test_tile_with_clubcard_yields_regular_and_loyalty(items):
    sku = "205119917"  # Božkov Originál Tuzemský 0,5l — the Clubcard tile
    types = {it.price_type for it in items if it.store_sku == sku}
    assert types == {"regular", "loyalty"}


def test_tile_without_clubcard_yields_regular_only(items):
    sku = "212270700"  # Božkov Vaječný likér 0,5l
    types = {it.price_type for it in items if it.store_sku == sku}
    assert types == {"regular"}


def test_bozkov_regular(items):
    it = _by(items, "205119917", "regular")
    assert it.raw_name == "Božkov Originál Tuzemský 0,5l"
    assert it.store_code == "tesco"
    assert it.source_kind == "catalog"
    assert it.volume_ml == 500
    assert it.price_czk == Decimal("199.90")
    assert it.regular_czk is None
    assert it.url == "https://nakup.itesco.cz/shop/cs-CZ/products/205119917"
    assert it.image_url and it.image_url.endswith(".jpeg")


def test_bozkov_clubcard(items):
    it = _by(items, "205119917", "loyalty")
    assert it.price_czk == Decimal("149.90")
    assert it.regular_czk == Decimal("199.90")
    assert it.promo_from == date.today()
    assert it.promo_to == date(2026, 11, 24)


def test_source_category_from_rest_of_shelf_link(items):
    assert _by(items, "205119917", "regular").source_category == "rum-likery-a-elixiry/likery-a-elixiry"
    assert _by(items, "212270700", "regular").source_category == "likery-a-medovina/kremove-likery"


def test_vajecny_liker_regular(items):
    it = _by(items, "212270700", "regular")
    assert it.volume_ml == 500
    assert it.price_czk == Decimal("149.90")
    assert it.regular_czk is None
