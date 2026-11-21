# Billa
- **Web:** https://www.billa.cz
- **Typ dat:** ✅ **katalog s běžnými cenami** + ceny s **BILLA Klubem** (věrnostní). E-shop skončil 31. 1. 2026, ale katalog s cenami na webu zůstal (`/produkty/…`, `/produkt/…`).
- **Priorita:** P1 od 21. 11. 2026 — jediný nalezený první-stranný zdroj **běžných (neakčních) cen** pro celý sortiment lihovin.

## Co víme (spike 21. 11. 2026)
- `robots.txt` obsahuje jen odkaz na sitemapu, nic nezakazuje.
- Stejný frontend jako Penny (REWE, Nuxt 3 SSR): karta `li.ws-product-tile`, `data-product-slug` = `<slug>-<sku>`, `data-teaser-name` = název. Pomocné funkce sdílíme s `sources/penny.py`.
- **Funguje z čistého `httpx`** s naším UA (200, bez anti-bot ochrany).
- Lihoviny: [/produkty/lihoviny-1559](https://www.billa.cz/produkty/lihoviny-1559) — **456 produktů**. Podkategorie `rum-a-tuzemak-1560`, `gin-1561`, `brandy-a-konak-1562`, `whiskey-a-bourbon-1563`, `likery-1564`, `vodka-1566` pokrývají jen 290 z nich (zbytek — pálenky, bylinné… — je jen v nadřazené).
- Stránkování: `?page=N` vrátí stránky 1..N najednou (30 na stránku); stránka za koncem vrátí **nic** → nejdřív přečíst „456 produktů", pak `?page=ceil(456/30)`. Pozor: `selectolax .text()` slepí sousední čísla („44" + „456 produktů") — `text(separator=" ")`.
- Cenové bloky `[data-test="product-price-type"]`: „Běžná cena" → `regular`, „S BILLA klub účtem" → `loyalty` (s `regular_czk` = běžná). Blok s přeškrtnutou cenou = akce pro všechny → `promo`. Platnost klubových cen na kartě není → `promo_to` prázdné (zavře se, až zmizí z katalogu).
- Obrázky: karta má jen base64 placeholder; URL jsou v Nuxt payloadu (`https://images.cdn.europe-west1.gcp.commercetools.com/…/82-219425-…jpg`) a začínají číslem artiklu (`82-219425` = sku `82219425`) → mapování bez dalších požadavků; ukládáme variantu `-medium`.

## Fixture
`scraper/tests/fixtures/billa/lihoviny_two_tiles.html` — Božkov Originál Tuzemský (běžná 200,90 + klub 109,90), Jägermeister (jen běžná) a úryvek payloadu s jejich obrázky.

## Rozhodnutí po spike
- **Zařadit — P1, runner: PC, `httpx` + `selectolax`** (`sources/billa.py`), `source_kind='catalog'`.
- Jeden běh = 2 požadavky na celý výpis + 2 na každou podkategorii (kvůli kategorii) ≈ 12–14 požadavků, ~2 min s rate limitem 1 / 2 s.
- První běh 21. 11.: 448 cen, 37 produktů spárovaných s Tescem/Penny (např. Finlandia: Billa 299,90 vs. Tesco Clubcard 319,90 / běžná 479,90).

## Spike checklist
- [x] Existuje stále katalog s cenami? → ano, kompletní, s běžnou i klubovou cenou.
- [x] JSON endpoint? → ne, SSR HTML (+ Nuxt payload pro obrázky).
- [x] Rozlišení akce pro všechny vs. BILLA Klub → štítek cenového bloku.
- [ ] Platnost akce → u klubových cen na kartě není.
- [x] robots.txt, podmínky → robots nic nezakazuje.
- [x] Fixtures
