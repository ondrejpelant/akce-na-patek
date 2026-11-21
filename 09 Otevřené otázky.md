# Otevřené otázky

> Claude Code: nezodpovězené otázky neřeš odhadem — zeptej se Ondry. Po odpovědi přesuň do „Rozhodnuto“ s datem.

## K rozhodnutí během vývoje
7. Dárkové balení (lahev + 2 skleničky) = stejný produkt, nebo zvlášť?
8. Tuzemák: kategorie „Rum“, nebo „Pálenky“?
9. Albert: supermarket vs. hypermarket leták — které ceny? Kaufland: která prodejna (ceny podle prodejny)?
10. Název/doména na Vercelu (`akce-na-patek.vercel.app`?)

## Rozhodnuto
- 21. 11. 2026 — **Ceny:** každý obchod má u produktu výchozí běžnou cenu, po dobu akce ji přebije akční. U obchodů bez katalogu se běžná cena bere z „ceny před slevou“ v letáku, případně ruční zadání. → [[03 Data/Datový model]]
- 21. 11. 2026 — **Makro vyřazeno.**
- 21. 11. 2026 — **Aktualizace ručně na PC** jedním příkazem (`aktualizuj.bat`, `/aktualizuj`), žádný cron. → [[02 Architektura/ADR/ADR-005 Ruční aktualizace na PC]]
- 21. 11. 2026 — **Repo public** (původně soukromé, přepnuto 21. 11. odpoledne). V repu nejsou žádné secrets (`.env` v `.gitignore`, autor commitů používá GitHub noreply adresu).
- 21. 11. 2026 — **Věrnostní ceny** se počítají do nejnižší ceny, ale zobrazují se barevně odlišené s ikonou ⓘ a vysvětlivkou „platí jen s …“. → [[06 Frontend/UI specifikace]]
- 21. 11. 2026 — **Jen lihoviny.**
- 21. 11. 2026 — DB Neon ([[02 Architektura/ADR/ADR-001 Databáze]]), orchestrace GitHub Actions ([[02 Architektura/ADR/ADR-002 Orchestrace]], později nahrazeno ADR-005), Python scraper + Next.js web ([[02 Architektura/ADR/ADR-003 Jazyk scraperu]]), obrázky hotlinkem ([[02 Architektura/ADR/ADR-004 Obrázky produktů]]).
