"""SCD2 price merge.

Called once per `aktualizuj` run after every source has staged its items.
Operates per (scrape_run, store_product, price_type) key.

Invariants (see 03 Data/Datový model.md):
  * Second run on the same day with identical data MUST NOT insert new price rows.
  * leaflet_regular / manual rows are never closed by absence — only overwritten.
  * leaflet promo/loyalty rows close when today's 'ok' run no longer contains them.
  * catalog rows close when the item is absent in an 'ok' run.
  * partial / failed runs never close any prices.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

log = logging.getLogger(__name__)


def merge_prices(conn, scrape_run_ids: list[int]) -> int:
    """Merge every staged item from the given runs into `price`.

    Returns the number of newly inserted price rows (not counting touched
    observed_at bumps).
    """
    if not scrape_run_ids:
        return 0

    inserted = 0
    with conn.cursor() as cur:
        cur.execute(
            """
            select r.id, r.store_id, r.status
            from scrape_run r
            where r.id = any(%s)
            """,
            (scrape_run_ids,),
        )
        runs = cur.fetchall()
        runs_by_id = {rid: (store_id, status) for rid, store_id, status in runs}

        # 1) For every staged payload in each run, upsert the matching price row.
        for run_id, (store_id, _status) in runs_by_id.items():
            cur.execute(
                """
                select s.payload, sp.id, sp.source_kind
                from stg_listing s
                join store_product sp
                  on sp.store_id = %s and sp.store_sku = s.store_sku
                where s.scrape_run_id = %s and sp.product_id is not null
                """,
                (store_id, run_id),
            )
            rows = cur.fetchall()
            for payload, store_product_id, source_kind in rows:
                item = payload if isinstance(payload, dict) else {}
                inserted += _upsert_price(cur, store_product_id, source_kind, item, run_id)

        # 2) Close prices that today's 'ok' runs no longer contain.
        for run_id, (store_id, status) in runs_by_id.items():
            if status != "ok":
                continue
            _close_missing(cur, store_id=store_id, scrape_run_id=run_id)

    return inserted


# ---------------------------------------------------------------------------


def _upsert_price(
    cur,
    store_product_id: int,
    source_kind: str,
    item: dict[str, Any],
    scrape_run_id: int,
) -> int:
    """Insert, update, or just touch a price row for one staged item.

    Returns 1 if a new row was inserted, 0 otherwise.
    """
    price_type = item.get("price_type")
    if price_type is None:
        return 0

    price_czk = _dec(item.get("price_czk"))
    if price_czk is None or price_czk <= 0:
        return 0
    regular_czk = _dec(item.get("regular_czk"))
    promo_from = item.get("promo_from")
    promo_to = item.get("promo_to")
    price_source = _price_source(source_kind, price_type, regular_czk, item)

    # Current row for this (store_product, price_type), if any.
    cur.execute(
        """
        select id, price_czk, regular_czk, promo_from, promo_to
        from price
        where store_product_id = %s and price_type = %s and valid_to = 'infinity'
        """,
        (store_product_id, price_type),
    )
    current = cur.fetchone()

    if current is None:
        cur.execute(
            """
            insert into price (
                store_product_id, price_type, price_czk, regular_czk,
                promo_from, promo_to, price_source, scrape_run_id
            ) values (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                store_product_id,
                price_type,
                price_czk,
                regular_czk,
                promo_from,
                promo_to,
                price_source,
                scrape_run_id,
            ),
        )
        return 1

    cur_id, cur_price, cur_regular, cur_from, cur_to = current
    unchanged = (
        _dec(cur_price) == price_czk
        and _dec(cur_regular) == regular_czk
        and _as_date(cur_from) == _as_date(promo_from)
        and _as_date(cur_to) == _as_date(promo_to)
    )
    if unchanged:
        cur.execute(
            "update price set observed_at = now(), scrape_run_id = %s where id = %s",
            (scrape_run_id, cur_id),
        )
        return 0

    # Change: close the current row and open a new one.
    cur.execute("update price set valid_to = now() where id = %s", (cur_id,))
    cur.execute(
        """
        insert into price (
            store_product_id, price_type, price_czk, regular_czk,
            promo_from, promo_to, price_source, scrape_run_id
        ) values (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            store_product_id,
            price_type,
            price_czk,
            regular_czk,
            promo_from,
            promo_to,
            price_source,
            scrape_run_id,
        ),
    )
    return 1


def _close_missing(cur, *, store_id: int, scrape_run_id: int) -> None:
    """Close prices this store carries that today's run did not re-observe.

    Only touches catalog and leaflet promo/loyalty rows.
    leaflet_regular and manual rows are never closed by absence.
    """
    cur.execute(
        """
        with observed as (
            select sp.id as store_product_id, p.price_type
            from stg_listing s
            join store_product sp
              on sp.store_id = %s and sp.store_sku = s.store_sku
            cross join lateral (
                select (s.payload ->> 'price_type')::text as price_type
            ) p
            where s.scrape_run_id = %s
        )
        update price set valid_to = now()
        where valid_to = 'infinity'
          and price_source in ('catalog', 'leaflet')
          and store_product_id in (select id from store_product where store_id = %s)
          and (store_product_id, price_type) not in (select store_product_id, price_type from observed)
        """,
        (store_id, scrape_run_id, store_id),
    )


def _price_source(source_kind: str, price_type: str, regular_czk, item: dict) -> str:
    """Map the (source_kind, price_type) to one of catalog|leaflet|leaflet_regular|manual."""
    # Hard override (used by `add-price`).
    override = item.get("price_source")
    if override in {"catalog", "leaflet", "leaflet_regular", "manual"}:
        return override
    if source_kind == "catalog":
        return "catalog"
    # leaflet source: regular rows that come from the strikethrough "price before discount"
    # feed the leaflet_regular lane; promo/loyalty stays as leaflet.
    if price_type == "regular":
        return "leaflet_regular"
    return "leaflet"


def _dec(v) -> Decimal | None:
    if v is None:
        return None
    if isinstance(v, Decimal):
        return v
    try:
        return Decimal(str(v))
    except Exception:
        return None


def _as_date(v):
    """Compare dates uniformly: str, date or None."""
    if v is None:
        return None
    s = str(v)
    return s[:10]  # trim timestamps to YYYY-MM-DD; dates stay as-is
