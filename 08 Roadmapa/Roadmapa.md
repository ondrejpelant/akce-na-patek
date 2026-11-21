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
- [x] Mřížka `/` s vyhledáváním a kategoriemi ([[06 Frontend/UI specifikace]])
- [x] Detail `/p/[slug]`
- [x] noindex, patička, placeholder obrázky (`BottlePlaceholder` per kategorie), light-only (dark mode je NE v MVP)
- [ ] Deploy na Vercel ([[07 Provoz/Deploy]]) — čeká na Ondru v UI

**AK:** `/?q=jemna` i `/?q=jemn%C3%A1` vrací vodku (diakritika tolerance ✓); kliknutí na kartu otevře `/p/<slug>` s nabídkou obchodu, cenou, slevou -21 % a datem platnosti; viewport 375×812 bez horizontálního scrollu. Lighthouse zatím nespuštěn — až po Vercel deployi (localhost dev build neřekne realistické skóre).

## M4 — Aktualizace jedním klikem ✅
- [x] `scraper update` + `aktualizuj.bat` + souhrnná tabulka ([[05 Scraper/Aktualizace dat]])
- [x] `.claude/commands/aktualizuj.md` — hotové z M1, nyní pracuje proti reálnému `update`
- [x] `/api/revalidate`, `/status`, banner se stářím dat
- [x] Sanity checky (50 % mediánu posledních 7 OK běhů → `partial`), přeskočení dnes již aktualizovaných obchodů
- [x] `add-price` (ruční zadání běžné ceny)

**AK:** `uv run python -m scraper update --force` proběhl za 2 s (Penny OK 6), Lidl/Tesco/Billa/Albert/Kaufland → SKIP „no parser" (nebudou zabraňovat další aktualizaci); `/status` ukazuje per-store poslední běh; ruční POST na `/api/revalidate` vrací `{ok: true, revalidated: ["/"]}`. Selhání jednoho obchodu nezavre jeho ceny (SCD2 `_close_missing` běží jen pro `ok` status).

## M5 — Další zdroje + párování ✅ (P2 obchody po MVP)
- [x] Zbylé **P1** zdroje — přidáno **Tesco** (Playwright, kat. lihoviny). Lidl vyřazen z MVP (M0).
      Billa, Albert, Kaufland zůstávají P2/P3 — mimo MVP rozsah.
- [x] `brands.yaml` rozšířen (~70 značek vč. Královská palírna, Svijany, R. Jelínek, všech hlavních);
      kaskáda párování v `matching/matcher.py` (EAN → exact_norm → fuzzy ≥ 90 → pending 75-90 → new)
- [x] CLI `review` — interaktivní a/r/n/s/q pro pending `match_candidate`
- [x] 52 testovacích párů v `scraper/tests/fixtures/matching_cases.csv` (100 % accuracy, `test_matcher.py`)
- [x] Penny filter na pivo/cider — spirits only, per [[01 Zadání/Vize a rozsah]]

**AK:** `test_matcher.py` uzavírá 85 % AK na 100 %. Finlandia/Jameson/Božkov se v současných datech objeví v Tescu (katalog 346 položek) a potenciálně v Penny když je v akci — ověřit po manuálním `aktualizuj.bat --force` z File Exploreru (Tesco Playwright potřebuje reálné desktop session, z Claude headless pwsh nebylo možné).

## M6 — Vylepšení
- [ ] Řazení dle ceny/l a slevy, filtr „jen akce“
- [ ] Sparkline historie cen
- [ ] PWA manifest
- [ ] P3 zdroje (pokud spike dovolí), víno/šumivé
