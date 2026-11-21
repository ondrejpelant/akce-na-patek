# ADR-001: Databáze — Neon Postgres

- **Stav:** přijato (21. 11. 2026)

## Kontext
Potřebujeme zdarma relační DB, kterou zapisuje denní dávka a čte web na Vercelu. Malý objem dat, 1 uživatel. Potřeba fulltextu tolerantního k diakritice a fuzzy matchingu.

## Možnosti
| | Neon | Supabase | Turso (SQLite) | SQLite soubor v repu |
|---|---|---|---|---|
| Cena | 0 | 0 | 0 | 0 |
| Pauza při nečinnosti | ne (scale-to-zero, auto wake) | **ano, po 7 dnech** | ne | ne |
| Postgres (pg_trgm, unaccent, MV) | ✅ | ✅ | ❌ | ❌ |
| Serverless driver pro Vercel | ✅ | ✅ (REST) | ✅ | n/a |
| Blízké mým SQL znalostem | ✅ | ✅ | ~ | ~ |

## Rozhodnutí
**Neon Postgres**, region EU (Frankfurt). Přístup z webu přes `@neondatabase/serverless` + Drizzle ORM, ze scraperu přes `psycopg` (pooled connection string).

## Důsledky
- Dvě DB role: `etl_rw` (scraper, GitHub Secret) a `web_ro` (jen SELECT, Vercel env).
- Migrace jako čisté SQL soubory v `db/migrations/` (spouští je GitHub Action nebo ručně), Drizzle jen jako query builder/typy (introspekce), ne jako zdroj schématu.
- Pokud Neon změní free tier, migrace na Supabase = změna connection stringu.
