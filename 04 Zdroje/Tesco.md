# Tesco
- **Web:** https://nakup.itesco.cz (online nákup) · leták na itesco.cz
- **Typ dat:** plný katalog s cenami + akční ceny + **Clubcard ceny** (věrnostní)
- **Priorita:** P1 — jediný velký řetězec s plným online katalogem potravin → páteř katalogu produktů (fotky, EAN?)

## Co víme (po spike 21. 11. 2026)
- E-shop běží, kategorie [napoje/lihoviny](https://nakup.itesco.cz/shop/cs-CZ/browse/napoje/lihoviny) má **346 produktů**, výpis po 24 (volitelně 48) na stránku.
- Server-side rendered HTML → žádný JSON/GraphQL endpoint pro katalog. Parser = `selectolax` nad HTML.
- `robots.txt` katalog nezakazuje (disallowy jsou jen na login/filter URL, viz `nakup.itesco.cz/robots.txt`).
- Sitemapy: `nakup.itesco.cz/sitemaps/cs-CZ/groceries/products-index.xml` a `promotions-index.xml` — užitečný indexer všech produktů/akcí.

## Stránkování
- URL: `?page=N&count=24` (nebo `count=48`), první stránka bez `page=` nebo `page=1`.
- Celkový počet produktů najdeš v `nav.ddsweb-pagination__container` — text „Zobrazeno 1 až 24 z 346 produktů“.

## Stabilní selektory (fixture: `scraper/tests/fixtures/tesco/lihoviny_two_tiles.html`)
| Co | Selektor | Poznámka |
|---|---|---|
| **tile root** | `li[data-testid]` | `data-testid` = `store_sku` (např. `205119917`), stejné ID jako v URL `/products/205119917` |
| **raw_name** | `h2.online-components-product-tile-product-heading__heading > a` | obsahuje i objem, parsuje se v `matching/normalize.py` |
| **product URL** | stejný `<a>`, `href` | |
| **image_url** | `img.online-components-product-tile-product-image__image` | hotlink na `digitalcontent.api.tesco.com/...`, z URL vyhodit `?w=225` pro plnou velikost |
| **regular price** | `p.online-components-product-tile-price__text` | text `199,90 Kč` s `&nbsp;` |
| **unit price (regular)** | `p.online-components-product-tile-unit-price__subtext` | `399,80 Kč/l`, můžeme ignorovat (dopočítáme z `volume_ml`) |
| **Clubcard container** | `div.online-components-product-tile-clubcard-promotion__wrapper` | **optional**: existuje jen u produktů v akci |
| └ loyalty price | `p.ddsweb-value-bar__content-text` | text `149,90 Kč Ušetřete 25% s Clubcard` — cenu i % slevy vytáhnout regexem |
| └ promo_to | `p.ddsweb-value-bar__terms` | `Nabídka platí do 24. 11. 2026` → `promo_to` |
| **subcategory** | `a.online-components-product-tile-rest-of-shelf__rest-of-shelf`, `href` | třetí úroveň Tesco kategorie, mapuje se na naši `category` |

Mapování na `ScrapedItem`:
- 1 tile bez Clubcardu → **1 item**: `price_type='regular'`, `price_source='catalog'`.
- 1 tile s Clubcardem → **2 items** se stejným `store_sku`: `regular` + `loyalty` (ta s `promo_from=now`, `promo_to` z textu, `regular_czk` = běžná cena ze stejné karty).

## Anti-bot — pozor
- **`httpx` s našim UA dostane 403** (ověřeno 21. 11., `scratchpad/probe_tesco.py`). Tesco má anti-bot vrstvu (Akamai/DataDome, viditelný beacon na obfuskovaném endpointu `/gy2P5…`).
- Browser pane (Playwright-based) projde bez problémů z domácí IP.
- Spoofování prohlížečových hlaviček NEDĚLÁME (porušilo by [[../07 Provoz/Právní a etické zásady]] bod 4).

## Rozhodnutí po spike
- **Zařadit — P1, runner: PC, technika: Playwright Chromium** (`needs_browser = True` v `sources/tesco.py`).
- `uv run playwright install chromium` provést při implementaci M2 (~400 MB).
- Rate limit: 0,5 rps default + 1–2 s mezi stránkami. 15 stránek × ~2 s ≈ 30–45 s na jeden běh. OK.
- EAN/ABV nejsou v tile — přijdou z **detail page**. V MVP můžeme EAN vynechat (párovat jen přes značku + objem) a abv doplňovat z normalize/brands. Detail crawl přidáme, pokud bude parování slabé.

## Spike checklist
- [x] `robots.txt` + podmínky užití — katalog není v `Disallow`.
- [x] JSON endpoint — neexistuje, server-rendered HTML.
- [x] Funguje z `httpx`? → **ne, 403**.
- [x] Funguje z browser pane? → **ano**.
- [x] Clubcard cena + platnost? → ano, `ddsweb-value-bar__terms` má `Nabídka platí do DD. MM. RRRR`.
- [x] Cena před slevou? → běžná cena je na tile nad Clubcardem (`.online-components-product-tile-price__text`) → `regular_czk` pro akční řádek.
- [ ] Závisí cena na zvolené prodejně/PSČ? → neověřeno, spike proběhl bez výběru. (Pozn.: Tesco má nahoře „Vyberte si doručení“, ale ceny jsou vidět i bez toho — pravděpodobně jednotné.)
- [x] Odhad počtu položek v lihovinách — **346**.
- [x] Fixture — `scraper/tests/fixtures/tesco/lihoviny_two_tiles.html` (2 karty: s a bez Clubcardu).
