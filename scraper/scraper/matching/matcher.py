"""Produkt matching: `store_product` → `product`.

Cascade (see 03 Data/Párování produktů.md):
  1. EAN             → auto-accept            (exact EAN match on `product`)
  2. exact_norm      → auto-accept            (same brand + same normalised name + same volume)
  3. fuzzy >= 90     → auto-accept            (same brand, same volume, token_set_ratio >= 90)
  4. fuzzy 75-90     → match_candidate pending (same volume, score in [75, 90))
  5. no match        → new `product`          (one row per unique (brand, name, volume))

Volume MUST equal exactly (0,7 l ≠ 0,75 l). Multipacks are skipped entirely.

The module is intentionally small and stateless — all SQL happens through a
provided `psycopg` cursor. Callers own the transaction.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from rapidfuzz import fuzz

from scraper.matching.normalize import display_name, f_norm
from scraper.matching.normalize import parse as parse_name

log = logging.getLogger(__name__)

AUTO_FUZZY = 90.0
PENDING_FUZZY = 75.0
DEFAULT_CATEGORY_SLUG = "ostatni"

# Words that describe the drink type rather than a distinguishing variant.
# Dropped during normalisation so "Jameson Irish Whiskey 0.7l" and
# "Jameson 0.7l" compare as one product.
_DESCRIPTOR_STOPWORDS = frozenset({
    "vodka", "rum", "gin", "whisky", "whiskey", "tequila", "brandy", "cognac",
    "konak", "liker", "likery", "liqueur", "pivo", "cream",
    "irish", "scotch", "london", "dry",
    "original", "label", "finest", "premium", "special",
    "years", "year", "let", "roky", "roku", "ans", "anos",
    "hvezd", "hvezda", "hvezdy", "hviezd",
})

# Punctuation-folding — "*", "+", dots inside abbreviations etc.
_PUNCT_RE = re.compile(r"[.,;:!?/\\\"'`*+()\[\]{}]")

# Short abbreviation expansions. Keep tight: VSOP stays distinct from VS.
_ABBREV_EXPANSIONS = {
    "vs": "very special",
    "xo": "extra old",
}

_HERE = Path(__file__).parent
_BRANDS_PATH = _HERE / "brands.yaml"
_CATEGORY_RULES_PATH = _HERE / "category_rules.yaml"
_SOURCE_CATEGORIES_PATH = _HERE / "source_categories.yaml"


# ---------------------------------------------------------------------------
# Parsed representation of a store_product row that the matcher works with
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Candidate:
    """A single store_product awaiting a `product_id`."""

    store_product_id: int
    raw_name: str
    volume_ml: int | None
    abv: float | None
    ean: str | None
    source_kind: str  # 'catalog' | 'leaflet'
    store_code: str | None = None
    source_category: str | None = None  # store's own category path, if any


@dataclass
class MatchOutcome:
    store_product_id: int
    product_id: int | None  # None when we created a pending match_candidate only
    method: str              # 'ean' | 'exact_norm' | 'fuzzy' | 'new' | 'pending' | 'skip'
    score: float | None = None
    reason: str | None = None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def match_candidates(conn, candidates: list[Candidate]) -> list[MatchOutcome]:
    """Run the full cascade for every candidate and apply DB writes.

    Returns one outcome per candidate (same order).
    """
    outcomes: list[MatchOutcome] = []
    brands = _load_brands()
    rules = _load_category_rules()
    cat_by_slug = _category_id_by_slug(conn)
    default_cat = cat_by_slug.get(DEFAULT_CATEGORY_SLUG) or next(iter(cat_by_slug.values()))

    with conn.cursor() as cur:
        for c in candidates:
            outcomes.append(_match_one(cur, c, brands=brands, rules=rules,
                                       cat_by_slug=cat_by_slug, default_cat=default_cat))
    return outcomes


# ---------------------------------------------------------------------------
# The cascade
# ---------------------------------------------------------------------------


def _match_one(
    cur,
    c: Candidate,
    *,
    brands: list[tuple[str, list[str]]],
    rules: list[tuple[str, list[str]]],
    cat_by_slug: dict[str, int],
    default_cat: int,
) -> MatchOutcome:
    parsed = parse_name(c.raw_name)
    volume = c.volume_ml or parsed.volume_ml
    if volume is None or parsed.is_multipack:
        return MatchOutcome(c.store_product_id, None, "skip",
                            reason="no volume" if volume is None else "multipack")

    brand, name = split_brand_name(c.raw_name, brands)

    # 1) EAN
    if c.ean:
        pid = _find_by_ean(cur, c.ean)
        if pid:
            _link(cur, c.store_product_id, pid, method="ean", score=100.0)
            return MatchOutcome(c.store_product_id, pid, "ean", 100.0)

    # 2 + 3) Same brand + same volume -> pull all candidates and score them.
    norm_new = match_norm(name)
    for pid, _candidate_name, score in _score_candidates(cur, brand=brand, name=norm_new,
                                                       volume_ml=volume):
        if score >= 100:
            _link(cur, c.store_product_id, pid, method="exact_norm", score=100.0)
            return MatchOutcome(c.store_product_id, pid, "exact_norm", 100.0)
        if score >= AUTO_FUZZY:
            _link(cur, c.store_product_id, pid, method="fuzzy", score=score)
            return MatchOutcome(c.store_product_id, pid, "fuzzy", score)
        if score >= PENDING_FUZZY:
            _stage_pending(cur, c.store_product_id, pid, score)
            return MatchOutcome(c.store_product_id, None, "pending", score)
        break  # candidates are sorted descending; nothing better can follow

    # 5) no match → new product
    slug = resolve_category(c.raw_name, c.store_code, c.source_category, rules=rules)
    category_id = cat_by_slug.get(slug, default_cat)
    pid = _create_product(cur, category_id=category_id, brand=brand, name=name,
                          volume_ml=volume, abv=c.abv or parsed.abv)
    _link_only(cur, c.store_product_id, pid)
    return MatchOutcome(c.store_product_id, pid, "new")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _find_by_ean(cur, ean: str) -> int | None:
    cur.execute("select id from product where ean = %s limit 1", (ean,))
    row = cur.fetchone()
    return row[0] if row else None


def _score_candidates(
    cur, *, brand: str, name: str, volume_ml: int
) -> list[tuple[int, str, float]]:
    """Fetch every product that shares brand + volume and score it against
    `name` (which must already be match_norm-normalised). Returns rows sorted
    descending by score so callers can early-exit."""
    cur.execute(
        """
        select id, name from product
        where f_norm(brand) = f_norm(%s) and volume_ml = %s
        """,
        (brand, volume_ml),
    )
    rows: list[tuple[int, str]] = cur.fetchall()
    scored: list[tuple[int, str, float]] = []
    for pid, candidate_name in rows:
        other = match_norm(candidate_name)
        # rapidfuzz scores two empty strings 0; for us "brand only" == "brand only".
        score = 100.0 if not name and not other else float(fuzz.token_set_ratio(name, other))
        scored.append((pid, candidate_name, score))
    scored.sort(key=lambda t: t[2], reverse=True)
    return scored


def _create_product(cur, *, category_id: int, brand: str, name: str,
                    volume_ml: int, abv: Any) -> int:
    slug = _slugify(f"{brand} {name} {volume_ml}ml")
    cur.execute(
        """
        insert into product (category_id, brand, name, volume_ml, abv, slug)
        values (%s, %s, %s, %s, %s, %s)
        on conflict (slug) do update set slug = excluded.slug
        returning id
        """,
        (category_id, brand, name, volume_ml, abv, slug),
    )
    return cur.fetchone()[0]


def _link(cur, store_product_id: int, product_id: int, *, method: str, score: float) -> None:
    _link_only(cur, store_product_id, product_id)
    cur.execute(
        """
        insert into match_candidate (store_product_id, product_id, score, method, status)
        values (%s, %s, %s, %s, 'accepted')
        on conflict (store_product_id, product_id) do update set
            score = excluded.score,
            method = excluded.method,
            status = 'accepted'
        """,
        (store_product_id, product_id, score, method),
    )


def _link_only(cur, store_product_id: int, product_id: int) -> None:
    cur.execute(
        "update store_product set product_id = %s where id = %s",
        (product_id, store_product_id),
    )


def _stage_pending(cur, store_product_id: int, product_id: int, score: float) -> None:
    cur.execute(
        """
        insert into match_candidate (store_product_id, product_id, score, method, status)
        values (%s, %s, %s, 'fuzzy', 'pending')
        on conflict (store_product_id, product_id) do update set
            score = excluded.score,
            status = case when match_candidate.status = 'rejected'
                          then 'rejected' else 'pending' end
        """,
        (store_product_id, product_id, score),
    )


def _category_id_by_slug(conn) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute("select slug, id from category")
        return dict(cur.fetchall())


# ---------------------------------------------------------------------------
# Brand / category lookup
# ---------------------------------------------------------------------------


_brands_cache: list[tuple[str, list[str]]] | None = None
_rules_cache: list[tuple[str, list[str]]] | None = None


def _load_brands() -> list[tuple[str, list[str]]]:
    global _brands_cache
    if _brands_cache is not None:
        return _brands_cache
    data = yaml.safe_load(_BRANDS_PATH.read_text(encoding="utf-8")) or []
    entries: list[tuple[str, list[str]]] = []
    for item in data:
        canonical = item["name"]
        aliases_set: set[str] = {_norm_alias(canonical)}
        for a in item.get("aliases", []) or []:
            aliases_set.add(_norm_alias(a))
        entries.append((canonical, sorted(aliases_set, key=len, reverse=True)))
    # Longer canonical names first so "Captain Morgan Spiced Gold" beats "Captain Morgan".
    entries.sort(key=lambda t: len(_norm_alias(t[0])), reverse=True)
    _brands_cache = entries
    return entries


def _norm_alias(text: str) -> str:
    """Normalise a brand or alias for comparison: f_norm + punctuation → space."""
    s = _PUNCT_RE.sub(" ", f_norm(text))
    return re.sub(r"\s+", " ", s).strip()


def _load_category_rules() -> list[tuple[str, list[str]]]:
    global _rules_cache
    if _rules_cache is not None:
        return _rules_cache
    data = yaml.safe_load(_CATEGORY_RULES_PATH.read_text(encoding="utf-8")) or []
    _rules_cache = [(e["category"], [f_norm(k) for k in e["keywords"]]) for e in data]
    return _rules_cache


def _detect_brand(clean_name: str, brands: list[tuple[str, list[str]]]) -> str | None:
    # Strip punctuation so aliases like "tullamore dew" match "tullamore d.e.w."
    haystack = _PUNCT_RE.sub(" ", clean_name)
    haystack = re.sub(r"\s+", " ", haystack)
    for canonical, aliases in brands:
        for alias in aliases:
            if _contains_token(haystack, alias):
                return canonical
    return None


def split_brand_name(
    raw_name: str, brands: list[tuple[str, list[str]]] | None = None
) -> tuple[str, str]:
    """Split a raw store name into (brand, name) for storage on `product`.

    Both keep the original casing and diacritics; matching always compares
    them through match_norm(), so display form does not affect scoring.
    Known brand -> its canonical spelling from brands.yaml, removed from the
    name wherever it appears ("Vodka jemná 37,5% Královská palírna" ->
    ("Královská palírna", "Vodka jemná")). Unknown brand -> the first two
    words of the name.
    """
    brands = brands if brands is not None else _load_brands()
    display = display_name(raw_name)
    detected = _detect_brand(f_norm(display), brands)
    tokens = display.split()
    # The name may end up empty ("Jägermeister 0,7l") — the web renders
    # "{brand} {name}", so repeating the brand there would show it twice.
    if detected:
        rest = _remove_alias_tokens(tokens, _aliases_of(detected, brands))
        return detected, " ".join(rest).strip(" -,.()")
    brand = " ".join(tokens[:2]) or "Neznámá"
    return brand, " ".join(tokens[2:]).strip(" -,.()")


def _remove_alias_tokens(tokens: list[str], aliases: list[str]) -> list[str]:
    """Drop the first token span whose normalised form equals one of the
    aliases (longest alias first). Works on display tokens, so "D.E.W." and
    "Božkov" are matched diacritic- and punctuation-insensitively."""
    for alias in aliases:
        for i in range(len(tokens)):
            for j in range(i + 1, len(tokens) + 1):
                joined = _norm_alias(" ".join(tokens[i:j]))
                if joined == alias:
                    return tokens[:i] + tokens[j:]
                if len(joined) > len(alias):
                    break
    return tokens


def _fallback_brand(clean_name: str) -> str:
    parts = [w for w in re.split(r"\s+", clean_name) if w]
    head = " ".join(parts[:2]) if parts else "Neznámá"
    return head.title()


def _strip_brand(clean_name: str, brand: str, brands: list[tuple[str, list[str]]]) -> str:
    # Normalise punctuation in the input so aliases like "tullamore d e w" match
    # "tullamore d.e.w." in the raw name.
    text = _PUNCT_RE.sub(" ", clean_name)
    text = re.sub(r"\s+", " ", text)
    for alias in _aliases_of(brand, brands):
        text = re.sub(rf"(?<!\w){re.escape(alias)}(?!\w)", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -,.()")
    return text


def _aliases_of(brand: str, brands: list[tuple[str, list[str]]]) -> list[str]:
    for canonical, aliases in brands:
        if canonical == brand:
            return aliases
    return [f_norm(brand)]


def _contains_token(haystack: str, needle: str) -> bool:
    return bool(re.search(rf"(?<![\w]){re.escape(needle)}(?![\w])", haystack))


def resolve_category(
    raw_name: str,
    store_code: str | None,
    source_category: str | None,
    *,
    rules: list[tuple[str, list[str]]] | None = None,
) -> str:
    """Name keywords first (editorial), then the store's own category tree,
    then the default."""
    slug = _category_for(raw_name, rules if rules is not None else _load_category_rules())
    if slug != DEFAULT_CATEGORY_SLUG:
        return slug
    return _category_from_source(store_code, source_category) or DEFAULT_CATEGORY_SLUG


def _category_from_source(store_code: str | None, path: str | None) -> str | None:
    """Longest whole-segment prefix of `path` found in source_categories.yaml."""
    if not store_code or not path:
        return None
    mapping = _load_source_categories().get(store_code, {})
    segments = path.strip("/").split("/")
    for n in range(len(segments), 0, -1):
        slug = mapping.get("/".join(segments[:n]))
        if slug:
            return slug
    return None


_source_cats_cache: dict[str, dict[str, str]] | None = None


def _load_source_categories() -> dict[str, dict[str, str]]:
    global _source_cats_cache
    if _source_cats_cache is None:
        data = yaml.safe_load(_SOURCE_CATEGORIES_PATH.read_text(encoding="utf-8")) or {}
        _source_cats_cache = {store: dict(m or {}) for store, m in data.items()}
    return _source_cats_cache


def _category_for(raw_name: str, rules: list[tuple[str, list[str]]]) -> str:
    text = f_norm(raw_name)
    for slug, keywords in rules:
        for kw in keywords:
            # Keyword must start a word ("gin" must not hit "original"), but may
            # continue ("liker" matches "likerem", "rum" matches "rumovy").
            if re.search(rf"(?<!\w){re.escape(kw)}", text):
                return slug
    return DEFAULT_CATEGORY_SLUG


def match_norm(text: str) -> str:
    """Stronger normalisation used only during product matching.

    f_norm (lower + unaccent) PLUS:
      - punctuation collapsed to space,
      - descriptor stopwords (vodka/whiskey/original/label …) dropped,
      - short abbreviations expanded (VS → "very special"),
    then tokens re-joined. Multi-word values stay as single strings so that
    `fuzz.token_set_ratio` treats them per-token.
    """
    base = _PUNCT_RE.sub(" ", f_norm(text))
    tokens = [t for t in base.split() if t]
    out: list[str] = []
    for tok in tokens:
        if tok in _DESCRIPTOR_STOPWORDS:
            continue
        out.extend((_ABBREV_EXPANSIONS.get(tok) or tok).split())
    return " ".join(out)


def _slugify(text: str) -> str:
    base = unicodedata.normalize("NFD", text)
    base = "".join(c for c in base if unicodedata.category(c) != "Mn")
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower()
    return base or "produkt"


# Testing hook — keep private tests from bleeding global state.
def _clear_cache_for_tests() -> None:
    global _brands_cache, _rules_cache, _source_cats_cache
    _brands_cache = None
    _rules_cache = None
    _source_cats_cache = None
