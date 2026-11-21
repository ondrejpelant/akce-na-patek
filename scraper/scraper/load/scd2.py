"""SCD2 price merge.

Rules (see 03 Data/Datový model.md):
  - Second run on the same day with identical data MUST NOT create a new row in `price`.
  - leaflet_regular / manual prices are never closed by absence — only overwritten.
  - leaflet (promo, loyalty) prices from an 'ok' run close if today's items don't contain them.
  - catalog items absent in an 'ok' run close (item removed from assortment).
  - partial / failed runs never close any price.

Full implementation lands in M2 together with staging and a dedicated test
(test_scd2.py) covering the "run twice, no diff → 0 new rows" invariant.
"""

from __future__ import annotations


def merge_prices(conn, scrape_run_ids: list[int]) -> int:
    """Merge staged items into `price` with SCD2 semantics.
    Returns the number of newly inserted price rows.
    """
    raise NotImplementedError("M2")
