# Párování produktů (entity resolution)

> Nejtěžší a nejvíc podceňovaná část. Bez dobrého párování nefunguje srovnání cen.

## Cíl
Každé `store_product` přiřadit ke kanonickému `product` (značka + název + objem), nebo založit nový produkt.

## Krok 1 — normalizace (Python, `scraper/matching/normalize.py`)
Z `raw_name` vytáhnout:
- **objem** regexem: `0,7 l`, `0.7L`, `700 ml`, `70cl`, `1l`, `3 x 0,5 l` (multipack → zatím vyřadit) → `volume_ml`
- **% alk.**: `40%`, `40 % obj.`, `37,5%` → `abv`
- **značku**: slovník známých značek (`brands.yaml`, ručně udržovaný, start ~150 značek: Finlandia, Absolut, Božkov, Tullamore D.E.W., Jameson, Jägermeister, Becherovka, Captain Morgan, Bacardi, Metaxa, Hennessy, Rémy Martin, Jelínek, Tatratea…) + aliasy (`tullamore dew` = `tullamore d.e.w.`).
- **zbytek názvu**: odstranit objem, %, slova jako „lahev“, „dárkové balení“, „+ 2 skleničky“ (dárkové balení = **příznak**, ne jiný produkt? → [[09 Otevřené otázky]]).
- vše `lower` + bez diakritiky + jednotné mezery.

## Krok 2 — kaskáda párování
| # | Metoda | Podmínka | Akce |
|---|---|---|---|
| 1 | `ean` | shodný EAN | auto-accept |
| 2 | `exact_norm` | shodná značka + normalizovaný název + objem | auto-accept |
| 3 | `fuzzy` | shodná značka + objem, `token_set_ratio(name) ≥ 90` | auto-accept |
| 4 | `fuzzy` | shodný objem, skóre 75–90 | `match_candidate` pending → ruční review |
| 5 | žádný | — | nový `product` (jen ze zdroje `catalog`; letáková položka bez páru čeká na review) |

**Objem musí sedět vždy** (tolerance ±0: 0,7 l ≠ 0,75 l). Bez objemu nepárovat automaticky.

## Krok 3 — ruční review (bez přihlašování!)
Protože appka nemá login, review neprobíhá ve webu. Možnosti (od nejjednoduššího):
1. **CLI:** `uv run python -m scraper review` — interaktivně v terminálu ukáže pending kandidáty, `a/r/n/s` (accept/reject/new/skip).
2. Volitelně později: chráněná stránka `/admin/review` za tajným tokenem v URL (env proměnná) — jen pokud CLI nebude stačit.

## Kvalita
- Test sada `scraper/tests/fixtures/matching_cases.csv` (raw_name A, raw_name B, má_se_spárovat) — začít s ~50 ručně vybranými páry, rozšiřovat při každé chybě.
- Metriky po běhu do logu: % spárovaných položek per obchod, počet pending.
