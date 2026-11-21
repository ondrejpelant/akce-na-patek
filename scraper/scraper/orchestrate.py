"""Orchestration for `scraper update`.

Runs every active source sequentially and keeps per-store state in scrape_run:
  - BlockedError  -> status='failed'
  - other errors  -> status='failed'
  - sanity check  -> status='partial'  (items_found too low)
  - otherwise     -> status='ok'

After every source is done, SCD2 merge runs over ALL ok+partial runs from this
cycle, materialised view is refreshed, and the web is asked to revalidate.

Failure of one store never aborts the others and never closes the other stores'
current prices (close-on-absence runs per-store in scd2._close_missing).
"""

from __future__ import annotations

import logging
import socket
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from scraper.config import Config
from scraper.http import BlockedError, HttpClient
from scraper.load.publish import cleanup_staging, refresh_materialized_view
from scraper.load.scd2 import merge_prices
from scraper.load.staging import finish_run, open_run, stage_items
from scraper.sources import REGISTRY

# sanity check: at least this fraction of the 7-day median must be returned.
SANITY_RATIO = 0.5

log = logging.getLogger(__name__)


@dataclass
class StoreResult:
    code: str
    name: str
    status: str
    items_found: int = 0
    items_changed: int = 0
    duration_s: float = 0.0
    error: str | None = None
    skipped_reason: str | None = None


@dataclass
class UpdateReport:
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None
    stores: list[StoreResult] = field(default_factory=list)
    revalidated: bool = False
    revalidate_error: str | None = None  # None + not revalidated = not configured

    @property
    def any_failed(self) -> bool:
        return any(s.status == "failed" for s in self.stores)


def run_update(
    cfg: Config,
    *,
    only_store: str | None = None,
    force: bool = False,
) -> UpdateReport:
    """Entry point for `scraper update`."""
    _load_source_registry()
    host = socket.gethostname()
    report = UpdateReport()

    import psycopg

    conn = psycopg.connect(cfg.database_url)
    try:
        active_stores = _list_active_stores(conn)
    finally:
        conn.close()

    with HttpClient(cfg.user_agent, cfg.rate_limit_rps) as http:
        for store_id, code, name in active_stores:
            if only_store and code != only_store:
                continue
            if code not in REGISTRY:
                report.stores.append(
                    StoreResult(code=code, name=name, status="skipped",
                                skipped_reason="no parser")
                )
                continue

            with psycopg.connect(cfg.database_url) as conn:
                if not force and _ran_ok_today(conn, store_id):
                    report.stores.append(
                        StoreResult(code=code, name=name, status="skipped",
                                    skipped_reason="dnes OK")
                    )
                    continue

                report.stores.append(_run_store(conn, http, code, name, host))

    scrape_run_ids = [
        _latest_run_id_for(cfg, s.code)
        for s in report.stores
        if s.status in {"ok", "partial"}
    ]
    scrape_run_ids = [i for i in scrape_run_ids if i is not None]

    if scrape_run_ids:
        with psycopg.connect(cfg.database_url) as conn:
            merge_prices(conn, scrape_run_ids)
            conn.commit()
            refresh_materialized_view(conn)
            cleanup_staging(conn)

    report.revalidated, report.revalidate_error = _try_revalidate(cfg)
    report.finished_at = datetime.now()
    return report


# ---------------------------------------------------------------------------


def _run_store(conn, http: HttpClient, code: str, name: str, host: str) -> StoreResult:
    started = time.monotonic()
    source_cls = REGISTRY[code]
    source = source_cls(http)

    scrape_run_id = open_run(conn, code, host)
    conn.commit()

    try:
        items = list(source.fetch())
    except BlockedError as exc:
        finish_run(conn, scrape_run_id, status="failed", items_found=0, error=str(exc))
        conn.commit()
        return StoreResult(
            code=code, name=name, status="failed",
            duration_s=time.monotonic() - started,
            error=f"blokováno: {exc}",
        )
    except Exception as exc:
        finish_run(
            conn, scrape_run_id, status="failed", items_found=0,
            error=traceback.format_exc(),
        )
        conn.commit()
        return StoreResult(
            code=code, name=name, status="failed",
            duration_s=time.monotonic() - started,
            error=f"{type(exc).__name__}: {exc}",
        )

    staged, _matched = stage_items(conn, scrape_run_id, items)

    # partial = SCD2 will not close prices this run did not see.
    threshold = _sanity_threshold(conn, store_code=code)
    note: str | None = None
    if source.partial_reason:
        note = source.partial_reason
    elif not items:
        note = "0 položek"
    elif threshold is not None and len(items) < threshold:
        note = f"jen {len(items)} položek (< 50 % mediánu {threshold * 2:.0f})"
    status = "partial" if note else "ok"

    finish_run(
        conn, scrape_run_id, status=status,
        items_found=len(items), items_changed=None, error=note,
    )
    conn.commit()

    return StoreResult(
        code=code, name=name, status=status,
        items_found=len(items), items_changed=staged,
        duration_s=time.monotonic() - started,
        error=note,
    )


def _list_active_stores(conn) -> list[tuple[int, str, str]]:
    with conn.cursor() as cur:
        cur.execute("select id, code, name from store where is_active order by code")
        return list(cur.fetchall())


def _ran_ok_today(conn, store_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            select 1 from scrape_run
            where store_id = %s and status in ('ok','partial')
              and items_found > 0
              and finished_at::date = current_date
            limit 1
            """,
            (store_id,),
        )
        return cur.fetchone() is not None


def _sanity_threshold(conn, *, store_code: str) -> float | None:
    """50 % of the median items_found across the last 7 ok runs of this store.
    Returns None when there is no history yet (so first runs pass).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            select percentile_cont(0.5) within group (order by items_found)
            from (
              select r.items_found
              from scrape_run r join store s on s.id = r.store_id
              where s.code = %s and r.status = 'ok' and r.items_found is not null
              order by r.started_at desc
              limit 7
            ) last_runs
            """,
            (store_code,),
        )
        row = cur.fetchone()
    if not row or row[0] is None:
        return None
    return float(row[0]) * SANITY_RATIO


def _latest_run_id_for(cfg: Config, store_code: str) -> int | None:
    import psycopg

    with psycopg.connect(cfg.database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            select r.id from scrape_run r join store s on s.id = r.store_id
            where s.code = %s and r.started_at::date = current_date
            order by r.started_at desc limit 1
            """,
            (store_code,),
        )
        row = cur.fetchone()
    return row[0] if row else None


def _try_revalidate(cfg: Config) -> tuple[bool, str | None]:
    """POST to the web's revalidate route. Returns (ok, error).
    (False, None) means revalidation is not configured."""
    if not cfg.revalidate_url or not cfg.revalidate_token:
        return False, None
    try:
        resp = httpx.post(
            cfg.revalidate_url,
            params={"token": cfg.revalidate_token},
            timeout=10,
        )
        resp.raise_for_status()
        return True, None
    except Exception as exc:
        log.warning("revalidate failed: %s", exc)
        return False, f"{type(exc).__name__}: {exc}"


def _load_source_registry() -> None:
    """Import every source module so @register populates REGISTRY."""
    import scraper.sources.penny
    import scraper.sources.tesco  # noqa: F401
