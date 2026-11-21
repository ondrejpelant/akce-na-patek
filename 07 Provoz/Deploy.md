# Deploy

## Jednorázové nastavení
1. **GitHub:** soukromé repo `akce-na-patek` (scrapery nechceme publikovat). Push obsahu této složky (bez `.obsidian/workspace*.json`).
2. **Neon:** projekt `akce-na-patek`, region Frankfurt → DB `app` → vytvořit role `etl_rw` a `web_ro` → spustit `db/migrations/*.sql` v pořadí.
3. **Lokální `scraper/.env`** na PC: `DATABASE_URL` (pooled, role etl_rw), `REVALIDATE_URL` (`https://<app>.vercel.app/api/revalidate`), `REVALIDATE_TOKEN`. Vzor v `scraper/.env.example` (commitnutý, bez hodnot).
4. **Vercel:** Import repo → Root Directory `web` → Framework Next.js → env `DATABASE_URL` (role web_ro), `REVALIDATE_TOKEN`. Plán Hobby.
5. Vypnout Vercel preview deploye pro větve, které nepotřebuješ (šetří build minuty).

## Průběžně
- Merge do `main` → Vercel automaticky nasadí web.
- DB migrace: ručně (`psql $DATABASE_URL -f db/migrations/00X_*.sql`) nebo workflow `migrate.yml` s `workflow_dispatch`. Migrace jen dopředu, nikdy needitovat již spuštěnou.

## .gitignore (kořen)
`.env*`, `web/node_modules/`, `web/.next/`, `scraper/.venv/`, `__pycache__/`, `.obsidian/workspace*.json`, `.obsidian/cache`
