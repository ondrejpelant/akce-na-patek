# 🍾 Akce na pátek — rozcestník

> Osobní srovnávač cen alkoholu v českých supermarketech. Zdarma, bez přihlašování, denně aktualizovaný.

## Zadání
- [[01 Zadání/Vize a rozsah]] — co appka dělá a co ne
- [[01 Zadání/Revize plánu]] — ověření reálnosti, rizika, co v plánu chybělo ⚠️ **číst jako první**

## Architektura
- [[02 Architektura/Architektura]] — celkový obrázek + diagram
- [[02 Architektura/Tech stack a limity free tierů]]
- ADR: [[02 Architektura/ADR/ADR-001 Databáze]] · [[02 Architektura/ADR/ADR-002 Orchestrace]] · [[02 Architektura/ADR/ADR-003 Jazyk scraperu]] · [[02 Architektura/ADR/ADR-004 Obrázky produktů]] · [[02 Architektura/ADR/ADR-005 Ruční aktualizace na PC]]

## Data
- [[03 Data/Datový model]] — DDL, SCD2 historie cen
- [[03 Data/Párování produktů]] — nejtěžší část projektu
- [[03 Data/Kategorie]]

## Zdroje dat
- [[04 Zdroje/Přehled zdrojů]] — matice dostupnosti
- [[04 Zdroje/Tesco]] · [[04 Zdroje/Billa]] · [[04 Zdroje/Albert]] · [[04 Zdroje/Lidl]] · [[04 Zdroje/Kaufland]] · [[04 Zdroje/Penny]] · [[04 Zdroje/Makro]] · [[04 Zdroje/Agregátory a jiné]]

## Scraper a orchestrace
- [[05 Scraper/Scraper pipeline]]
- [[05 Scraper/Aktualizace dat]] — jak spustit aktualizaci před nákupem

## Frontend
- [[06 Frontend/UI specifikace]]
- [[06 Frontend/Datové dotazy]]

## Provoz
- [[07 Provoz/Deploy]]
- [[07 Provoz/Monitoring]]
- [[07 Provoz/Právní a etické zásady]]

## Plán
- [[08 Roadmapa/Roadmapa]] — milníky s akceptačními kritérii
- [[08 Roadmapa/Backlog]]
- [[09 Otevřené otázky]]
- Deník vývoje: složka `10 Deník/`

Pro Claude Code: [[CLAUDE]]
