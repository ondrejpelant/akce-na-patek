"""Staging layer.

For a given scrape run:
  1. open_run(conn, store_code, host) -> scrape_run_id
  2. stage_items(conn, scrape_run_id, items)
     - insert every ScrapedItem into stg_listing
     - upsert store_product by (store_id, store_sku) and bump last_seen_at
     - run the matcher cascade for still-unmatched rows
  3. finish_run(conn, scrape_run_id, status=..., items_found=..., ...)

All functions take an open `psycopg.Connection`. Caller controls the transaction.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable

from scraper.matching.matcher import Candidate, match_candidates
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
    """Return (staged_rows, matched_rows).

    Matched_rows = how many previously-unmatched store_products got a product_id
    from this run's matcher pass.
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

    matched = match_unmatched(conn, store_id)
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


def match_unmatched(conn, store_id: int) -> int:
    """Pull every unmatched store_product for this store and run the matcher.
    Returns count of rows that got a product_id this round (fuzzy pending does
    not count; it stays unmatched until a human reviews it).
    """
    with conn.cursor() as cur:
        # The store's own category is not a store_product column; take it from
        # the newest staged payload (stg_listing keeps 14 days). Older items
        # fall back to name keywords.
        cur.execute(
            """
            select sp.id, sp.raw_name, sp.volume_ml, sp.abv, sp.ean, sp.source_kind,
                   s.code,
                   (select st.payload ->> 'source_category'
                    from stg_listing st
                    join scrape_run r on r.id = st.scrape_run_id
                    where r.store_id = sp.store_id and st.store_sku = sp.store_sku
                    order by st.id desc
                    limit 1) as source_category
            from store_product sp
            join store s on s.id = sp.store_id
            where sp.store_id = %s and sp.product_id is null
            for update of sp
            """,
            (store_id,),
        )
        rows = cur.fetchall()

    candidates = [
        Candidate(
            store_product_id=row[0],
            raw_name=row[1],
            volume_ml=row[2],
            abv=float(row[3]) if row[3] is not None else None,
            ean=row[4],
            source_kind=row[5],
            store_code=row[6],
            source_category=row[7],
        )
        for row in rows
    ]
    outcomes = match_candidates(conn, candidates)
    return sum(1 for o in outcomes if o.product_id is not None)


def _resolve_store_id_from_run(conn, scrape_run_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute("select store_id from scrape_run where id = %s", (scrape_run_id,))
        row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Unknown scrape_run_id {scrape_run_id}")
    return row[0]
