# Kategorie

Seed data — `db/migrations/003_seed.sql`. Kategorie se přiřazuje z kategorie zdroje (Tesco/Billa mají strom kategorií) a u letáků klíčovými slovy (`category_rules.yaml`).

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
