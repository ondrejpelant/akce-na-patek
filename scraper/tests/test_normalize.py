from decimal import Decimal

import pytest

from scraper.matching.normalize import f_norm, parse


@pytest.mark.parametrize(
    "raw,expected_ml,expected_abv",
    [
        ("Finlandia Vodka 40% 0,7 l", 700, Decimal("40")),
        ("Finlandia vodka 0,7 l", 700, None),
        ("Finlandia Vodka 0.7L 40 %", 700, Decimal("40")),
        ("Jameson 1l 40%", 1000, Decimal("40")),
        ("Fernet Stock 500 ml", 500, None),
        ("Jägermeister 70cl 35 % obj.", 700, Decimal("35")),
        ("Becherovka 0,5 l 38 % alk.", 500, Decimal("38")),
        ("Metaxa 7* 0,7 l 40%", 700, Decimal("40")),
        ("Absolut Vodka 1 L 37,5 %", 1000, Decimal("37.5")),
    ],
)
def test_parse_volume_and_abv(raw, expected_ml, expected_abv):
    p = parse(raw)
    assert p.volume_ml == expected_ml
    assert p.abv == expected_abv


def test_multipack_flagged():
    p = parse("Becherovka 3 x 0,5 l 38%")
    assert p.is_multipack is True


def test_f_norm_diacritics():
    assert f_norm("Jägermeister") == "jagermeister"
    assert f_norm("Božkov") == "bozkov"
    assert f_norm("KOŇAK") == "konak"


def test_clean_name_strips_noise():
    p = parse("Finlandia Vodka 40% 0,7 l dárkové balení")
    assert "0,7" not in p.clean_name
    assert "%" not in p.clean_name
    assert "finlandia" in p.clean_name
    assert "vodka" in p.clean_name


def test_tolerance_on_volume_is_zero():
    # 0,7 l ≠ 0,75 l — both legal spirit sizes.
    assert parse("Vodka 0,7 l").volume_ml == 700
    assert parse("Vodka 0,75 l").volume_ml == 750
