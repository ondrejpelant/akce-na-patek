# Lidl
- **Web:** https://www.lidl.cz (hlavně nepotravinový shop) · letáky online
- **Typ dat:** leták ve formě **obrázků stránek** (žádná strukturovaná data cen)
- **Priorita (po spike):** **❌ vyřazeno z MVP**, viz Rozhodnutí níže.

## Co víme (po spike 21. 11. 2026)
- `robots.txt` je mírný, povoluje katalogové stránky; disallow pro `search?q=*`, `*offset=*`, `*sort=*` a různé user-api.
- Potravinový online katalog **reálně neexistuje**: hub [vino-pivo-a-lihoviny/h10096268](https://www.lidl.cz/h/vino-pivo-a-lihoviny/h10096268) má přes JSON-LD `AggregateOffer.offerCount = 4` (čtyři položky v celé kategorii, nejlevnější 9,90 Kč → drobné artikly, ne lihoviny).
- **Leták API funguje z čistého `httpx`** (200, 95 KB JSON): `GET https://endpoints.leaflets.schwarz/v4/flyer?flyer_identifier=<slug>&region_id=0&region_code=0`
  - Příklad slug: `akcni-letaky-od-ctvrtka-19-11-22-11-2026`
  - Vrací: `startDate/endDate`, `offerStartDate/offerEndDate`, 46 stránek letáku jako PNG na `imgproxy.leaflets.schwarz`, `teasers` (náhledy), `keyWords` (OCR text per stránka — slepenec slov typu „999 Kč Kuřecí Prsa Svijany Svijanský Máz 05 … Lidl Plus -25%“), `altText` (AI popis stránky).
  - `pages[].links` je prázdné → žádné interaktivní produktové body. Žádné `products`, `offers`, `articles` objekty se strukturovanými cenami v odpovědi.
- Doména `endpoints.leaflets.schwarz` je Schwarz Group (matka Lidlu i Kauflandu) — stejný endpoint pravděpodobně slouží i Kauflandu (ověřit u Kauflandu).

## Fixture
- `scraper/tests/fixtures/lidl/flyer_od_ctvrtka_19_11_2026.json` — kompletní flyer response (95 KB).

## Proč nejde udělat scraper bez přídavné práce
- Ceny v letáku existují **jen jako pixely na obrázku stránky**. Vytěžit „Finlandia 0,7 l = 249,90 Kč“ by vyžadovalo OCR + CV (např. Tesseract + heuristiky na rozpoznání produktových karet v mřížce letáku). To:
  - není free (tesseract OK, ale přesnost na malých fonts bývá bídná, obvykle je potřeba cloudové OCR = platba);
  - je netriviální a mimo rozsah MVP;
  - poměr efort/výtěžek u ~tuctu alkoholů na leták je nízký.

## Alternativy, které jsem zvážil
1. **Lidl Plus app** — proprietární binary feed, nevyužíváme.
2. **OCR letákových obrázků** — mimo rozsah.
3. **Manuální `aktualizuj.bat add-price`** — postačí pro ty 2–3 položky, které si koupím pravidelně a chci mít v DB i bez Lidlu.

## Rozhodnutí po spike
- **Vyřadit z MVP.** Lidl se dostane do MVP, jen pokud se **objeví strukturovaný JSON** s cenami letáku (sledovat změny v endpoint `endpoints.leaflets.schwarz`), nebo pokud se rozhodneme pro OCR pipeline (až po M6).
- Upravit [[Přehled zdrojů]] a [[../08 Roadmapa/Roadmapa]] (Lidl mimo M5).
