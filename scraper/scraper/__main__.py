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
from scraper.orchestrate import StoreResult, UpdateReport, run_update
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
    """Run every active source, SCD2 merge the results, refresh the MV and
    revalidate the web. Prints a summary table at the end.
    """
    _setup_logging(verbose)
    _write_log_file()

    cfg = Config.from_env()
    report = run_update(cfg, only_store=store, force=force)
    _print_report(report)

    raise typer.Exit(code=1 if report.any_failed else 0)


def _write_log_file() -> None:
    """Also append logs to scraper/logs/RRRR-MM-DD_HHMM.log for post-mortem."""
    from datetime import datetime

    from scraper.config import SCRAPER_ROOT

    log_dir = SCRAPER_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{datetime.now():%Y-%m-%d_%H%M}.log"
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(fh)


def _print_report(report: UpdateReport) -> None:
    from rich.table import Table

    title = f"Akce na pátek — aktualizace {report.started_at:%d. %m. %Y %H:%M}"
    table = Table(title=title, show_lines=False)
    table.add_column("Obchod")
    table.add_column("Status")
    table.add_column("Položek", justify="right")
    table.add_column("Změn cen", justify="right")
    table.add_column("Trvání", justify="right")
    table.add_column("Poznámka", max_width=40)

    for s in report.stores:
        table.add_row(*_row_for(s))

    console.print()
    console.print(table)

    if report.revalidated:
        console.print("[green]Web revalidován ✓[/]")
    elif report.revalidate_error:
        console.print(
            f"[yellow]Web NEBYL revalidován — {report.revalidate_error}. "
            "Běží web na REVALIDATE_URL?[/]"
        )
    else:
        console.print("[dim]Web nebyl revalidován — chybí REVALIDATE_URL / REVALIDATE_TOKEN v .env.[/]")


def _row_for(s: StoreResult) -> list[str]:
    status_text = {
        "ok": "[green]OK[/]",
        "partial": "[yellow]PARTIAL[/]",
        "failed": "[red]CHYBA[/]",
        "skipped": "[dim]SKIP[/]",
    }.get(s.status, s.status)
    duration = f"{int(s.duration_s // 60):d}:{int(s.duration_s % 60):02d}" if s.duration_s else "—"
    note = s.error or s.skipped_reason or ""
    return [
        s.name,
        status_text,
        str(s.items_found) if s.items_found else "—",
        str(s.items_changed) if s.items_changed else "—",
        duration,
        note,
    ]


