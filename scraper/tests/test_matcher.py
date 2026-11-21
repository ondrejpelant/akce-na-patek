"""Matcher-cascade tests driven by fixtures/matching_cases.csv.

The CSV encodes real-world raw_name pairs that should (or must not) collapse
into a single `product`. A green suite means the normaliser + brand detector +
fuzzy scorer agree with the editorial judgement in the CSV. When a scraper
change breaks this, the test names the specific pair.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scraper.matching import matcher
from scraper.matching.normalize import f_norm
from scraper.matching.normalize import parse as parse_name

AUTO_FUZZY = matcher.AUTO_FUZZY  # 90.0
FIXTURE = Path(__file__).parent / "fixtures" / "matching_cases.csv"


def _load_cases() -> list[tuple[str, str, bool, str]]:
    with FIXTURE.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return [
            (row["name_a"], row["name_b"], row["should_match"].strip().upper() == "TRUE",
             row.get("note", ""))
            for row in reader
        ]


def _would_match(name_a: str, name_b: str) -> bool:
    """Does the cascade's "auto" lane (exact or fuzzy ≥ AUTO_FUZZY) fire?

    Mirrors the logic inside matcher._match_one for pairs of raw names:
      - volumes must match exactly (0.7 l ≠ 0.75 l);
      - when both names land on a known brand, the brands must agree;
      - the per-brand remainder goes through match_norm + token_set_ratio.
    """
    brands = matcher._load_brands()
    pa = parse_name(name_a)
    pb = parse_name(name_b)

    if pa.volume_ml != pb.volume_ml:
        return False

    detected_a = matcher._detect_brand(pa.clean_name, brands)
    detected_b = matcher._detect_brand(pb.clean_name, brands)
    if detected_a and detected_b and f_norm(detected_a) != f_norm(detected_b):
        return False

    brand_a = detected_a or matcher._fallback_brand(pa.clean_name)
    brand_b = detected_b or matcher._fallback_brand(pb.clean_name)
    if not detected_a and not detected_b and f_norm(brand_a) != f_norm(brand_b):
        return False

    norm_a = matcher.match_norm(matcher._strip_brand(pa.clean_name, brand_a, brands))
    norm_b = matcher.match_norm(matcher._strip_brand(pb.clean_name, brand_b, brands))
    return matcher.name_score(norm_a, norm_b) >= AUTO_FUZZY


# Driver -------------------------------------------------------------------


CASES = _load_cases()

# Same bottle, but the strict auto-merge leaves it apart (it goes to `review`).
# strict xfail: if one starts matching, the test says so and it can be removed.
KNOWN_MISSES = {
    ("Smirnoff Red Label 1l", "Smirnoff Red No. 21 1l"),
}


def _param(a, b, should_match, note):
    marks = (
        [pytest.mark.xfail(strict=True, reason="strict auto-merge; resolved via review")]
        if (a, b) in KNOWN_MISSES else []
    )
    return pytest.param(a, b, should_match, note, marks=marks, id=f"{a[:20]}__vs__{b[:20]}")


@pytest.mark.parametrize("name_a,name_b,should_match,note", [_param(*c) for c in CASES])
def test_pair(name_a: str, name_b: str, should_match: bool, note: str):
    got = _would_match(name_a, name_b)
    if got != should_match:
        pytest.fail(
            f"\n  A: {name_a!r}\n  B: {name_b!r}\n"
            f"  expected {'MATCH' if should_match else 'NO MATCH'} ({note}),"
            f" got {'MATCH' if got else 'NO MATCH'}",
        )


def test_different_known_categories_never_merge():
    # "Božkov Vodka 0,7l" vs "Božkov Originál 0,7l": both names are empty after
    # stopwords, only the category (vodka vs rum) tells them apart.
    vodka, rum, ostatni = 2, 1, 10
    assert not matcher.categories_compatible(vodka, rum, ostatni)
    assert matcher.categories_compatible(vodka, vodka, ostatni)
    assert matcher.categories_compatible(vodka, ostatni, ostatni)
    assert matcher.categories_compatible(None, rum, ostatni)


def test_overall_accuracy():
    """Soft gate: at least 85 % of cases must be classified correctly.
    Lets individual regressions surface via test_pair while a broad drift still
    fails loudly.
    """
    correct = sum(1 for a, b, expected, _ in CASES if _would_match(a, b) == expected)
    accuracy = correct / len(CASES)
    assert accuracy >= 0.85, (
        f"matcher accuracy {accuracy:.1%} dropped below the 85 % AK (M5)"
    )
