"""Scraper CLI (typer).

Commands:
  update        — orchestrate every active source, match, publish, revalidate web
  run           — run one source only (scrape → stage → match → SCD2 → refresh MV)
  match         — run auto-matching across all unmatched store_products
  publish       — SCD2 merge + refresh materialized view
  review        — interactive review of pending match candidates
  add-price     — manually add a regular price for a product in a store
  cleanup       — delete stg_listing older than 14 days

Full orchestration arrives in M4 (aktualizuj.bat). M2 ships `run --store penny`
end-to-end against Neon.
"""

from __future__ import annotations

import logging
import socket
import traceback

import typer
from rich.console import Console
from rich.logging import RichHandler

from scraper import __version__
from scraper.config import Config
from scraper.http import BlockedError, HttpClient
from scraper.load.publish import cleanup_staging, refresh_materialized_view
from scraper.load.scd2 import merge_prices
from scraper.load.staging import finish_run, open_run, stage_items
from scraper.sources import REGISTRY

app = typer.Typer(add_completion=False, no_args_is_help=True, help="Akce na pátek — scraper")
console = Console()
log = logging.getLogger(__name__)


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=False, show_path=False)],
    )


def _connect(cfg: Config):
    import psycopg

    return psycopg.connect(cfg.database_url)


@app.command()
def update(
    force: bool = typer.Option(False, "--force", help="Spustit i když dnes už proběhlo"),
    store: str | None = typer.Option(None, "--store", help="Jen jeden obchod (code)"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> None:
    """Orchestrate every active source, match, publish, revalidate web.
    Full orchestration arrives in M4; for M2 use `run --store <code>` instead.
    """
    _setup_logging(verbose)
    console.print(f"[yellow]update: not yet implemented (M4), force={force}, store={store}[/]")
    raise typer.Exit(code=0)


@app.command()
def run(
    store: str = typer.Option(..., "--store", help="Kód obchodu (tesco, penny, ...)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Nic nezapisuj do DB"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> None:
    """Scrape a single store end-to-end and refresh the materialized view."""
    _setup_logging(verbose)

    # ensure source modules register themselves
    import scraper.sources.penny  # noqa: F401

    if store not in REGISTRY:
        console.print(f"[red]Neznámý obchod: {store}. Známé: {sorted(REGISTRY)}[/]")
        raise typer.Exit(code=2)

    cfg = Config.from_env()
    source_cls = REGISTRY[store]
    host = socket.gethostname()

    with HttpClient(cfg.user_agent, cfg.rate_limit_rps) as http:
        source = source_cls(http)
        if dry_run:
            items = list(source.fetch())
            console.print(f"[green]{store}: {len(items)} items (dry-run, nic nezapsáno)[/]")
            for it in items[:5]:
                console.print(f"  {it.store_sku} {it.price_type:7} {it.price_czk:>8} Kč  {it.raw_name}")
            return

        with _connect(cfg) as conn:
            scrape_run_id = open_run(conn, store, host)
            conn.commit()

            try:
                items = list(source.fetch())
            except BlockedError as exc:
                finish_run(conn, scrape_run_id, status="failed", items_found=0, error=str(exc))
                conn.commit()
                console.print(f"[red]{store}: blokováno zdrojem — {exc}[/]")
                raise typer.Exit(code=1) from exc
            except Exception as exc:
                finish_run(
                    conn,
                    scrape_run_id,
                    status="failed",
                    items_found=0,
                    error=traceback.format_exc(),
                )
                conn.commit()
                console.print(f"[red]{store}: chyba při stahování — {exc}[/]")
                raise typer.Exit(code=1) from exc

            staged, matched = stage_items(conn, scrape_run_id, items)
            inserted = merge_prices(conn, [scrape_run_id])
            finish_run(
                conn,
                scrape_run_id,
                status="ok",
                items_found=len(items),
                items_changed=inserted,
            )
            conn.commit()

        with _connect(cfg) as conn:
            refresh_materialized_view(conn)

    console.print(
        f"[green]{store}: staged={staged}, matched={matched}, new price rows={inserted}[/]"
    )


@app.command()
def match() -> None:
    """Re-run auto-matching for every unmatched store_product."""
    cfg = Config.from_env()
    from scraper.load.staging import _automatch_unmatched

    with _connect(cfg) as conn, conn.cursor() as cur:
        cur.execute("select id from store")
        store_ids = [row[0] for row in cur.fetchall()]
        total = 0
        for sid in store_ids:
            total += _automatch_unmatched(conn, sid)
        conn.commit()
    console.print(f"[green]matched {total} store_products[/]")


@app.command()
def publish() -> None:
    """Refresh the materialized view and clean up old staging rows."""
    cfg = Config.from_env()
    with _connect(cfg) as conn:
        refresh_materialized_view(conn)
        deleted = cleanup_staging(conn)
    console.print(f"[green]publish: MV refreshed, {deleted} old stg_listing rows deleted[/]")


@app.command()
def review() -> None:
    console.print("[yellow]review: not yet implemented (M5)[/]")


@app.command(name="add-price")
def add_price() -> None:
    console.print("[yellow]add-price: not yet implemented (M4)[/]")


@app.command()
def cleanup() -> None:
    """Delete stg_listing rows older than 14 days."""
    cfg = Config.from_env()
    with _connect(cfg) as conn:
        deleted = cleanup_staging(conn)
    console.print(f"[green]deleted {deleted} old stg_listing rows[/]")


@app.command()
def version() -> None:
    console.print(f"scraper {__version__}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
