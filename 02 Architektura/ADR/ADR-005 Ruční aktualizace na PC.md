# ADR-005: Ruční aktualizace dat na mém PC

- **Stav:** přijato (21. 11. 2026), nahrazuje [[ADR-002 Orchestrace]]

## Kontext
Appku používám jen já a jen když jdu nakupovat. Denní automatické spouštění není potřeba. Z domácí (rezidenční) IP navíc projde víc zdrojů než z datacenter GitHubu (Tesco, Kaufland), aniž bychom cokoliv obcházeli.

## Rozhodnutí
- Aktualizaci spouštím **ručně na svém PC (Windows)** jedním příkazem před použitím appky: dvojklik na `aktualizuj.bat` v kořeni repa (nebo `/aktualizuj` v Claude Code).
- Skript spustí všechny zdroje postupně, pak párování, SCD2 load, refresh pohledů, revalidaci webu a vypíše souhrnnou tabulku.
- **Žádný cron.** GitHub Actions se používá jen pro CI (testy, build).
- Volitelně později: Plánovač úloh ve Windows (stejný `.bat`), pokud by mě ruční spouštění přestalo bavit.

## Důsledky
- Data mohou být staré několik dní → web musí **zřetelně ukazovat stáří dat** a nesmí produkty skrývat jen kvůli stáří (viz [[../../03 Data/Datový model]]).
- Connection string s právem zápisu je v lokálním `.env` (v .gitignore), ne v GitHub Secrets.
- Odpadá self-hosted runner, keepalive i limit minut. Repo může být libovolně soukromé.
- Potřebný software na PC: Python přes `uv`, Playwright Chromium (jen pro zdroje, které ho potřebují), Git.
