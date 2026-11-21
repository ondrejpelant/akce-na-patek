from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from scraper.sources.penny import parse_og_image, parse_tiles

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "penny"
    / "category_alkohol_week47.html"
)


@pytest.fixture(scope="module")
def items():
    html = FIXTURE.read_text(encoding="utf-8")
    return list(parse_tiles(html))


def _by_sku(items, store_sku, price_type):
    for it in items:
        if it.store_sku == store_sku and it.price_type == price_type:
            return it
    raise AssertionError(f"no item with sku={store_sku} type={price_type}")


def test_each_tile_yields_promo_and_regular(items):
    skus = {it.store_sku for it in items}
    assert skus == {"88442352", "88444129"}
    for sku in skus:
        types = {it.price_type for it in items if it.store_sku == sku}
        assert types == {"promo", "regular"}


def test_vodka_promo(items):
    promo = _by_sku(items, "88442352", "promo")
    assert promo.raw_name == "Vodka jemná 37,5% Královská palírna"
    assert promo.store_code == "penny"
    assert promo.source_kind == "leaflet"
    assert promo.volume_ml == 500
    assert promo.abv == Decimal("37.5")
    assert promo.price_czk == Decimal("109.90")
    assert promo.regular_czk == Decimal("139.90")
    assert promo.promo_from == date(2026, 11, 18)
    assert promo.promo_to == date(2026, 11, 24)
    assert promo.url == "https://www.penny.cz/products/vodka-jemna-375-kralovska-palirna-88442352"


def test_vodka_regular_feeds_leaflet_regular_in_scd2(items):
    # The strikethrough price becomes the "regular" line that SCD2 persists as
    # `leaflet_regular` in the loader. Shape-check only here; loader test owns the
    # price_source assertion.
    regular = _by_sku(items, "88442352", "regular")
    assert regular.price_czk == Decimal("139.90")
    assert regular.regular_czk is None  # not used on regular rows
    assert regular.promo_from is None
    assert regular.promo_to is None


def test_tuzemak_shape(items):
    promo = _by_sku(items, "88444129", "promo")
    assert promo.raw_name == "Tuzemák 37,5% Královská palírna"
    assert promo.volume_ml == 500
    assert promo.price_czk == Decimal("109.90")
    assert promo.regular_czk == Decimal("144.90")


def test_og_image_from_product_page():
    html = (
        '<head><meta content="https://images.cdn.europe-west1.gcp.commercetools.com/x/88-442352.jpg" '
        'property="og:image"></head>'
    )
    assert parse_og_image(html) == "https://images.cdn.europe-west1.gcp.commercetools.com/x/88-442352.jpg"


def test_og_image_missing_or_not_https():
    assert parse_og_image("<head></head>") is None
    assert parse_og_image('<meta property="og:image" content="/relative.jpg">') is None
