# ADR-002: Orchestrace — GitHub Actions cron

- **Stav:** ❌ nahrazeno [[ADR-005 Ruční aktualizace na PC]] (21. 11. 2026). GitHub Actions zůstává jen pro CI.

## Kontext
Denní spuštění scraperů pro 6–7 obchodů, některé s Playwrightem (headless Chromium), celkem desítky minut. Zdarma.

## Možnosti
1. **Vercel Cron** — Hobby max 1×/den, funkce max 300 s, bez Chromia v rozumné velikosti → ❌
2. **GitHub Actions schedule** — zdarma, plný Linux VM, Playwright OK, matice per obchod, logy, e-mail při selhání → ✅
3. **Self-hosted runner / Plánovač úloh na mém PC** — rezidenční IP (méně blokací), ale závislé na zapnutém PC → záloha
4. Cloudflare Workers Cron, Render cron — limity CPU / placené → ❌

## Rozhodnutí
**GitHub Actions** s cronem `0 3 * * *` UTC (4:00 v zimě / 5:00 v létě). Matice per obchod (`fail-fast: false`), po ní job `match-and-publish`. Zdroje, které z datacenter IP nejdou, se označí `runner: self-hosted` a poběží na PC (Windows, GitHub runner jako služba).

## Důsledky
- Spuštění i ručně (`workflow_dispatch`) s parametrem obchodu.
- Při veřejném repu nutný keepalive (60denní vypnutí), viz [[05 Scraper/Aktualizace dat]].
- Žádný „orchestrátor“ typu Airflow/Dagster — pro 1 DAG o 3 krocích by to byl overkill.
