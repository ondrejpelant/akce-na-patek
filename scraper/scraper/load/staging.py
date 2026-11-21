"""Staging layer.

For a given scrape run:
  1. open_run(conn, store_code, host) -> scrape_run_id
  2. stage_items(conn, scrape_run_id, items)
     - insert every ScrapedItem into stg_listing (both raw + validated payload)
     - upsert store_product by (store_id, store_sku) and bump last_seen_at
     - auto-create products for still-unmatched store_products
       (M2 "one source = every item is a new product")
  3. finish_run(conn, scrape_run_id, status=..., items_found=..., ...)

All functions take an open `psycopg.Connection`. Caller controls the transaction.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from collections.abc import Iterable

from scraper.matching.normalize import f_norm
from scraper.matching.normalize import parse as normalize_name
from scraper.models import ScrapedItem

log = logging.getLogger(__name__)


def open_run(conn, store_code: str, host: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into scrape_run (store_id, host, status)
            select id, %s, 'running' from store where code = %s
            returning id
            """,
            (host, store_code),
        )
        row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Unknown store code: {store_code}. Seed data missing?")
    return row[0]


def stage_items(conn, scrape_run_id: int, items: Iterable[ScrapedItem]) -> tuple[int, int]:
    """Return (staged_rows, upserted_store_products).

    Store_products with product_id IS NULL after this call are auto-matched
    (M2: one source -> one product per unique (brand, name, volume_ml)).
    """
    staged = 0
    touched_sku: set[tuple[int, str]] = set()
    store_id = _resolve_store_id_from_run(conn, scrape_run_id)

    with conn.cursor() as cur:
        for item in items:
            cur.execute(
                """
                insert into stg_listing (scrape_run_id, store_sku, payload, raw)
                values (%s, %s, %s::jsonb, %s::jsonb)
                """,
                (
                    scrape_run_id,
                    item.store_sku,
                    item.model_dump_json(),
                    json.dumps(item.raw, ensure_ascii=False),
                ),
            )
            staged += 1

            if (store_id, item.store_sku) in touched_sku:
                # Same sku already upserted in this run (common: promo + regular rows
                # share a store_sku). last_seen_at was bumped the first time.
                continue
            touched_sku.add((store_id, item.store_sku))

            cur.execute(
                """
                insert into store_product (
                    store_id, store_sku, raw_name, volume_ml, abv, ean,
                    url, image_url, source_kind, last_seen_at
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                on conflict (store_id, store_sku) do update set
                    raw_name     = excluded.raw_name,
                    volume_ml    = coalesce(excluded.volume_ml, store_product.volume_ml),
                    abv          = coalesce(excluded.abv,       store_product.abv),
                    ean          = coalesce(excluded.ean,       store_product.ean),
                    url          = coalesce(excluded.url,       store_product.url),
                    image_url    = coalesce(excluded.image_url, store_product.image_url),
                    source_kind  = excluded.source_kind,
                    last_seen_at = now()
                """,
                (
                    store_id,
                    item.store_sku,
                    item.raw_name,
                    item.volume_ml,
                    item.abv,
                    item.ean,
                    item.url,
                    item.image_url,
                    item.source_kind,
                ),
            )

    matched = _automatch_unmatched(conn, store_id)
    return staged, matched


