# Přehled zdrojů

> Stav 21. 11. 2026 (po M0 Spike a hledání zdroje běžných cen). Albert a Kaufland zůstávají P2/P3.

| Obchod | Typ dat | Pokrytí alkoholu | Technika | Anti-bot | Runner | Priorita | Stav |
|---|---|---|---|---|---|---|---|
| [[Tesco]] | katalog + akce + Clubcard | jen 1. stránka (~48 z 346), od 2. stránky 403 | **Playwright (systémový Edge)** + HTML selektory `online-components-product-tile-*` | ⚠️ Akamai (403 na `httpx` i na str. 2+) | PC | P1 | ⚠️ partial |
| [[Lidl]] | leták jako obrázky | neznámé / OCR potřeba | leták API `endpoints.leaflets.schwarz/v4/flyer` → vrací PNG + OCR keywords, žádné strukturované ceny | ne | PC | ❌ | ❌ vyřazeno z MVP |
| [[Penny]] | akce týdne + cena před slevou | 2–10 lihovin/týden | **`httpx` + `selectolax`** nad SSR HTML (`/category/alkohol-24`) | ne | PC | P1 | ✅ ok |
| [[Billa]] | **katalog s běžnými cenami** + BILLA Klub | plné (456 lihovin) | **`httpx` + `selectolax`**, `/produkty/lihoviny-1559` (stejný frontend jako Penny) | ne | PC | P1 | ✅ ok |
| [[Albert]] | akce (leták) + běžná z „před slevou“ | ověřit | HTML/JSON | ? | PC | P2 | 🔲 spike |
| [[Kaufland]] | akce („Nabídka prodejny“) | ověřit; stejný Schwarz leták API jako Lidl? | HTML / leaflet API | ⚠️ Cloudflare + DataDome | PC | P3 | 🔲 spike |
| [[Makro]] | B2B po přihlášení | — | — | — | — | ❌ vyřazeno | — |

Legenda priorit: P1 = MVP, P2 = hned po MVP, P3 = pokud to půjde bez obcházení ochran.

## Hledání zdroje běžných cen (21. 11. 2026)
- **Billa** — katalog s cenami zůstal po zrušení e-shopu → zařazena (viz [[Billa]]). Jediný nalezený první-stranný zdroj běžných cen celého sortimentu.
- Agregátory (Potravinka.cz, Kupní Síla, kupi.cz) běžné ceny mají, ale jako zdroj je nebereme — jejich databáze je jejich produkt (viz [[Agregátory a jiné]]).
- Státní otevřená data cen po obchodech v ČR nejsou (ČSÚ jen průměrné ceny a indexy; cenový radar má jen Slovensko).
- Albert (e-shop zavřen 12/2025) a Lidl běžné ceny online neukazují; Tesco ano, ale jen 1. stránku.

## Výsledek M0 pro P1
- **2 reálně použitelné zdroje v MVP: Tesco (katalog) a Penny (týdenní akce).**
- Lidl vyřazen z MVP — leták je bitmapa, bez OCR se k cenám nedostaneme bez porušení etických pravidel.
- Tesco potřebuje Playwright (cca 400 MB prohlížeč, `uv run playwright install chromium`), Penny si vystačí s `httpx`.

## Obecný postup spike pro každý zdroj
1. Otevřít web v Chrome DevTools → záložka Network → filtr `Fetch/XHR`. Hledat JSON endpointy, které stránka sama volá (často čistší než HTML).
2. Zkontrolovat `robots.txt` a podmínky užití; zapsat do note.
3. Zkusit endpoint přes `curl` / `httpx` **z domácího PC** (tam poběží aktualizace). Zapsat, zda funguje bez prohlížeče, nebo je potřeba Playwright.
4. Uložit 2–3 vzorové odpovědi do `scraper/tests/fixtures/<store>/` (pro testy parseru).
5. Zjistit: **cena před slevou** (= zdroj běžné ceny), ID položky, název, objem, %, cena, cena před slevou, platnost akce, věrnostní příznak, URL obrázku, EAN, kategorie.
6. Vyplnit šablonu [[Šablony/Zdroj]].
