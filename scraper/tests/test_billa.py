from decimal import Decimal
from pathlib import Path

import pytest

from scraper.sources.billa import declared_count, parse_images, parse_tiles

FIXTURE = Path(__file__).parent / "fixtures" / "billa" / "lihoviny_two_tiles.html"


@pytest.fixture(scope="module")
def html():
    return FIXTURE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def items(html):
    return list(parse_tiles(html))


def _by(items, sku, price_type):
    for it in items:
        if it.store_sku == sku and it.price_type == price_type:
            return it
    raise AssertionError(f"no {price_type} for {sku}")


def test_klub_tile_yields_regular_and_loyalty(items):
    assert {i.price_type for i in items if i.store_sku == "82219425"} == {"regular", "loyalty"}
    regular = _by(items, "82219425", "regular")
    loyalty = _by(items, "82219425", "loyalty")
    assert regular.raw_name == "Božkov Originál Tuzemský 0,5l"
    assert regular.price_czk == Decimal("200.90")
    assert loyalty.price_czk == Decimal("109.90")
    assert loyalty.regular_czk == Decimal("200.90")
    assert regular.volume_ml == 500
    assert regular.source_kind == "catalog"
    assert regular.url == "https://www.billa.cz/produkt/bozkov-original-tuzemsky-05l-82219425"


def test_regular_only_tile(items):
    assert {i.price_type for i in items if i.store_sku == "82244858"} == {"regular"}
    jager = _by(items, "82244858", "regular")
    assert jager.volume_ml == 700
    assert jager.price_czk > 0


def test_images_from_payload_by_article_number(html):
    images = parse_images(html)
    assert set(images) == {"82219425", "82244858"}
    assert all(u.startswith("https://images.cdn.") and u.endswith("-medium.jpg") for u in images.values())
    assert "/82-219425-" in images["82219425"]


def test_declared_count():
    assert declared_count("<body><div>456 produktů</div></body>") == 456
    assert declared_count("<body>nic</body>") == 0


def test_declared_count_does_not_glue_neighbouring_numbers():
    assert declared_count("<body><span>44</span><span>456 produktů</span></body>") == 456
