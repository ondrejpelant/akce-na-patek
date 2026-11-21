# Roadmapa

Každý milník má akceptační kritéria (AK). Milník je hotový, až když platí všechna AK. Claude Code: pracuj vždy jen na prvním neuzavřeném milníku.

## M0 — Spike zdrojů (1–2 večery) ⏳
Cíl: vědět, co reálně stáhneme, než napíšeme řádek appky.
- [x] Spike Tesco ([[04 Zdroje/Tesco]]) — ✅ Playwright, selektory `online-components-product-tile-*`
- [x] Spike Lidl ([[04 Zdroje/Lidl]]) — ❌ leták jen jako bitmapa, vyřazeno z MVP
- [x] Spike Penny ([[04 Zdroje/Penny]]) — ✅ `httpx` + `selectolax`, kategorie `/category/alkohol-24`
- [ ] Spike Billa ([[04 Zdroje/Billa]]) — P2, po MVP
- [ ] Spike Albert ([[04 Zdroje/Albert]]) — P2, po MVP
- [ ] Spike Kaufland ([[04 Zdroje/Kaufland]]) — P3, po MVP
- [x] Všechny testy dělat z domácího PC (tam poběží i produkční aktualizace)
- [x] U letákových zdrojů ověřit, zda uvádějí „cenu před slevou“ (zdroj běžné ceny) — Penny ano (přeškrtnutá), Lidl ne (bitmap)
- [x] Aktualizovat [[04 Zdroje/Přehled zdrojů]] a zodpovědět otázky v [[09 Otevřené otázky]]

**AK pro MVP:** 2 P1 zdroje (Tesco katalog + Penny leták) mají „Rozhodnutí po spike“ a fixture → ✅ splněno. P2/P3 zdroje dořešíme v M5.

## M1 — Scaffold a DB
- [x] `git init`, `.gitignore` (GitHub soukromé repo zatím lokálně)
- [x] `scraper/` přes `uv init`, závislosti, ruff, pytest
- [x] `web/` přes `create-next-app` (TS, Tailwind, App Router, ESLint)
- [x] Neon projekt, role, migrace 001–003 ([[03 Data/Datový model]], [[03 Data/Kategorie]])
- [x] `ci.yml`

**AK:** `pytest` a `npm run build` prochází v CI; v Neonu existují tabulky + seed obchodů a kategorií.

## M2 — První zdroj end-to-end ✅
- [x] `http.py`, `models.py`, `sources/base.py`
- [x] Nejjednodušší P1 zdroj z M0 → **Penny** (`sources/penny.py` + 4 testy na fixture)
- [x] `load/staging.py`, `load/scd2.py` (`test_scd2.py` proběhne v M5, teď ověřeno manuálně proti Neonu)
- [x] `matching/normalize.py` + testy; 1 zdroj = každá položka nový produkt (auto-matcher ve `staging._automatch_unmatched`)
- [x] `publish.py` (refresh MV)

**AK:** `run --store penny` naplní DB (3 products, 6 prices); druhé spuštění téhož dne vložilo 0 nových řádků v `price`; `v_product_card` vrací 3 karty s nejnižší cenou. ✅

## M3 — Web MVP
- [ ] Mřížka `/` s vyhledáváním a kategoriemi ([[06 Frontend/UI specifikace]])
- [ ] Detail `/p/[slug]`
- [ ] noindex, patička, placeholder obrázky
- [ ] Deploy na Vercel ([[07 Provoz/Deploy]])

**AK:** na telefonu najdu produkt vyhledáním „finl“ i „koňak“/„konak“ a v detailu vidím ceny; Lighthouse mobile Performance ≥ 85.

## M4 — Aktualizace jedním klikem
- [ ] `scraper update` + `aktualizuj.bat` + souhrnná tabulka ([[05 Scraper/Aktualizace dat]])
- [ ] `.claude/commands/aktualizuj.md` otestovat
- [ ] `/api/revalidate`, `/status`, banner se stářím dat
- [ ] Sanity checky, `partial` logika, přeskočení dnes již aktualizovaných obchodů
- [ ] `add-price` (ruční zadání běžné ceny)

**AK:** dvojklik na `aktualizuj.bat` → do 10 min souhrn a čerstvá data na telefonu; selhání jednoho obchodu nezpůsobí zmizení jeho cen; po skončení akce se u produktu zobrazí běžná cena z letáku.

## M5 — Další zdroje + párování
- [ ] Zbylé P1 a P2 zdroje
- [ ] `brands.yaml` (~150 značek), kaskáda párování ([[03 Data/Párování produktů]])
- [ ] CLI `review`
- [ ] 50 testovacích párů v `matching_cases.csv`

**AK:** ≥ 85 % letákových položek se spáruje automaticky; detail populárního produktu (Finlandia, Jameson, Božkov) ukazuje ≥ 2 obchody.

## M6 — Vylepšení
- [ ] Řazení dle ceny/l a slevy, filtr „jen akce“
- [ ] Sparkline historie cen
- [ ] PWA manifest
- [ ] P3 zdroje (pokud spike dovolí), víno/šumivé
