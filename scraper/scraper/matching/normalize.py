"""Parse brand, volume and ABV out of a messy product name.

Design notes (see 03 Data/Párování produktů.md):
  - Volume MUST be known to match products. 0,7 l ≠ 0,75 l (no tolerance).
  - Brand comes from a hand-maintained list (brands.yaml, loaded elsewhere).
  - This module is intentionally stateless and pure — easy to unit-test.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal

_VOLUME_RE = re.compile(
    r"""
    (?<![\d,\.])              # not glued to another digit
    (?P<num>\d+(?:[,\.]\d+)?) # 0,7 / 1.0 / 700
    \s*
    (?P<unit>ml|cl|dl|l)\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Multipack hint, e.g. "3 x 0,5 l". Treated as unmatchable for MVP (we flag it).
# Czech product names sometimes use the Unicode multiplication sign — allow both.
_MULTIPACK_RE = re.compile(r"\b(\d+)\s*[x×]\s*\d", re.IGNORECASE)  # noqa: RUF001

_ABV_RE = re.compile(
    r"(?P<num>\d{1,2}(?:[,\.]\d+)?)\s*%(?:\s*(?:obj\.?|alc\.?|alk\.?|vol\.?))?",
    re.IGNORECASE,
)

_NOISE_WORDS = (
    "lahev",
    "darkove baleni",
    "dárkové balení",
    "+ sklenicky",
    "+ 2 sklenicky",
    "+ 2 skleničky",
    "+ sklenice",
    "+ 2 sklenice",
)


@dataclass(frozen=True)
class Parsed:
    volume_ml: int | None
    abv: Decimal | None
    is_multipack: bool
    clean_name: str  # lowercased, diacritics stripped, without volume/abv/noise


def strip_diacritics(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def f_norm(s: str) -> str:
    """Python equivalent of SQL f_norm(): lower + unaccent."""
    return strip_diacritics(s or "").lower()


def _to_ml(num: str, unit: str) -> int:
    value = Decimal(num.replace(",", "."))
    unit = unit.lower()
    factor = {"ml": Decimal(1), "cl": Decimal(10), "dl": Decimal(100), "l": Decimal(1000)}[unit]
    return int(value * factor)


def parse(raw_name: str) -> Parsed:
    name = f_norm(raw_name)
    is_multipack = bool(_MULTIPACK_RE.search(name))

    volume_ml: int | None = None
    # Prefer the last volume match (e.g. "Finlandia 40 % 0,7 l" → 700).
    for m in _VOLUME_RE.finditer(name):
        volume_ml = _to_ml(m.group("num"), m.group("unit"))

    abv: Decimal | None = None
    m = _ABV_RE.search(name)
    if m:
        try:
            abv = Decimal(m.group("num").replace(",", "."))
            if not (Decimal("0") <= abv <= Decimal("100")):
                abv = None
        except Exception:
            abv = None

    clean = _VOLUME_RE.sub(" ", name)
    clean = _ABV_RE.sub(" ", clean)
    clean = _MULTIPACK_RE.sub(" ", clean)
    for w in _NOISE_WORDS:
        clean = clean.replace(w, " ")
    clean = re.sub(r"\s+", " ", clean).strip(" -,.()[]")

    return Parsed(volume_ml=volume_ml, abv=abv, is_multipack=is_multipack, clean_name=clean)


def display_name(raw_name: str) -> str:
    """Same removals as parse().clean_name (volume, ABV, multipack, noise) but
    keeps the original casing and diacritics — this is what the web shows."""
    s = _VOLUME_RE.sub(" ", raw_name)
    s = _ABV_RE.sub(" ", s)
    s = _MULTIPACK_RE.sub(" ", s)
    for w in _NOISE_WORDS:
        s = re.sub(re.escape(w), " ", s, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s).strip(" -,.()[]")