def finish_run(
    conn,
    scrape_run_id: int,
    *,
    status: str,
    items_found: int,
    items_changed: int | None = None,
    error: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            update scrape_run set
                status = %s,
                items_found = %s,
                items_changed = %s,
                error = %s,
                finished_at = now()
            where id = %s
            """,
            (status, items_found, items_changed, error, scrape_run_id),
        )


# ---------------------------------------------------------------------------
# M2 auto-matching: "one source = every item is a new product"
# ---------------------------------------------------------------------------

_DEFAULT_CATEGORY_SLUG = "ostatni"


def _resolve_store_id_from_run(conn, scrape_run_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute("select store_id from scrape_run where id = %s", (scrape_run_id,))
        row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Unknown scrape_run_id {scrape_run_id}")
    return row[0]


def _automatch_unmatched(conn, store_id: int) -> int:
    """For every unmatched store_product of this store, create (or find) a product
    keyed on (brand, name, volume_ml) and link them. Returns number matched.
    """
    rules = _load_category_rules()
    category_by_slug = _category_id_by_slug(conn)
    default_cat = category_by_slug.get(_DEFAULT_CATEGORY_SLUG) or next(iter(category_by_slug.values()))

    matched = 0
    with conn.cursor() as cur:
        cur.execute(
            """
            select id, raw_name, volume_ml, abv
            from store_product
            where store_id = %s and product_id is null
            for update
            """,
            (store_id,),
        )
        rows = cur.fetchall()

        for sp_id, raw_name, volume_ml, abv in rows:
            parsed = normalize_name(raw_name)
            volume = volume_ml or parsed.volume_ml
            if volume is None or parsed.is_multipack:
                continue  # unmatched; leaves it for manual review

            brand = _detect_brand(parsed.clean_name) or _fallback_brand(parsed.clean_name)
            name = _strip_brand(parsed.clean_name, brand)
            if not name:
                name = parsed.clean_name

            category_id = category_by_slug.get(_category_for(raw_name, rules), default_cat)
            product_id = _get_or_create_product(
                cur,
                category_id=category_id,
                brand=brand,
                name=name,
                volume_ml=volume,
                abv=abv or parsed.abv,
            )
            cur.execute(
                "update store_product set product_id = %s where id = %s",
                (product_id, sp_id),
            )
            matched += 1
    return matched


def _get_or_create_product(cur, *, category_id, brand, name, volume_ml, abv) -> int:
    cur.execute(
        "select id from product where brand = %s and name = %s and volume_ml = %s",
        (brand, name, volume_ml),
    )
    row = cur.fetchone()
    if row:
        return row[0]
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


# --- helpers ---------------------------------------------------------------

_BRAND_CACHE: list[tuple[str, list[str]]] | None = None


def _load_brands() -> list[tuple[str, list[str]]]:
    """Return [(canonical_brand, [alias1, alias2, ...])] with normalized aliases.
    The canonical display form stays as-is (preserves diacritics)."""
    global _BRAND_CACHE
    if _BRAND_CACHE is not None:
        return _BRAND_CACHE
    from pathlib import Path

    import yaml  # local import keeps module importable without yaml at test time

    from scraper.matching import __file__ as matching_init

    path = Path(matching_init).parent / "brands.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    out: list[tuple[str, list[str]]] = []
    for entry in data:
        name = entry["name"]
        aliases = {f_norm(name)}
        for alias in entry.get("aliases", []) or []:
            aliases.add(f_norm(alias))
        # Longest aliases first so "Captain Morgan Spiced Gold" beats "Captain Morgan".
        out.append((name, sorted(aliases, key=len, reverse=True)))
    # Longer canonical names first too, for the same reason.
    out.sort(key=lambda t: len(f_norm(t[0])), reverse=True)
    _BRAND_CACHE = out
    return out


def _detect_brand(clean_name: str) -> str | None:
    for canonical, aliases in _load_brands():
        for alias in aliases:
            if _contains_token(clean_name, alias):
                return canonical
    return None


def _fallback_brand(clean_name: str) -> str:
    # Last-resort: use the first two words of the normalized name, title-cased.
    parts = [w for w in re.split(r"\s+", clean_name) if w]
    head = " ".join(parts[:2]) if parts else "Neznámá"
    return head.title()


def _strip_brand(clean_name: str, brand: str) -> str:
    brand_norm = f_norm(brand)
    out = re.sub(rf"\b{re.escape(brand_norm)}\b", " ", clean_name)
    for alias in _aliases_of(brand):
        out = re.sub(rf"\b{re.escape(alias)}\b", " ", out)
    out = re.sub(r"\s+", " ", out).strip(" -,.()")
    return out


def _aliases_of(brand: str) -> list[str]:
    for canonical, aliases in _load_brands():
        if canonical == brand:
            return aliases
    return [f_norm(brand)]


def _contains_token(haystack: str, needle: str) -> bool:
    return bool(re.search(rf"(?<![\w]){re.escape(needle)}(?![\w])", haystack))


_CATEGORY_RULES_CACHE: list[tuple[str, list[str]]] | None = None


def _load_category_rules() -> list[tuple[str, list[str]]]:
    global _CATEGORY_RULES_CACHE
    if _CATEGORY_RULES_CACHE is not None:
        return _CATEGORY_RULES_CACHE
    from pathlib import Path

    import yaml

    from scraper.matching import __file__ as matching_init

    path = Path(matching_init).parent / "category_rules.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    _CATEGORY_RULES_CACHE = [(e["category"], [f_norm(k) for k in e["keywords"]]) for e in data]
    return _CATEGORY_RULES_CACHE


def _category_for(raw_name: str, rules: list[tuple[str, list[str]]]) -> str:
    text = f_norm(raw_name)
    for slug, keywords in rules:
        for kw in keywords:
            if kw in text:
                return slug
    return _DEFAULT_CATEGORY_SLUG


def _category_id_by_slug(conn) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute("select slug, id from category")
        return dict(cur.fetchall())


def _slugify(text: str) -> str:
    base = unicodedata.normalize("NFD", text)
    base = "".join(c for c in base if unicodedata.category(c) != "Mn")
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower()
    return base or "produkt"
