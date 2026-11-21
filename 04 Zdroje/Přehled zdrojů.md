# Přehled zdrojů

> Stav po M0 Spike (21. 11. 2026). Zbylé 🔲 (Billa, Albert, Kaufland) jsou P2/P3, dostanou se na řadu po MVP.

| Obchod | Typ dat | Pokrytí alkoholu | Technika | Anti-bot | Runner | Priorita | Stav |
|---|---|---|---|---|---|---|---|
| [[Tesco]] | katalog + akce + Clubcard | plné (346 položek) | **Playwright Chromium** + HTML selektory `online-components-product-tile-*` | ⚠️ Akamai/DataDome (403 na `httpx`) | PC | P1 | ✅ ok |
| [[Lidl]] | leták jako obrázky | neznámé / OCR potřeba | leták API `endpoints.leaflets.schwarz/v4/flyer` → vrací PNG + OCR keywords, žádné strukturované ceny | ne | PC | ❌ | ❌ vyřazeno z MVP |
| [[Penny]] | akce týdne + cena před slevou | 2–10 lihovin/týden | **`httpx` + `selectolax`** nad SSR HTML (`/category/alkohol-24`) | ne | PC | P1 | ✅ ok |
| [[Billa]] | katalog? + akce | ověřit | produktové stránky billa.cz | ? | PC | P2 | 🔲 spike |
| [[Albert]] | akce (leták) + běžná z „před slevou“ | ověřit | HTML/JSON | ? | PC | P2 | 🔲 spike |
| [[Kaufland]] | akce („Nabídka prodejny“) | ověřit; stejný Schwarz leták API jako Lidl? | HTML / leaflet API | ⚠️ Cloudflare + DataDome | PC | P3 | 🔲 spike |
| [[Makro]] | B2B po přihlášení | — | — | — | — | ❌ vyřazeno | — |

Legenda priorit: P1 = MVP, P2 = hned po MVP, P3 = pokud to půjde bez obcházení ochran.

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
