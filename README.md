# 🍾 Akce na pátek

> Osobní srovnávač cen alkoholu v českých supermarketech. Zdarma, bez přihlašování, denně aktualizovaný.

[![CI](https://github.com/ondrejpelant/akce-na-patek/actions/workflows/ci.yml/badge.svg)](https://github.com/ondrejpelant/akce-na-patek/actions/workflows/ci.yml)

Mřížka karet ve stylu Vinted (fotka, nejnižší cena, obchod), nahoře vyhledávání a kategorie. Detail produktu = ceny ve všech obchodech seřazené vzestupně. Jen lihoviny, jen akce a katalogové ceny Tesca, jen já.

## Jak to funguje

```
┌───────────────────────┐    ┌──────────────┐    ┌────────────────┐
│  scraper (Python)     │───►│  Neon        │◄───│  web (Next.js) │
│  Tesco, Penny, …      │    │  Postgres    │    │  Vercel Hobby  │
│  spouštěno ručně      │    │  (SCD2 ceny) │    │  read-only     │
│  na PC před nákupem   │    │              │    │                │
└───────────────────────┘    └──────────────┘    └────────────────┘
```

- **ETL** běží lokálně, ručně — `aktualizuj.bat` před nákupem, ne cron.
- **DB** je Neon Postgres (free tier), ceny ve formátu SCD2.
- **Web** jen čte přes serverless driver, cache + on-demand revalidace po aktualizaci.

Detailní rozpad: [`02 Architektura/Architektura.md`](02%20Architektura/Architektura.md) a ADRy v [`02 Architektura/ADR/`](02%20Architektura/ADR/).

## Rozcestník (Obsidian vault)

- [`00 Index.md`](00%20Index.md) — kompletní přehled dokumentace
- [`01 Zadání/`](01%20Zadání/) — co appka dělá a co ne
- [`03 Data/Datový model.md`](03%20Data/Datový%20model.md) — DDL, SCD2, view vrstvy
- [`04 Zdroje/Přehled zdrojů.md`](04%20Zdroje/Přehled%20zdrojů.md) — matice obchodů (status po M0 Spike)
- [`08 Roadmapa/Roadmapa.md`](08%20Roadmapa/Roadmapa.md) — milníky s akceptačními kritérii
- [`CLAUDE.md`](CLAUDE.md) — kontext pro Claude Code

## Rozběhání lokálně

### Jednorázová příprava

```powershell
winget install astral-sh.uv
```

Pak si zkopíruj env soubory a doplň Neon connection stringy (viz [`07 Provoz/Deploy.md`](07%20Provoz/Deploy.md)):

```powershell
Copy-Item scraper\.env.example scraper\.env
Copy-Item web\.env.example web\.env.local
```

### Scraper

```powershell
cd scraper
uv sync
uv run pytest
```

### Web

```powershell
cd web
npm install
npm run dev
```

Otevři [http://localhost:3000](http://localhost:3000). Kontrola DB: [/api/health](http://localhost:3000/api/health).

### Aktualizace dat (M4)

Dvojklik na `aktualizuj.bat` v kořeni → scraper projede všechny aktivní zdroje → data se objeví na webu. Zatím není, přijde v milníku M4.

## Struktura repa

```
Akce-na-patek/
├── CLAUDE.md                  ← kontext pro Claude Code
├── 00 Index.md … 10 Deník/    ← Obsidian vault (dokumentace, ADR, deník)
├── scraper/                   ← Python (uv): sources, matching, load
├── web/                       ← Next.js 16 + Tailwind v4 (Vercel Hobby)
├── db/migrations/             ← SQL migrace (jen dopředu)
└── .github/workflows/ci.yml   ← jen CI (testy, build), scraping tu neběží
```

## Pravidla scrapování

Osobní nekomerční použití. Dodržujeme `robots.txt`, rate limit 1 req / 2 s, identifikovatelný `User-Agent`. Neobcházíme CAPTCHA, anti-bot ochrany ani přihlášení. Když zdroj začne blokovat, vyřadí se. Detail: [`07 Provoz/Právní a etické zásady.md`](07%20Provoz/Právní%20a%20etické%20zásady.md).

## Licence a odpovědnost

Osobní projekt, bez licence (žádná práva nejsou poskytována). Ceny jsou orientační, neneseme za ně odpovědnost. Ověř si je v obchodě. **Nadměrné pití škodí zdraví.**
