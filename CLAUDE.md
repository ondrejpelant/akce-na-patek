# CLAUDE.md — Akce na pátek

Tenhle soubor čte Claude Code na začátku každé session. Složka `Akce-na-patek` je **zároveň Obsidian vault (dokumentace) i kořen git repozitáře (kód)**.

## Co stavíme (1 odstavec)
Osobní webová appka (bez přihlašování), která denně stahuje ceny alkoholu z českých řetězců (Tesco, Billa, Albert, Lidl, Kaufland, Penny, případně Makro) a ukazuje, kde je daný produkt **dnes nejlevnější**. Úvodní stránka = mřížka karet ve stylu Vinted (fotka, nejnižší cena, obchod), nahoře vyhledávání a kategorie. Detail produktu = ceny ve všech obchodech seřazené vzestupně. Vše musí běžet **zdarma**.
Detail: [[01 Zadání/Vize a rozsah]] · Revize reálnosti: [[01 Zadání/Revize plánu]]

## Než začneš cokoliv implementovat
1. Přečti [[00 Index]] a aktuální milník v [[08 Roadmapa/Roadmapa]].
2. Přečti note k oblasti, na které pracuješ (zdroj → `04 Zdroje/<řetězec>.md`, DB → [[03 Data/Datový model]] atd.).
3. Zkontroluj [[09 Otevřené otázky]] — pokud úkol závisí na nezodpovězené otázce, zeptej se, nehádej.

## Pravidla
- **Zdroj pravdy pro technická rozhodnutí jsou ADR** v `02 Architektura/ADR/`. Stack neměň bez nového ADR (šablona v `Šablony/`).
- **Nula nákladů.** Pokud řešení vyžaduje placenou službu, placený proxy/unblocker nebo kartu, zastav se a zeptej se.
- **Scraping etika:** dodržuj [[07 Provoz/Právní a etické zásady]] — rate limit, identifikovatelný User-Agent, robots.txt, žádné obcházení CAPTCHA, loginu ani anti-bot ochran.
- **Tajné údaje** jen v `scraper/.env` (v .gitignore) a Vercel Environment Variables. Nikdy necommituj connection stringy.
- **Jazyk:** dokumentace a komentáře česky, kód, názvy tabulek/sloupců a commity anglicky.
- **Malé kroky:** jeden úkol z roadmapy = jeden PR/commit set. Po každém úkolu spusť testy/lint.

## Po dokončení úkolu
- Odškrtni úkol v [[08 Roadmapa/Roadmapa]].
- Zapiš krátký záznam do `10 Deník/RRRR-MM-DD.md` (šablona [[Šablony/Deník]]): co je hotovo, co nefunguje, co dál.
- Pokud se realita liší od dokumentace (zdroj změnil strukturu, limit free tieru se změnil…), **oprav dokumentaci** ve stejném kroku.

## Struktura repozitáře (cílová)
```
Akce-na-patek/
├── CLAUDE.md                 ← tento soubor
├── 00 Index.md … 10 Deník/   ← Obsidian dokumentace
├── web/                      ← Next.js appka (deploy Vercel, Root Directory = web)
├── scraper/                  ← Python scrapery + matching + loader
├── db/migrations/            ← SQL migrace (číslované, jen dopředu)
├── .github/workflows/ci.yml  ← jen CI (testy, build)
├── .claude/commands/         ← /aktualizuj
└── aktualizuj.bat            ← ruční aktualizace dat (M4)
```

## Aktualizace dat
Neběží automaticky. Ondra ji spouští ručně před nákupem: dvojklik na `aktualizuj.bat` nebo `/aktualizuj` v Claude Code. Viz [[05 Scraper/Aktualizace dat]].

## Klíčová produktová rozhodnutí (21. 11. 2026)
- Každý obchod má u produktu **výchozí běžnou cenu**; po dobu akce ji přebije akční cena. U obchodů bez katalogu se běžná cena odvozuje z „ceny před slevou“ v letáku, případně se zadá ručně.
- Nejnižší cena **zahrnuje věrnostní ceny**, ale ty jsou barevně odlišené s ikonou ⓘ a vysvětlivkou.
- Jen lihoviny. Makro vyřazeno.

## Příkazy (doplnit po scaffoldu v M1)
- `cd web && npm run dev` — lokální frontend
- `aktualizuj.bat` — plná aktualizace (`--store X`, `--force`, `review`, `add-price`)
- `cd scraper && uv run python -m scraper run --store tesco --dry-run` — test scraperu bez zápisu do DB
- `cd scraper && uv run pytest`
- `cd scraper && uv run python -m scraper rematch` — po změně `brands.yaml`/pravidel párování: smaže produkty a spáruje znovu (mění slugy, maže výsledky `review`)
