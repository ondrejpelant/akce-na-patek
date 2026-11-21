"""Staging: open a scrape_run, insert validated ScrapedItems into stg_listing,
upsert store_product, finalise the run.

Implemented in M2 (first end-to-end source). Function signatures below are the
stable contract the CLI depends on.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from scraper.models import ScrapedItem


@dataclass
class RunResult:
    scrape_run_id: int
    items_found: int
    status: str  # 'ok' | 'partial' | 'failed'


def open_run(conn, store_code: str, host: str) -> int:
    """Insert a scrape_run row with status='running', return its id."""
    raise NotImplementedError("M2")


def stage_items(conn, scrape_run_id: int, items: Iterable[ScrapedItem]) -> int:
    """Insert items into stg_listing and upsert store_product.
    Returns number of staged rows.
    """
    raise NotImplementedError("M2")


def finish_run(
    conn,
    scrape_run_id: int,
    *,
    status: str,
    items_found: int,
    items_changed: int | None = None,
    error: str | None = None,
) -> None:
    raise NotImplementedError("M2")
