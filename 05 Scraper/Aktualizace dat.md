# Aktualizace dat (ruční, na PC)

Rozhodnutí: [[../02 Architektura/ADR/ADR-005 Ruční aktualizace na PC|ADR-005]].

## Jak to používám
1. Jdu nakupovat → **dvojklik na `aktualizuj.bat`** v kořeni složky (nebo v Claude Code `/aktualizuj`).
2. Za pár minut se objeví souhrn:
```
Akce na pátek — aktualizace 21. 11. 2026 09:15
┌──────────┬────────┬─────────┬──────────┬──────────┬────────┐
│ Obchod   │ Status │ Položek │ Změn cen │ Nespáro- │ Trvání │
│          │        │         │          │ váno     │        │
├──────────┼────────┼─────────┼──────────┼──────────┼────────┤
│ Tesco    │ OK     │ 1 204   │ 37       │ 0        │ 2:41   │
│ Lidl     │ OK     │ 18      │ 18       │ 2        │ 0:09   │
│ Penny    │ CHYBA  │ —       │ —        │ —        │ 0:03   │  403 Forbidden
│ ...      │        │         │          │          │        │
└──────────┴────────┴─────────┴──────────┴──────────┴────────┘
Web aktualizován ✓  https://akce-na-patek.vercel.app
Nespárované položky: 2 → spusť `aktualizuj.bat review`
Stiskni Enter pro zavření…
```
3. Otevřu appku v telefonu — data jsou čerstvá.

## `aktualizuj.bat` (vytvořit v M4)
```bat
@echo off
chcp 65001 >nul
cd /d "%~dp0scraper"
if "%1"=="review" (
  uv run python -m scraper review
) else (
  uv run python -m scraper update %*
)
echo.
pause
```
Parametry: `aktualizuj.bat` (vše) · `aktualizuj.bat --store lidl` (jen jeden obchod) · `aktualizuj.bat --force` (spustit i když dnes už proběhlo) · `aktualizuj.bat review` (ruční párování).

## Příkaz `scraper update` (orchestrace v Pythonu)
Jeden proces, sekvenčně:
1. Načte `.env` (`DATABASE_URL`, `REVALIDATE_URL`, `REVALIDATE_TOKEN`).
2. **Přeskočí** obchody, které dnes už úspěšně proběhly (pokud není `--force`).
3. Pro každý aktivní obchod: `run --store X` v `try/except` — chyba jednoho obchodu neukončí ostatní.
4. `match` → `publish` (SCD2 load + refresh MV) → vždy, i když některé obchody selhaly.
5. `POST REVALIDATE_URL` (Vercel on-demand revalidace).
6. Vypíše souhrnnou tabulku (knihovna `rich`) a log uloží do `scraper/logs/RRRR-MM-DD_HHMM.log`.
7. Exit code 0 = vše OK, 1 = něco selhalo (pro případný Plánovač úloh).

## Claude Code příkaz
`.claude/commands/aktualizuj.md` — Claude spustí aktualizaci, přečte souhrn a log, a pokud nějaký zdroj selhal na parsování, navrhne opravu parseru.

## Jednorázová příprava PC
1. Nainstalovat `uv` (`winget install astral-sh.uv`), Git.
2. `cd scraper && uv sync`; pokud některý zdroj potřebuje prohlížeč: `uv run playwright install chromium`.
3. Vytvořit `scraper/.env` podle `scraper/.env.example`.

## CI (`.github/workflows/ci.yml`)
Na push/PR: `uv run pytest` + `ruff` ve `scraper/`, `npm run lint && npm run build` ve `web/`. Žádný scraping v GitHubu.
