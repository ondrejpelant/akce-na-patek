"""Scraper CLI (typer).

Commands:
  update        — orchestrate every active source, match, publish, revalidate web
  run           — run one source only
  match         — match staged items to canonical products
  publish       — SCD2 merge + refresh materialized view
  review        — interactive review of pending match candidates
  add-price     — manually add a regular price for a product in a store
  cleanup       — delete stg_listing older than 14 days

Full orchestration arrives in M2 (one source end-to-end) and M4 (aktualizuj.bat).
"""

from __future__ import annotations

import typer
from rich.console import Console

from scraper import __version__

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Akce na pátek — scraper",
)
console = Console()


@app.command()
def update(
    force: bool = typer.Option(False, "--force", help="Spustit i když dnes už proběhlo"),
    store: str | None = typer.Option(None, "--store", help="Jen jeden obchod (code)"),
) -> None:
    """Orchestrate every active source, match, publish, revalidate web.
    Full implementation in M2-M4.
    """
    console.print(f"[yellow]update: not yet implemented (M2-M4), force={force}, store={store}[/]")
    raise typer.Exit(code=0)


@app.command()
def run(
    store: str = typer.Option(..., "--store", help="Kód obchodu (tesco, lidl, ...)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Nic nezapisuj do DB"),
    save_fixtures: bool = typer.Option(False, "--save-fixtures", help="Uložit surové odpovědi"),
) -> None:
    """Run one source. In M1 this is a stub that confirms CLI wiring works."""
    console.print(f"[yellow]run: not yet implemented (M2), store={store}, dry_run={dry_run}[/]")
    raise typer.Exit(code=0)


@app.command()
def match() -> None:
    console.print("[yellow]match: not yet implemented (M2)[/]")


@app.command()
def publish() -> None:
    console.print("[yellow]publish: not yet implemented (M2)[/]")


@app.command()
def review() -> None:
    console.print("[yellow]review: not yet implemented (M5)[/]")


@app.command(name="add-price")
def add_price() -> None:
    console.print("[yellow]add-price: not yet implemented (M4)[/]")


@app.command()
def cleanup() -> None:
    console.print("[yellow]cleanup: not yet implemented (M2)[/]")


@app.command()
def version() -> None:
    console.print(f"scraper {__version__}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
