# Penny
- **Web:** https://www.penny.cz (SSR Nuxt/Vue3, žádný e-shop potravin — jen „nabídka týdne“ s akcemi)
- **Typ dat:** akční ceny týdenního letáku + **cena před slevou** (přeškrtnutá)
- **Priorita (po spike):** **✅ P1 — zařadit**, nejčistší zdroj ze všech P1 kandidátů

## Co víme (po spike 21. 11. 2026)
- `robots.txt` je minimalistický (jen odkaz na sitemapu), nic nezakazuje.
- Server-side rendered HTML (Nuxt 3), ceny jsou přímo v markupu. Žádné XHR pro produkty.
- **Funguje z čistého `httpx`** s našim UA: 200 OK, `content-type: text/html`, ověřeno v `scratchpad/probe_penny.py`.
- Katalogová kategorie přímo pro MVP: [/category/alkohol-24](https://www.penny.cz/category/alkohol-24)
- Počet položek: malý, Penny publikuje jen týdenní akce (18.-24. 11. 2026: 3 položky, z toho 2 lihoviny). Jiných týdnech typicky 5–15.
- Název kategorie 24 (= `alkohol`) stabilní — číslo za pomlčkou je kategorie ID.

## URL schéma
| Co | URL |
|---|---|
| hub všech kategorií | `/category` |
| jedna kategorie | `/category/<slug>-<id>` (`/category/alkohol-24`) |
| všechny akce v týdnu | `/category/vsechny-akce-99000000` |
| produktový detail | `/products/<slug>-<store_sku>` (`/products/vodka-jemna-375-kralovska-palirna-88442352`) |
| letákový tab | `/?tab=offers/lw-<week>-slug` (dynamický, raději ne) |

## Stabilní selektory (fixture: `scraper/tests/fixtures/penny/category_alkohol_week47.html`)
| Co | Selektor | Poznámka |
|---|---|---|
| **tile root** | `li.ws-product-tile[data-test="product-tile"]` | |
| **store_sku** | `[data-product-slug]` → poslední `\d+` za pomlčkou | např. `vodka-jemna-375-kralovska-palirna-88442352` → `88442352` |
| **raw_name** | atribut `data-teaser-name` (nebo `h3.ws-product-title` text) | |
| **product URL** | `a.ws-product-tile__link[href]` | relativní |
| **image_url** | `img.ws-product-image[src]` | pozor: v SSR to je base64 placeholder, reálný obrázek se dohraje přes `loading="lazy"` → můžeme si ho stáhnout na detailu, nebo spustit Playwright jen pro tuto stránku; pro MVP OK fallback na placeholder |
| **volume** | `.ws-product-information__piece-description li` | text `0,5 l` |
| **discount %** | `.ws-product-badge-discount__value` (text `-21`) | |
| **promo_from** | `.ws-product-price-validity > div:nth-child(1)` | text `od st 18.11.2026` |
| **promo_to** | `.ws-product-price-validity > div:nth-child(2)` | text `do út 24.11.2026` |
| **price_czk (promo)** | `.ws-product-price-value__main` | text `109,90 Kč` (NBSP) |
| **regular_czk (strikethrough)** | `.ws-product-price-strike s` nebo z atributu `title` | **cena před slevou** → `regular_czk`, podle [[../03 Data/Datový model]] sekce „Odkud se vezme běžná cena“ |
| **unit price** | `[data-test="product-price-type-label"]` | `1 l 219,80 Kč` (můžeme ignorovat, dopočítáme) |

Mapování na `ScrapedItem`:
- 1 tile → **2 items** se stejným `store_sku`:
  - `price_type='promo'`, `price_source='leaflet'`, `price_czk = 109,90`, `regular_czk = 139,90`, `promo_from=2026-11-18`, `promo_to=2026-11-24`
  - `price_type='regular'`, `price_source='leaflet_regular'`, `price_czk = 139,90` (odvozeno z přeškrtnuté)
- `source_kind = 'leaflet'`

## Spike checklist
- [x] `robots.txt` — neblokuje.
- [x] Funguje z `httpx`? → **ano, 200 OK, HTML ~500 KB**.
- [x] Cena před slevou? → ano (přeškrtnutá, hlavní zdroj `leaflet_regular` ceny).
- [x] Platnost akce? → ano, 2 data v DOM, formát `od <den> DD.MM.RRRR`.
- [x] Věrnostní cena? → Penny nemá věrnostní program, nic sem nepatří.
- [x] Odhad počtu položek v kategorii alkohol → 2–10 položek týdně (tento týden 3).
- [x] Fixture — `scraper/tests/fixtures/penny/category_alkohol_week47.html` (2 lihoviny z aktuálního týdne, pivo vynecháno kvůli MVP = jen lihoviny).

## Rozhodnutí po spike
- **Zařadit — P1, runner: PC, technika: `httpx` + `selectolax` nad HTML** (`needs_browser = False`).
- Rate limit: default 0,5 rps stačí.
- `source_kind = 'leaflet'`, 1 URL `category/alkohol-24` + případně `category/vsechny-akce-99000000` jako záchytná síť (prochází ale všechno, nejen alkohol — filtrovat kategorizací).
- Reálné obrázky: SSR placeholder → kdybychom chtěli hezké obrázky, buď (a) fetch detail produktu, nebo (b) Playwright. V MVP OK s fallback placeholderem per kategorie.
