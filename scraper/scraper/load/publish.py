"""Refresh the materialized view that feeds the web.
Called at the end of every update, even if some stores failed.
"""

from __future__ import annotations


def refresh_materialized_view(conn) -> None:
    """refresh materialized view concurrently mv_current_price;"""
    with conn.cursor() as cur:
        cur.execute("refresh materialized view concurrently mv_current_price;")
    conn.commit()


def cleanup_staging(conn, days: int = 14) -> int:
    """Delete stg_listing rows older than `days`. Returns deleted count."""
    with conn.cursor() as cur:
        cur.execute(
            "delete from stg_listing where loaded_at < now() - make_interval(days => %s);",
            (days,),
        )
        deleted = cur.rowcount or 0
    conn.commit()
    return deleted
