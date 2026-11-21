# Monitoring

Minimální, zdarma:
1. **Souhrnná tabulka** na konci `aktualizuj.bat` + log v `scraper/logs/`.
2. **Tabulka `scrape_run`** + stránka `/status` ve webu.
3. **Sanity checky** v běhu (viz [[05 Scraper/Scraper pipeline]]): pokles počtu položek > 50 % → `partial`; nulový počet → `failed`.
4. **Čerstvost ve UI**: banner se stářím poslední aktualizace; akce jen v době platnosti; běžná cena > 60 dní → „může být neaktuální“.

## Typické poruchy a co dělat
| Symptom | Pravděpodobná příčina | Akce |
|---|---|---|
| `failed` 403/429 | blokace | počkat, nespouštět opakovaně; nic neobcházet; při trvalé blokaci zdroj vyřadit |
| `failed` parse error | zdroj změnil strukturu | stáhnout nové fixtures (`--save-fixtures`), opravit parser, aktualizovat note zdroje |
| `partial` | stránkování / timeout | zkontrolovat log, případně zvýšit timeout |
| hodně `pending` v matchingu | nové značky | doplnit `brands.yaml`, spustit `review` |
