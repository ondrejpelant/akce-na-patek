Spusť aktualizaci dat aplikace Akce na pátek.

1. Ve složce `scraper/` spusť `uv run python -m scraper update $ARGUMENTS`.
2. Ukaž mi souhrnnou tabulku z výstupu.
3. Pokud některý obchod skončil chybou:
   - 403/429 (blokace) → jen to oznam, nic neobcházej (viz `07 Provoz/Právní a etické zásady.md`).
   - chyba parsování → přečti poslední log v `scraper/logs/`, ulož nové fixtures (`run --store X --save-fixtures --dry-run`), navrhni opravu parseru a po mém souhlasu ji proveď včetně testů.
4. Pokud jsou nespárované položky, nabídni spuštění `uv run python -m scraper review`.
5. Zapiš krátký záznam do `10 Deník/` jen pokud se něco opravovalo.
