# Kategorie

Seed data — `db/migrations/003_seed.sql`.

## Jak se kategorie přiřazuje (od 21. 11. 2026)
Pořadí (`matcher.resolve_category`):
1. **Klíčové slovo v názvu** — `scraper/scraper/matching/category_rules.yaml`. Slovo musí začínat slovo (prefix): `tuzem` chytí tuzemák i tuzemský, `gin` nechytí „originál".
2. **Kategorie obchodu** — `scraper/scraper/matching/source_categories.yaml` (zatím Tesco: cesta z odkazu „Více z kategorie" na kartě, např. `whisky-bourbon-a-jine-destilaty/skotska-whisky` → `whisky`). Vyhrává nejdelší shoda po segmentech.
3. Jinak `ostatni`.

Kategorie obchodu se nečte z DB kolonky, ale z posledního záznamu položky ve `stg_listing` (retence 14 dní). Při `rematch` starších položek se tedy použijí jen klíčová slova. Po zavedení: v „Ostatní" zůstaly 2 karty ze 42 (dřív 13).

| sort | slug | Název | Klíčová slova (příklady) |
|---|---|---|---|
| 10 | rum | Rum | rum, ron, spiced |
| 20 | vodka | Vodka | vodka, wodka |
| 30 | gin | Gin | gin |
| 40 | whisky | Whisky | whisky, whiskey, bourbon, scotch |
| 50 | brandy | Koňak a brandy | cognac, koňak, brandy, metaxa, armagnac |
| 60 | likery | Likéry | likér, liqueur, cream, amaretto |
| 70 | bylinne | Bylinné | becherovka, jägermeister, fernet, bylinný |
| 80 | palenky | Pálenky | slivovice, hruškovice, meruňkovice, borovička, tuzemák |
| 90 | tequila | Tequila a mezcal | tequila, mezcal |
| 100 | ostatni | Ostatní lihoviny | absinth, ouzo, pisco … |
| 200 | vino | Víno | (fáze 2) |
| 210 | sumive | Šumivá vína | prosecco, sekt, cava, šampaňské (fáze 2) |
| 220 | pivo | Pivo | (fáze 2 — hodně položek, multipacky) |

MVP = jen lihoviny (řádky 10–100). Víno a pivo přidají tisíce položek a komplikace s multipacky → po MVP, viz [[09 Otevřené otázky]].
Pozor na kolize: „Tuzemák“ ≠ rum (legálně), patří do `palenky` nebo `rum`? → rozhodnutí v otázkách.
