import pytest

from scraper.matching.matcher import split_brand_name
from scraper.matching.normalize import display_name


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Božkov Originál Tuzemský 0,5l", "Božkov Originál Tuzemský"),
        ("Finlandia Vodka 40% 0,7 l", "Finlandia Vodka"),
        ("Jägermeister 70cl 35 % obj.", "Jägermeister"),
        ("Becherovka 0,5 l dárkové balení", "Becherovka"),
    ],
)
def test_display_name_keeps_case_and_diacritics(raw, expected):
    assert display_name(raw) == expected


@pytest.mark.parametrize(
    "raw,brand,name",
    [
        ("Božkov Originál Tuzemský 0,5l", "Božkov", "Originál Tuzemský"),
        ("Vodka jemná 37,5% Královská palírna", "Královská palírna", "Vodka jemná"),
        ("Tuzemák 37,5% Královská palírna", "Královská palírna", "Tuzemák"),
        ("Tullamore D.E.W. 12 years 0,7l", "Tullamore D.E.W.", "12 years"),
        ("Jameson Irish Whiskey 0,7l", "Jameson", "Irish Whiskey"),
        ("Jagermeister 0,7l", "Jägermeister", ""),
    ],
)
def test_known_brand_uses_canonical_spelling(raw, brand, name):
    assert split_brand_name(raw) == (brand, name)


@pytest.mark.parametrize(
    "raw,category",
    [
        ("Božkov Originál 0,7l", "ostatni"),          # "gin" inside "original"
        ("Beefeater London Dry Gin 0,7l", "gin"),
        ("Božkov Vaječný likér 0,5l", "likery"),
        ("Captain Morgan Spiced Gold 0,7l", "rum"),
    ],
)
def test_category_keyword_must_start_a_word(raw, category):
    from scraper.matching.matcher import _category_for, _load_category_rules

    assert _category_for(raw, _load_category_rules()) == category


def test_unknown_brand_takes_first_two_words():
    assert split_brand_name("Heffron Single Malt 0,7l") == ("Heffron Single", "Malt")
    assert split_brand_name("Heffron 0,7l") == ("Heffron", "")
