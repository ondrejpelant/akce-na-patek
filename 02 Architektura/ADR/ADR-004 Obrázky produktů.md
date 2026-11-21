# ADR-004: Obrázky produktů — hotlink na CDN obchodů

- **Stav:** přijato (21. 11. 2026)

## Rozhodnutí
Neukládat obrázky. V `store_product.image_url` držet URL ze zdroje, `product.image_url` = nejlepší dostupná (priorita: katalogový zdroj Tesco/Billa > leták). Ve webu `<img loading="lazy">` s fallbackem na placeholder dle kategorie (SVG ikona lahve).

## Proč
- 1 GB storage free tierů by stačil, ale kopírování fotek je právně horší než odkaz a přidává práci.
- `next/image` optimalizace na Vercel Hobby má měsíční limit transformací → použít `unoptimized` nebo obyčejný `<img>`; povolené domény obrázků vyjmenovat v `next.config`.

## Implementace (21. 11. 2026)
- Tesco: URL z karty v katalogu (bez `?w=`); web si přes `sizedImage()` řekne o 300 px na kartu a 600 px na detail (Tesco media API bere `?w=`).
- Penny: výpis má jen lazy placeholder, fotka se bere z `og:image` stránky produktu (2–10 požadavků týdně, rate limit platí).
- `staging.sync_product_images` po každém párování: prázdný `product.image_url` doplní z libovolného obchodu, katalogový zdroj přepíše letákový a drží svou URL aktuální.
- `<img referrerPolicy="no-referrer">` — CDN obchodu nevidí, z jakého webu se obrázek načítá.

## Riziko
Obchod může hotlinking blokovat (Referer) nebo URL expirovat → fallback placeholder, scraper URL každý den obnoví.
