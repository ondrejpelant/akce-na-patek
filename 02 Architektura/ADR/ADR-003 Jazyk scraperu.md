# ADR-003: Scraper v Pythonu, web v TypeScriptu

- **Stav:** přijato (21. 11. 2026)

## Kontext
Web na Vercelu = Next.js/TypeScript. Scraper může být v čemkoliv, běží v GitHub Actions.

## Rozhodnutí
Scraper, matcher a loader v **Pythonu 3.12** (správa prostředí přes `uv`):
- `httpx` (HTTP/2, async), `selectolax` (rychlé HTML), `playwright` (jen pro JS-heavy zdroje), `pydantic` (validace položek), `rapidfuzz` (fuzzy matching), `psycopg[binary]` (Postgres), `pytest`.
Web v **TypeScriptu**: Next.js (App Router), Tailwind CSS, Drizzle ORM.

## Důvody
- Python má nejlepší ekosystém pro scraping/parsing a data cleansing; Ondra ho zná z datové práce.
- Oddělení: web nemá žádnou závislost na scraperu, jen na DB schématu.

## Důsledky
- Dva toolchainy v jednom repu (monorepo bez workspaces): `web/` (npm) a `scraper/` (uv).
- Sdílený kontrakt = DB schéma ([[03 Data/Datový model]]).