@app.command()
def run(
    store: str = typer.Option(..., "--store", help="Kód obchodu (tesco, penny, ...)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Nic nezapisuj do DB"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> None:
    """Scrape a single store end-to-end and refresh the materialized view."""
    _setup_logging(verbose)

    # ensure source modules register themselves
    import scraper.sources.penny
    import scraper.sources.tesco  # noqa: F401

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
            note = source.partial_reason or (None if items else "0 položek")
            # Status must be final before the merge: SCD2 only closes missing
            # prices for 'ok' runs.
            finish_run(
                conn,
                scrape_run_id,
                status="partial" if note else "ok",
                items_found=len(items),
                error=note,
            )
            inserted = merge_prices(conn, [scrape_run_id])
            with conn.cursor() as cur:
                cur.execute(
                    "update scrape_run set items_changed = %s where id = %s",
                    (inserted, scrape_run_id),
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
    with _connect(cfg) as conn:
        total = _match_all_stores(conn)
        conn.commit()
        refresh_materialized_view(conn)
    console.print(f"[green]matched {total} store_products[/]")


@app.command()
def rematch(
    yes: bool = typer.Option(False, "--yes", help="Neptat se na potvrzení"),
) -> None:
    """Smaže všechny produkty a spáruje položky obchodů znovu od nuly.

    Použij po změně brands.yaml nebo pravidel párování. Ceny zůstanou (visí na
    položkách obchodů), ale produkty dostanou nová ID a slugy, takže staré
    odkazy /p/<slug> přestanou fungovat. Ručně potvrzené páry z `review` se
    ztratí.
    """
    cfg = Config.from_env()
    with _connect(cfg) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from product")
            n_products = cur.fetchone()[0]
        if not yes and not typer.confirm(
            f"Smazat {n_products} produktů a spárovat znovu?", default=False
        ):
            raise typer.Exit(code=1)
        with conn.cursor() as cur:
            cur.execute("delete from match_candidate")
            cur.execute("update store_product set product_id = null")
            cur.execute("delete from product")
        total = _match_all_stores(conn)
        conn.commit()
        refresh_materialized_view(conn)
        with conn.cursor() as cur:
            cur.execute("select count(*) from product")
            after = cur.fetchone()[0]
    console.print(f"[green]rematch: {n_products} → {after} produktů, spárováno {total} položek[/]")


def _match_all_stores(conn) -> int:
    from scraper.load.staging import match_unmatched

    with conn.cursor() as cur:
        cur.execute("select id from store")
        store_ids = [row[0] for row in cur.fetchall()]
    return sum(match_unmatched(conn, sid) for sid in store_ids)


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
    """Interactive review of pending match_candidate rows.

    For each pending candidate the CLI prints both sides (store_product vs.
    product), the fuzzy score, and prompts:
      a = accept the suggestion (link store_product -> product)
      r = reject this candidate (same pair never comes up again)
      n = new product (the store_product gets a fresh product_id)
      s = skip for now (leave as pending)
      q = quit
    """
    cfg = Config.from_env()
    with _connect(cfg) as conn, conn.cursor() as cur:
        cur.execute(
            """
            select mc.store_product_id, mc.product_id, mc.score, mc.method,
                   sp.raw_name, sp.volume_ml, s.name as store_name,
                   p.brand, p.name, p.volume_ml, p.abv
            from match_candidate mc
            join store_product sp on sp.id = mc.store_product_id
            join store s          on s.id = sp.store_id
            join product p        on p.id = mc.product_id
            where mc.status = 'pending' and sp.product_id is null
            order by mc.score desc
            """
        )
        rows = cur.fetchall()

        if not rows:
            console.print("[green]Žádné pending kandidáti.[/]")
            return

        console.print(f"[bold]{len(rows)} pending kandidát(ů)[/]")
        for (sp_id, p_id, score, method, raw_name, sp_vol, store_name,
             brand, name, p_vol, p_abv) in rows:
            console.print()
            console.print(f"[dim]--- skóre {score:.1f} ({method}) ---[/]")
            console.print(f"  [bold]{store_name}[/]: {raw_name} ({sp_vol} ml)")
            console.print(f"  [bold]product[/]:    {brand} {name} ({p_vol} ml{', ' + str(p_abv) + ' %' if p_abv else ''})")
            choice = typer.prompt("a/r/n/s/q", default="s").strip().lower()
            if choice == "q":
                break
            if choice == "a":
                cur.execute(
                    "update store_product set product_id = %s where id = %s",
                    (p_id, sp_id),
                )
                cur.execute(
                    "update match_candidate set status = 'accepted' "
                    "where store_product_id = %s and product_id = %s",
                    (sp_id, p_id),
                )
                console.print("[green]accepted[/]")
            elif choice == "r":
                cur.execute(
                    "update match_candidate set status = 'rejected' "
                    "where store_product_id = %s and product_id = %s",
                    (sp_id, p_id),
                )
                console.print("[yellow]rejected[/]")
            elif choice == "n":
                from scraper.matching.matcher import _category_id_by_slug

                cat_by_slug = _category_id_by_slug(conn)
                cur.execute(
                    """
                    select category_id from product where id = %s
                    """,
                    (p_id,),
                )
                category_id = cur.fetchone()[0] or next(iter(cat_by_slug.values()))
                cur.execute(
                    """
                    insert into product (category_id, brand, name, volume_ml, abv, slug)
                    values (%s, %s, %s, %s, null,
                            %s)
                    returning id
                    """,
                    (
                        category_id,
                        brand,
                        f"{name} (varianta {sp_id})",
                        sp_vol,
                        f"{brand}-{name}-{sp_vol}ml-v{sp_id}".lower().replace(" ", "-"),
                    ),
                )
                new_pid = cur.fetchone()[0]
                cur.execute(
                    "update store_product set product_id = %s where id = %s",
                    (new_pid, sp_id),
                )
                cur.execute(
                    "update match_candidate set status = 'rejected' "
                    "where store_product_id = %s and product_id = %s",
                    (sp_id, p_id),
                )
                console.print(f"[green]new product id={new_pid}[/]")
            else:
                console.print("[dim]skipped[/]")
            conn.commit()


@app.command(name="add-price")
def add_price(
    store: str = typer.Option(..., "--store", help="Kód obchodu (tesco, penny, ...)"),
    query: str = typer.Option(..., "--query", "-q", help="Fragment názvu/značky produktu"),
    price: float = typer.Option(..., "--price", help="Běžná cena v Kč"),
) -> None:
    """Ručně zapíše běžnou cenu produktu v obchodě.

    Použití: před nákupem jsem v prodejně viděl, že Finlandia 0,7 l stojí v Pennym
    289 Kč mimo akci -> `add-price --store penny --query finlandia -q 0.7 --price 289`.
    Cena se uloží jako price_source='manual', price_type='regular' a vydrží,
    dokud ji nový běh nepřepíše nebo dokud ji nenahradí novější manual zápis.
    """
    cfg = Config.from_env()
    with _connect(cfg) as conn, conn.cursor() as cur:
        cur.execute(
            """
            select p.id, p.brand, p.name, p.volume_ml
            from product p
            where p.search_text % f_norm(%s)
               or p.search_text like '%%' || f_norm(%s) || '%%'
            order by similarity(p.search_text, f_norm(%s)) desc
            limit 10
            """,
            (query, query, query),
        )
        candidates = cur.fetchall()

        if not candidates:
            console.print(f"[red]Žádný produkt nematchnul '{query}'[/]")
            raise typer.Exit(code=1)

        if len(candidates) > 1:
            console.print("[bold]Vyber produkt:[/]")
            for i, (_pid, brand, name, volume) in enumerate(candidates, 1):
                console.print(f"  {i}. {brand} {name} ({volume} ml)")
            raw = typer.prompt("Číslo", default="1")
            try:
                idx = int(raw) - 1
                if idx < 0 or idx >= len(candidates):
                    raise ValueError
            except ValueError as exc:
                raise typer.Exit(code=1) from exc
        else:
            idx = 0

        product_id, brand, name, volume = candidates[idx]

        cur.execute(
            """
            select sp.id from store_product sp
            join store s on s.id = sp.store_id
            where sp.product_id = %s and s.code = %s
            """,
            (product_id, store),
        )
        row = cur.fetchone()
        if row:
            store_product_id = row[0]
        else:
            # Create a synthetic store_product so the price has somewhere to hang.
            cur.execute(
                """
                insert into store_product (store_id, store_sku, product_id, raw_name,
                                           volume_ml, source_kind)
                select s.id, 'manual-' || %s, %s, %s, %s, 'leaflet'
                from store s where s.code = %s
                returning id
                """,
                (product_id, product_id, f"{brand} {name}", volume, store),
            )
            fetched = cur.fetchone()
            if fetched is None:
                console.print(f"[red]Neznámý obchod: {store}[/]")
                raise typer.Exit(code=1)
            store_product_id = fetched[0]

        # SCD2: close the current regular row, open a new manual one.
        cur.execute(
            """
            update price set valid_to = now()
            where store_product_id = %s and price_type = 'regular' and valid_to = 'infinity'
            """,
            (store_product_id,),
        )
        cur.execute(
            """
            insert into price (store_product_id, price_type, price_czk, price_source)
            values (%s, 'regular', %s, 'manual')
            """,
            (store_product_id, price),
        )
        conn.commit()

        refresh_materialized_view(conn)

    console.print(
        f"[green]✓ {brand} {name} ({volume} ml) v {store}: běžná cena {price:.2f} Kč (manual)[/]"
    )


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
