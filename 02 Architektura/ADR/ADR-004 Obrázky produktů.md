# ADR-004: Obrázky produktů — hotlink na CDN obchodů

- **Stav:** přijato (21. 11. 2026)

## Rozhodnutí
Neukládat obrázky. V `store_product.image_url` držet URL ze zdroje, `product.image_url` = nejlepší dostupná (priorita: katalogový zdroj Tesco/Billa > leták). Ve webu `<img loading="lazy">` s fallbackem na placeholder dle kategorie (SVG ikona lahve).

## Proč
- 1 GB storage free tierů by stačil, ale kopírování fotek je právně horší než odkaz a přidává práci.
- `next/image` optimalizace na Vercel Hobby má měsíční limit transformací → použít `unoptimized` nebo obyčejný `<img>`; povolené domény obrázků vyjmenovat v `next.config`.

## Riziko
Obchod může hotlinking blokovat (Referer) nebo URL expirovat → fallback placeholder, scraper URL každý den obnoví.
