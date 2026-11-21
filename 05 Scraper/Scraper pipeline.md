# Scraper pipeline

## Struktura `scraper/`
```
scraper/
├── pyproject.toml            # uv; deps: httpx, selectolax, playwright, pydantic, rapidfuzz, psycopg[binary], pyyaml, typer, rich, python-dotenv
├── scraper/
│   ├── __main__.py           # CLI (typer): update, run, match, publish, review, add-price, cleanup
│   ├── config.py             # env: DATABASE_URL, USER_AGENT, RATE_LIMIT_RPS
│   ├── http.py               # sdílený klient: rate limit, retry s backoffem, timeouty, UA
│   ├── models.py             # pydantic ScrapedItem
│   ├── sources/
│   │   ├── base.py           # abstraktní Source
│   │   ├── tesco.py
│   │   ├── lidl.py
│   │   └── penny.py ...
│   ├── matching/
│   │   ├── normalize.py      # objem, %, značka
│   │   ├── brands.yaml
│   │   ├── category_rules.yaml
│   │   └── matcher.py
│   └── load/
│       ├── staging.py        # zápis do stg_listing + scrape_run
│       ├── scd2.py           # SCD2 merge cen
│       └── publish.py        # refresh MV, cleanup staging
└── tests/
    ├── fixtures/<store>/*.json|html
    ├── test_parsers.py
    ├── test_normalize.py
    └── test_scd2.py          # proti lokálnímu Postgresu (docker) nebo Neon branch
```

## Kontrakt zdroje
```python
class ScrapedItem(BaseModel):
    store_code: str
    store_sku: str                 # stabilní ID ve zdroji; u letáku sha1(norm_name|volume)
    raw_name: str
    price_czk: Decimal             # kladné, max 2 des. místa
    price_type: Literal["regular", "promo", "loyalty"]
    regular_czk: Decimal | None = None
    promo_from: date | None = None
    promo_to: date | None = None
    volume_ml: int | None = None   # pokud zdroj dává strukturovaně, jinak doplní normalize
    abv: Decimal | None = None
    ean: str | None = None
    url: str | None = None
    image_url: str | None = None
    source_category: str | None = None
    source_kind: Literal["catalog", "leaflet"]
    raw: dict                      # původní záznam

class Source(ABC):
    code: str
    needs_browser: bool = False    # True → Playwright
    @abstractmethod
    def fetch(self) -> Iterator[ScrapedItem]: ...
```
Jeden zdroj může vracet více `price_type` pro stejnou položku (např. Tesco běžná + Clubcard) → více ScrapedItem se stejným `store_sku`.

## Kroky jedné aktualizace (`scraper update`, viz [[Aktualizace dat]])
| Krok | CLI | Co dělá | Při chybě |
|---|---|---|---|
| 1. Extract | `run --store X` | `scrape_run` (running) → stáhne → validuje → `stg_listing` | `failed`, ostatní zdroje běží dál |
| 2. Sanity check | (součást 1) | `items_found` < 50 % mediánu posledních 7 běhů → `partial` | partial = neuzavírat akce |
| 3. Upsert store_product | (součást 1) | podle `(store_id, store_sku)`, aktualizuje `last_seen_at` | — |
| 4. Match | `match` | normalizace + kaskáda párování nových/nespárovaných | log počtu pending |
| 5. Load SCD2 | `publish` | merge cen pro běhy `ok`/`partial` této aktualizace; z letákových položek s `regular_czk` vytvoří běžnou cenu (`leaflet_regular`) | rollback transakce |
| 6. Refresh | `publish` | `refresh materialized view concurrently ...` | vždy, i když 1–5 selhalo |
| 7. Cleanup | `cleanup` | smaže `stg_listing` starší 14 dní | — |

## Šetrnost a robustnost (`http.py`)
- Rate limit default **1 požadavek / 2 s** na doménu, konfigurovatelné per zdroj.
- User-Agent: `AkceNaPatek/0.1 (osobni nekomercni projekt; kontakt: <email>)`.
- Retry: 3× s exponenciálním backoffem jen na 5xx/timeout; **na 403/429 nezkoušet znovu** → zdroj `failed` s jasnou chybou („blokováno“).
- Timeout 20 s. Žádná paralelizace v rámci jednoho obchodu.
- `--dry-run`: nic nezapisuje, vypíše statistiku + prvních 10 položek.
- `--save-fixtures`: uloží surové odpovědi do `tests/fixtures/`.

## Testy
- Parser každého zdroje testovaný proti fixtures (žádná síť v testech).
- `test_normalize.py` — tabulka vstup → (značka, objem, %).
- Když zdroj změní strukturu: test spadne v CI na nových fixtures → opravit parser, aktualizovat note zdroje.
